"""Tests for the bridge. Run with `pants test pesacheck_meedan_bridge/py::`.

Nothing here touches the network or a real database: Ghost and Check are
mocked, and every test gets its own SQLite file.
"""

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from unittest import mock

import requests

TMP = tempfile.mkdtemp()
# Set before settings is imported. environs does not override what's already
# in the environment, so a developer's .env can't change these.
os.environ.update(
    {
        "PESACHECK_SENTRY_DSN": "",
        "PESACHECK_URL": "https://pesacheck.org",
        "PESACHECK_GHOST_CONTENT_API_KEY": "key",
        "PESACHECK_GHOST_POSTS_LIMIT": "2",
        "PESACHECK_CHECK_URL": "https://check.invalid/graphql",
        "PESACHECK_CHECK_TOKEN": "t",  # nosec B105 - placeholder, nothing is called
        "PESACHECK_CHECK_WORKSPACE_SLUG": "ws",
        "PESACHECK_DATABASE_NAME": os.path.join(TMP, "unused.db"),
    }
)

import check_api  # noqa: E402
import database  # noqa: E402
import main  # noqa: E402
import settings  # noqa: E402


def ghost_post(i, day=1, **extra):
    post = {
        "id": f"{i:024x}",
        "title": f"Post {i}",
        "url": f"https://pesacheck.org/post-{i}/",
        "published_at": f"2026-09-{day:02d}T10:00:00.000+00:00",
        "custom_excerpt": f"Summary {i}",
        "tags": [
            {"name": "Somali", "visibility": "public"},
            {"name": "#internal", "visibility": "internal"},
        ],
        "authors": [{"name": "A"}],
    }
    post.update(extra)
    return post


def ghost_response(posts, next_page=None):
    resp = mock.Mock(status_code=200)
    resp.json.return_value = {
        "posts": posts,
        "meta": {"pagination": {"next": next_page}},
    }
    return resp


def check_response(i):
    return {
        "data": {
            "createProjectMedia": {
                "project_media": {
                    "id": f"pm{i}",
                    "full_url": f"https://check/{i}",
                    "claim_description": {"fact_check": {"id": f"fc{i}"}},
                }
            }
        }
    }


class Base(unittest.TestCase):
    def setUp(self):
        fd, self.db_file = tempfile.mkstemp(suffix=".db", dir=TMP)
        os.close(fd)
        settings.PESACHECK_DATABASE_NAME = self.db_file
        self.db = database.PesacheckDatabase()
        self.posted = []

        def fake_post(data):
            self.posted.append(data)
            return check_response(len(self.posted))

        p = mock.patch.object(main, "post_to_check", side_effect=fake_post)
        self.post_mock = p.start()
        self.addCleanup(p.stop)
        self.sentry_exc = mock.patch.object(
            main.sentry_sdk, "capture_exception"
        ).start()
        self.sentry_msg = mock.patch.object(main.sentry_sdk, "capture_message").start()
        self.addCleanup(mock.patch.stopall)

    def run_with(self, posts):
        with mock.patch.object(
            main.requests, "get", return_value=ghost_response(posts)
        ):
            main.main(self.db)

    def rows(self):
        conn = sqlite3.connect(self.db_file)
        rows = conn.execute("SELECT guid, status FROM pesacheck_feeds").fetchall()
        conn.close()
        return dict(rows)

    def add_row(self, guid, pub_date, status="Completed", description="x"):
        self.db.insert_pesacheck_feed(
            database.PesacheckFeed(
                title="t",
                pubDate=pub_date,
                author="a",
                guid=guid,
                link="l",
                thumbnail="",
                description=description,
                status=status,
                categories="[]",
            )
        )


class TestPagination(Base):
    def test_first_run_fetches_single_page_without_filter(self):
        with mock.patch.object(
            main.requests,
            "get",
            return_value=ghost_response([ghost_post(2), ghost_post(1)], next_page=2),
        ) as get:
            posts = main.fetch_from_pesacheck(since=None)
        self.assertEqual(len(posts), 2)
        self.assertEqual(get.call_count, 1)
        self.assertNotIn("filter", get.call_args.kwargs["params"])
        self.assertEqual(
            get.call_args.args[0], "https://pesacheck.org/ghost/api/content/posts/"
        )

    def test_sends_identifying_user_agent(self):
        with mock.patch.object(
            main.requests, "get", return_value=ghost_response([])
        ) as get:
            main.fetch_from_pesacheck()
        headers = get.call_args.kwargs["headers"]
        self.assertEqual(headers["User-Agent"], main.USER_AGENT)
        self.assertNotIn("python-requests", headers["User-Agent"])

    def test_checkpoint_follows_next_until_exhausted(self):
        pages = [
            ghost_response([ghost_post(5), ghost_post(4)], next_page=2),
            ghost_response([ghost_post(3), ghost_post(2)], next_page=3),
            ghost_response([ghost_post(1)], next_page=None),
        ]
        seen_pages = []

        def fake_get(url, params, headers, timeout):
            seen_pages.append((params["page"], params["filter"]))
            return pages[params["page"] - 1]

        since = datetime(
            2026,
            9,
            1,
            13,
            0,
            tzinfo=datetime.fromisoformat("2026-01-01T00:00+03:00").tzinfo,
        )
        with mock.patch.object(main.requests, "get", side_effect=fake_get):
            posts = main.fetch_from_pesacheck(since=since)
        self.assertEqual(
            [p["title"] for p in posts], [f"Post {i}" for i in (5, 4, 3, 2, 1)]
        )
        # Converted to UTC.
        self.assertEqual(seen_pages[0], (1, "published_at:>='2026-09-01 10:00:00'"))
        self.assertEqual([p for p, _ in seen_pages], [1, 2, 3])

    def test_checkpoint_ignores_legacy_rows(self):
        self.add_row("https://medium.com/p/abc", "2030-01-01 00:00:00")
        self.assertIsNone(main.get_checkpoint(self.db))
        self.add_row("a" * 24, "2026-09-01T10:00:00.000+00:00")
        self.add_row("b" * 24, "2026-09-03T10:00:00.000+00:00")
        self.assertEqual(
            main.get_checkpoint(self.db), datetime(2026, 9, 3, 10, tzinfo=UTC)
        )

    def test_burst_larger_than_limit_is_fully_imported_oldest_first(self):
        self.add_row("0" * 24, "2026-09-01T10:00:00.000+00:00")
        pages = [
            ghost_response([ghost_post(5, 5), ghost_post(4, 4)], next_page=2),
            ghost_response([ghost_post(3, 3), ghost_post(2, 2)], next_page=None),
        ]
        with mock.patch.object(
            main.requests,
            "get",
            side_effect=lambda url, params, **kw: pages[params["page"] - 1],
        ):
            main.main(self.db)
        self.assertEqual(
            [d["title"] for d in self.posted], ["Post 2", "Post 3", "Post 4", "Post 5"]
        )
        self.assertTrue(all(v == "Completed" for v in self.rows().values()))
        self.assertEqual(self.posted[0]["language"], "so")
        self.assertEqual(self.posted[0]["set_tags"], ["Somali"])

    def test_fetch_error_on_later_page_stores_nothing(self):
        self.add_row("0" * 24, "2026-09-01T10:00:00.000+00:00")
        err = mock.Mock(status_code=500, text="boom")
        pages = [ghost_response([ghost_post(5, 5)], next_page=2), err]
        with mock.patch.object(
            main.requests,
            "get",
            side_effect=lambda url, params, **kw: pages[params["page"] - 1],
        ):
            with self.assertRaises(Exception):
                main.main(self.db)
        self.assertEqual(self.posted, [])
        self.assertEqual(len(self.rows()), 1)
        self.sentry_exc.assert_called_once()


class TestDatabaseWrites(Base):
    def test_failed_insert_does_not_post(self):
        with mock.patch.object(
            self.db,
            "insert_pesacheck_feed",
            side_effect=sqlite3.OperationalError("database is locked"),
        ):
            self.run_with([ghost_post(1)])
        self.assertEqual(self.posted, [])
        self.sentry_exc.assert_called_once()

    def test_failed_claim_does_not_post(self):
        with mock.patch.object(
            self.db,
            "claim_pending_feed",
            side_effect=sqlite3.OperationalError("locked"),
        ):
            self.run_with([ghost_post(1)])
        self.assertEqual(self.posted, [])
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Pending"})
        self.sentry_exc.assert_called_once()

    def test_failed_update_after_post_is_not_reposted(self):
        with mock.patch.object(
            self.db,
            "update_pesacheck_feed",
            side_effect=sqlite3.OperationalError("disk full"),
        ):
            self.run_with([ghost_post(1)])
        self.assertEqual(len(self.posted), 1)
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Posting"})
        # Next run: not re-posted, and a warning is raised for reconciliation.
        self.sentry_msg.reset_mock()
        self.run_with([ghost_post(1)])
        self.assertEqual(len(self.posted), 1)
        levels = [c.kwargs.get("level") for c in self.sentry_msg.call_args_list]
        self.assertIn("warning", levels)

    def test_check_error_reverts_to_pending_and_retries(self):
        self.post_mock.side_effect = Exception('{"errors": ["bad"]}')
        self.run_with([ghost_post(1)])
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Pending"})
        self.post_mock.side_effect = lambda data: (
            self.posted.append(data),
            check_response(1),
        )[1]
        self.run_with([])
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Completed"})
        self.assertEqual(len(self.posted), 1)

    def test_check_timeout_leaves_posting(self):
        self.post_mock.side_effect = requests.Timeout("timed out")
        self.run_with([ghost_post(1)])
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Posting"})

    def test_update_of_missing_row_raises(self):
        feed = database.PesacheckFeed(
            title="t",
            pubDate="",
            author="",
            guid="missing",
            link="",
            thumbnail="",
            description="",
            status="Completed",
            categories="[]",
        )
        with self.assertRaises(sqlite3.Error):
            self.db.update_pesacheck_feed("missing", feed)
        with self.assertRaises(sqlite3.Error):
            self.db.update_pesacheck_feed_status("missing", "Posting")

    def test_duplicate_insert_raises(self):
        self.add_row("a" * 24, "")
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_row("a" * 24, "")

    def test_connection_failure_raises_original_error(self):
        settings.PESACHECK_DATABASE_NAME = "/nonexistent-dir/x.db"
        with self.assertRaises(sqlite3.OperationalError):
            database.PesacheckDatabase()


class TestMalformedPosts(Base):
    def test_malformed_post_skipped_others_processed(self):
        bad = ghost_post(2)
        del bad["title"]
        with mock.patch.object(
            main.requests,
            "get",
            return_value=ghost_response([ghost_post(3), bad, ghost_post(1)]),
        ):
            main.main(self.db)
        self.assertEqual([d["title"] for d in self.posted], ["Post 1", "Post 3"])
        self.assertEqual(self.sentry_exc.call_count, 1)
        self.assertIsInstance(self.sentry_exc.call_args.args[0], KeyError)


class TestSummary(Base):
    def feed(self, guid, description):
        return database.PesacheckFeed(
            title="t",
            pubDate="",
            author="",
            guid=guid,
            link="",
            thumbnail="",
            description=description,
            status="Pending",
            categories="[]",
        )

    def test_ghost_excerpt_is_plain_text(self):
        self.assertEqual(
            main.extract_summary(self.feed("a" * 24, "  A <b>claim</b> & more ")),
            "A <b>claim</b> & more",
        )
        self.assertIsNone(main.extract_summary(self.feed("a" * 24, "  ")))

    def test_legacy_with_figure(self):
        html = "<p>The summary.</p><figure><img src=x></figure><p>Body</p>"
        self.assertEqual(
            main.extract_summary(self.feed("https://medium.com/p/1", html)),
            "The summary.",
        )

    def test_legacy_without_figure_returns_none(self):
        html = "<p>Whole long article body</p><p>More body</p>"
        self.assertIsNone(
            main.extract_summary(self.feed("https://medium.com/p/1", html))
        )

    def test_legacy_figure_first_returns_none(self):
        html = "<div><figure><img src=x></figure><p>Body</p></div>"
        self.assertIsNone(
            main.extract_summary(self.feed("https://medium.com/p/1", html))
        )

    def test_legacy_without_figure_posts_not_found(self):
        self.add_row(
            "https://medium.com/p/1", "", status="Pending", description="<p>Body</p>"
        )
        with mock.patch.object(main.requests, "get", return_value=ghost_response([])):
            main.main(self.db)
        self.assertEqual(self.posted[0]["summary"], "Not Found")


class TestReviewRound2(Base):
    def test_failed_insert_aborts_batch_and_holds_checkpoint(self):
        self.add_row("0" * 24, "2026-09-01T10:00:00.000+00:00")
        before = main.get_checkpoint(self.db)
        older, newer = ghost_post(1, day=2), ghost_post(2, day=3)
        real_insert = self.db.insert_pesacheck_feed

        def flaky(feed):
            if feed.guid == older["id"]:
                raise sqlite3.OperationalError("database is locked")
            return real_insert(feed)

        with mock.patch.object(self.db, "insert_pesacheck_feed", side_effect=flaky):
            with mock.patch.object(
                main.requests, "get", return_value=ghost_response([newer, older])
            ):
                main.main(self.db)
        # Neither article was stored, so the checkpoint still covers both.
        self.assertNotIn(older["id"], self.rows())
        self.assertNotIn(newer["id"], self.rows())
        self.assertEqual(main.get_checkpoint(self.db), before)
        self.assertEqual(self.posted, [])
        # Next run (database healthy) imports both, oldest first.
        with mock.patch.object(
            main.requests, "get", return_value=ghost_response([newer, older])
        ):
            main.main(self.db)
        self.assertEqual([d["title"] for d in self.posted], ["Post 1", "Post 2"])

    def test_duplicate_post_across_pages_is_handled_once(self):
        # A post published mid-pagination can be returned on two pages; the
        # feed_exists() check already covers that, since each article is stored
        # before the next is looked at.
        dup = ghost_post(1, day=2)
        pages = [
            ghost_response([ghost_post(2, day=3), dup], next_page=2),
            ghost_response([dup, ghost_post(3, day=1)], next_page=None),
        ]
        self.add_row("0" * 24, "2026-09-01T10:00:00.000+00:00")
        with mock.patch.object(
            main.requests,
            "get",
            side_effect=lambda url, params, **kw: pages[params["page"] - 1],
        ):
            main.main(self.db)
        self.assertEqual(
            [d["title"] for d in self.posted], ["Post 3", "Post 1", "Post 2"]
        )
        self.sentry_exc.assert_not_called()

    def test_malformed_post_does_not_block_later_articles(self):
        bad = ghost_post(1, day=2)
        del bad["title"]
        good = ghost_post(2, day=3)
        with mock.patch.object(
            main.requests, "get", return_value=ghost_response([good, bad])
        ):
            main.main(self.db)
        self.assertEqual([d["title"] for d in self.posted], ["Post 2"])
        self.assertIsInstance(self.sentry_exc.call_args.args[0], KeyError)

    def test_bad_categories_leave_row_pending_without_posting(self):
        self.add_row("a" * 24, "", status="Pending")
        conn = sqlite3.connect(self.db_file)
        conn.execute("UPDATE pesacheck_feeds SET categories = 'not-json'")
        conn.commit()
        conn.close()
        with mock.patch.object(main.requests, "get", return_value=ghost_response([])):
            main.main(self.db)
        self.assertEqual(self.posted, [])
        self.assertEqual(self.rows(), {"a" * 24: "Pending"})

    def test_check_rejection_reverts_to_pending(self):
        self.post_mock.side_effect = Exception("Mutation rejected")
        with mock.patch.object(
            main.requests, "get", return_value=ghost_response([ghost_post(1)])
        ):
            main.main(self.db)
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Pending"})

    def test_whole_run_failure_raises(self):
        with mock.patch.object(
            main.requests, "get", side_effect=requests.ConnectionError("down")
        ):
            with self.assertRaises(requests.ConnectionError):
                main.main(self.db)
        # The end-of-run message is still sent.
        self.assertTrue(self.sentry_msg.called)


class TestDuplicates(Base):
    duplicate_payload = {
        "errors": [
            {
                "message": (
                    "PG::UniqueViolation: ERROR:  duplicate key value violates "
                    'unique constraint "index_fact_checks_on_signature"'
                )
            }
        ]
    }

    def test_duplicate_is_marked_terminally_and_not_retried(self):
        self.post_mock.side_effect = check_api.DuplicateFactCheckError("dup")
        with mock.patch.object(
            main.requests, "get", return_value=ghost_response([ghost_post(1)])
        ):
            main.main(self.db)
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Duplicate"})
        # The in-memory feed agrees with the row, so later reads can't drift.
        self.assertEqual(
            self.db.get_pesacheck_feeds_by_status("Duplicate")[0].status, "Duplicate"
        )
        # Next run: not retried, and no exception reported for it.
        self.sentry_exc.reset_mock()
        self.post_mock.reset_mock()
        with mock.patch.object(main.requests, "get", return_value=ghost_response([])):
            main.main(self.db)
        self.post_mock.assert_not_called()
        self.sentry_exc.assert_not_called()

    def test_duplicates_are_summarised_once_not_reported_as_errors(self):
        self.post_mock.side_effect = check_api.DuplicateFactCheckError("dup")
        with mock.patch.object(
            main.requests,
            "get",
            return_value=ghost_response([ghost_post(2, day=3), ghost_post(1, day=2)]),
        ):
            main.main(self.db)
        self.sentry_exc.assert_not_called()
        message = self.sentry_msg.call_args.args[0]
        self.assertIn("Posted 0 PesaCheck article(s)", message)
        self.assertIn("Skipped 2 PesaCheck article(s) Check already has", message)

    def test_pending_duplicate_from_an_earlier_run_is_resolved(self):
        self.add_row("a" * 24, "", status="Pending")
        self.post_mock.side_effect = check_api.DuplicateFactCheckError("dup")
        with mock.patch.object(main.requests, "get", return_value=ghost_response([])):
            main.main(self.db)
        self.assertEqual(self.rows(), {"a" * 24: "Duplicate"})


class TestConcurrentRuns(Base):
    """Two runs overlapping on the same row (cron firing while one is late)."""

    def test_only_one_run_claims_a_pending_row(self):
        self.add_row("a" * 24, "", status="Pending")
        self.assertTrue(self.db.claim_pending_feed("a" * 24))
        self.assertFalse(self.db.claim_pending_feed("a" * 24))
        self.assertEqual(self.rows(), {"a" * 24: "Posting"})

    def test_loser_of_the_race_does_not_post(self):
        self.add_row("a" * 24, "", status="Pending")
        feed = self.db.get_pesacheck_feeds_by_status("Pending")[0]
        # Another run claimed it between our read and our post.
        self.db.claim_pending_feed("a" * 24)
        self.assertIsNone(main.post_to_check_and_update(feed, db=self.db))
        self.assertEqual(self.posted, [])

    def test_completed_row_is_never_downgraded_to_duplicate(self):
        self.add_row("a" * 24, "", status="Completed")
        feed = database.PesacheckFeed(
            title="t",
            pubDate="",
            author="",
            guid="a" * 24,
            link="l",
            thumbnail="",
            description="d",
            status="Completed",
            categories="[]",
        )
        main.mark_terminal(feed, self.db, "Duplicate")
        self.assertEqual(self.rows(), {"a" * 24: "Completed"})
        self.sentry_exc.assert_called_once()

    def test_a_failure_while_marking_duplicate_keeps_the_duplicate_error(self):
        self.post_mock.side_effect = check_api.DuplicateFactCheckError("dup")
        with mock.patch.object(
            self.db,
            "update_pesacheck_feed_status",
            side_effect=sqlite3.OperationalError("locked"),
        ):
            self.run_with([ghost_post(1)])
        # The run still knows it was a duplicate, and says so once.
        message = self.sentry_msg.call_args.args[0]
        self.assertIn("Skipped 1 PesaCheck article(s)", message)
        # The write failure itself is reported rather than swallowed.
        self.assertEqual(self.sentry_exc.call_count, 1)


class TestDuplicateDetection(unittest.TestCase):
    DUPLICATE = (
        "PG::UniqueViolation: ERROR:  duplicate key value violates "
        'unique constraint "index_fact_checks_on_signature"'
    )

    def test_only_when_every_error_is_the_duplicate(self):
        self.assertTrue(check_api.is_duplicate([{"message": self.DUPLICATE}]))
        self.assertTrue(
            check_api.is_duplicate(
                [{"message": self.DUPLICATE}, {"message": self.DUPLICATE}]
            )
        )

    def test_a_second_unrelated_error_is_not_a_duplicate(self):
        # Otherwise the row is marked terminally and the real problem is lost.
        self.assertFalse(
            check_api.is_duplicate(
                [
                    {"message": self.DUPLICATE},
                    {"message": "permission denied for field set_status"},
                ]
            )
        )

    def test_odd_error_shapes_do_not_crash(self):
        self.assertFalse(check_api.is_duplicate([]))
        self.assertFalse(check_api.is_duplicate([{"message": None}]))
        self.assertFalse(check_api.is_duplicate(["a plain string"]))
        self.assertFalse(check_api.is_duplicate([{}]))
        # A duplicate reported as a bare string still counts.
        self.assertTrue(check_api.is_duplicate([self.DUPLICATE]))


class TestCheckApiValidation(unittest.TestCase):
    def call_with(self, payload, status=200):
        resp = mock.Mock(status_code=status, text=json.dumps(payload))
        resp.json.return_value = payload
        with mock.patch.object(check_api.requests, "post", return_value=resp):
            return check_api.post_to_check(
                {"media_type": "Blank", "channel": 1, "set_tags": [], "title": "t"}
            )

    def test_accepts_valid_response(self):
        self.assertEqual(self.call_with(check_response(1)), check_response(1))

    def test_rejects_graphql_errors_with_http_200(self):
        with self.assertRaises(Exception):
            self.call_with(
                {
                    "data": {"createProjectMedia": None},
                    "errors": [{"message": "Mutation rejected"}],
                }
            )

    def test_rejects_null_project_media(self):
        with self.assertRaises(Exception):
            self.call_with({"data": {"createProjectMedia": {"project_media": None}}})

    def test_raises_duplicate_error_for_signature_violation(self):
        with self.assertRaises(check_api.DuplicateFactCheckError):
            self.call_with(TestDuplicates.duplicate_payload)

    def test_other_graphql_errors_are_not_duplicates(self):
        with self.assertRaises(Exception) as ctx:
            self.call_with({"errors": [{"message": "Mutation rejected"}]})
        self.assertNotIsInstance(ctx.exception, check_api.DuplicateFactCheckError)

    def test_rejects_non_200(self):
        with self.assertRaises(Exception):
            self.call_with(check_response(1), status=500)


if __name__ == "__main__":
    unittest.main(verbosity=2)
