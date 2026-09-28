"""Tests for the bridge. Run with `pants test pesacheck_meedan_bridge/py::`.

Nothing here touches the network or a real database: the CMS APIs and Check
are mocked, and every test gets its own SQLite file.
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
        "PESACHECK_PROVIDER": "ghost",
        "PESACHECK_URL": "https://pesacheck.org",
        "PESACHECK_SITE_URL": "https://pesacheck.org",
        "PESACHECK_GHOST_CONTENT_API_KEY": "key",
        "PESACHECK_POSTS_LIMIT": "2",
        "PESACHECK_SUPERDESK_GRAPHQL_URL": "https://graphql.invalid/v1/graphql",
        "PESACHECK_SUPERDESK_TENANT_CODE": "123abc",
        "PESACHECK_CHECK_URL": "https://check.invalid/graphql",
        "PESACHECK_CHECK_TOKEN": "t",  # nosec B105 - placeholder, nothing is called
        "PESACHECK_CHECK_WORKSPACE_SLUG": "ws",
        "PESACHECK_DATABASE_NAME": os.path.join(TMP, "unused.db"),
    }
)

import check_api  # noqa: E402
import database  # noqa: E402
import main  # noqa: E402
import provider_base  # noqa: E402
import provider_ghost  # noqa: E402
import provider_superdesk  # noqa: E402
import providers  # noqa: E402
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


def superdesk_article(i, day=1, **extra):
    metadata = {
        "guid": f"uuid-{i}",
        "language": "so",
        "byline": "A",
        "subject": [
            {"code": "false", "name": "False", "scheme": "Debunk"},
            {"code": "KEN", "name": "Kenya", "scheme": "countrymention1"},
            {"code": "KEN", "name": "Kenya", "scheme": "countries"},
            {"code": "quickread", "name": "Quick Read", "scheme": "content_type"},
            {"code": "debunkso", "name": "Somali", "scheme": "Debunklang"},
            {"code": "sports", "name": "Sports", "scheme": "Harm_type"},
        ],
    }
    metadata.update(extra.pop("metadata", None) or {})
    article = {
        "id": 6000 + i,
        "title": f"Post {i}",
        "slug": f"post-{i}",
        "lead": f"<p>Summary {i}</p>",
        "published_at": f"2026-09-{day:02d}T10:00:00",
        "metadata": json.dumps(metadata),
        "swp_route": {"slug": "somali"},
    }
    article.update(extra)
    return article


def superdesk_response(articles):
    resp = mock.Mock(status_code=200)
    resp.json.return_value = {"data": {"items": articles}}
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
    provider = "ghost"

    def setUp(self):
        fd, self.db_file = tempfile.mkstemp(suffix=".db", dir=TMP)
        os.close(fd)
        settings.PESACHECK_DATABASE_NAME = self.db_file
        settings.PESACHECK_PROVIDER = self.provider
        self.addCleanup(setattr, settings, "PESACHECK_PROVIDER", "ghost")
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

    def rows(self):
        conn = sqlite3.connect(self.db_file)
        rows = conn.execute("SELECT guid, status FROM pesacheck_feeds").fetchall()
        conn.close()
        return dict(rows)

    def sources(self):
        conn = sqlite3.connect(self.db_file)
        rows = conn.execute("SELECT guid, source FROM pesacheck_feeds").fetchall()
        conn.close()
        return dict(rows)

    def add_row(
        self, guid, pub_date, status="Completed", description="x", source="ghost"
    ):
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
                source=source,
            )
        )

    def run_ghost(self, posts, next_page=None):
        with mock.patch.object(
            provider_ghost.requests,
            "get",
            return_value=ghost_response(posts, next_page),
        ):
            main.main(self.db)


class TestProviderRegistry(unittest.TestCase):
    def test_known_providers(self):
        self.assertIsInstance(
            providers.get_provider("ghost"), provider_ghost.GhostProvider
        )
        self.assertIsInstance(
            providers.get_provider("superdesk"), provider_superdesk.SuperdeskProvider
        )

    def test_unknown_provider_names_the_known_ones(self):
        with self.assertRaises(ValueError) as ctx:
            providers.get_provider("wordpress")
        self.assertIn("ghost, superdesk", str(ctx.exception))

    def test_provider_validates_its_own_settings(self):
        with mock.patch.object(settings, "PESACHECK_GHOST_CONTENT_API_KEY", None):
            with self.assertRaises(ValueError):
                providers.get_provider("ghost")
            # A missing Ghost key does not stop Superdesk running.
            providers.get_provider("superdesk")
        with mock.patch.object(settings, "PESACHECK_SUPERDESK_TENANT_CODE", None):
            with self.assertRaises(ValueError):
                providers.get_provider("superdesk")


class TestGhostProvider(Base):
    def test_first_run_fetches_single_page_without_filter(self):
        with mock.patch.object(
            provider_ghost.requests,
            "get",
            return_value=ghost_response([ghost_post(2), ghost_post(1)], next_page=2),
        ) as get:
            posts = provider_ghost.GhostProvider().fetch(since=None, limit=2)
        self.assertEqual(len(posts), 2)
        self.assertEqual(get.call_count, 1)
        self.assertNotIn("filter", get.call_args.kwargs["params"])

    def test_sends_identifying_user_agent(self):
        with mock.patch.object(
            provider_ghost.requests, "get", return_value=ghost_response([])
        ) as get:
            provider_ghost.GhostProvider().fetch()
        headers = get.call_args.kwargs["headers"]
        self.assertEqual(headers["User-Agent"], provider_base.USER_AGENT)
        self.assertNotIn("python-requests", headers["User-Agent"])

    def test_checkpoint_follows_next_until_exhausted(self):
        pages = [
            ghost_response([ghost_post(5), ghost_post(4)], next_page=2),
            ghost_response([ghost_post(3), ghost_post(2)], next_page=3),
            ghost_response([ghost_post(1)], next_page=None),
        ]
        seen = []

        def fake_get(url, params, headers, timeout):
            seen.append((params["page"], params["filter"]))
            return pages[params["page"] - 1]

        tz = datetime.fromisoformat("2026-01-01T00:00+03:00").tzinfo
        since = datetime(2026, 9, 1, 13, 0, tzinfo=tz)
        with mock.patch.object(provider_ghost.requests, "get", side_effect=fake_get):
            posts = provider_ghost.GhostProvider().fetch(since=since, limit=2)
        self.assertEqual(
            [p["title"] for p in posts], [f"Post {i}" for i in (5, 4, 3, 2, 1)]
        )
        self.assertEqual(seen[0], (1, "published_at:>='2026-09-01 10:00:00'"))

    def test_parse_maps_tags_and_language(self):
        article = provider_ghost.GhostProvider().parse(ghost_post(1))
        self.assertEqual(article.guid, ghost_post(1)["id"])
        self.assertEqual(article.categories, ["Somali"])
        self.assertEqual(article.language, "so")
        self.assertEqual(article.summary, "Summary 1")
        self.assertEqual(article.url, "https://pesacheck.org/post-1/")

    def test_checkpoint_is_scoped_to_the_provider(self):
        self.add_row("https://medium.com/p/abc", "2030-01-01 00:00:00", source="medium")
        self.assertIsNone(main.get_checkpoint(self.db, "ghost"))
        self.add_row("a" * 24, "2026-09-01T10:00:00.000+00:00")
        self.add_row("b" * 24, "2026-09-03T10:00:00.000+00:00")
        self.assertEqual(
            main.get_checkpoint(self.db, "ghost"), datetime(2026, 9, 3, 10, tzinfo=UTC)
        )
        self.assertIsNone(main.get_checkpoint(self.db, "superdesk"))

    def test_burst_larger_than_limit_is_fully_imported_oldest_first(self):
        self.add_row("0" * 24, "2026-09-01T10:00:00.000+00:00")
        pages = [
            ghost_response([ghost_post(5, 5), ghost_post(4, 4)], next_page=2),
            ghost_response([ghost_post(3, 3), ghost_post(2, 2)], next_page=None),
        ]
        with mock.patch.object(
            provider_ghost.requests,
            "get",
            side_effect=lambda url, params, **kw: pages[params["page"] - 1],
        ):
            main.main(self.db)
        self.assertEqual(
            [d["title"] for d in self.posted], ["Post 2", "Post 3", "Post 4", "Post 5"]
        )
        self.assertEqual(self.posted[0]["language"], "so")
        self.assertEqual(self.posted[0]["set_tags"], ["Somali"])
        self.assertEqual(set(self.sources().values()), {"ghost"})

    def test_fetch_error_on_later_page_stores_nothing(self):
        self.add_row("0" * 24, "2026-09-01T10:00:00.000+00:00")
        err = mock.Mock(status_code=500, text="boom")
        pages = [ghost_response([ghost_post(5, 5)], next_page=2), err]
        with mock.patch.object(
            provider_ghost.requests,
            "get",
            side_effect=lambda url, params, **kw: pages[params["page"] - 1],
        ):
            with self.assertRaises(Exception):
                main.main(self.db)
        self.assertEqual(self.posted, [])
        self.assertEqual(len(self.rows()), 1)


class TestSuperdeskProvider(Base):
    provider = "superdesk"

    def run_superdesk(self, articles):
        with mock.patch.object(
            provider_superdesk.requests,
            "post",
            return_value=superdesk_response(articles),
        ):
            main.main(self.db)

    def test_parse_maps_the_staging_shape(self):
        article = provider_superdesk.SuperdeskProvider().parse(superdesk_article(1))
        self.assertEqual(article.guid, "uuid-1")
        self.assertEqual(article.title, "Post 1")
        self.assertEqual(article.url, "https://pesacheck.org/fact-checks/somali/post-1")
        self.assertEqual(article.summary, "Summary 1")  # HTML stripped
        self.assertEqual(article.language, "so")
        self.assertEqual(
            article.categories, ["Somali", "Kenya", "Quick Read", "Sports"]
        )
        self.assertEqual(article.published_at, "2026-09-01T10:00:00+00:00")
        self.assertEqual(article.author, "A")

    def test_url_base_is_configurable(self):
        with mock.patch.object(
            settings, "PESACHECK_SITE_URL", "https://pesacheck-ui.vercel.app/"
        ):
            article = provider_superdesk.SuperdeskProvider().parse(superdesk_article(1))
        self.assertEqual(
            article.url, "https://pesacheck-ui.vercel.app/fact-checks/somali/post-1"
        )

    def test_falls_back_to_numeric_id_without_a_guid(self):
        article = superdesk_article(1)
        article["metadata"] = json.dumps({"subject": []})
        self.assertEqual(
            provider_superdesk.SuperdeskProvider().parse(article).guid, "6001"
        )

    def test_unparseable_metadata_does_not_crash(self):
        article = superdesk_article(1)
        article["metadata"] = "not json"
        parsed = provider_superdesk.SuperdeskProvider().parse(article)
        self.assertEqual(parsed.categories, [])
        self.assertEqual(parsed.language, "")

    def test_query_filters_to_fact_checks_for_the_tenant(self):
        with mock.patch.object(
            provider_superdesk.requests, "post", return_value=superdesk_response([])
        ) as post:
            provider_superdesk.SuperdeskProvider().fetch(
                since=datetime(2026, 9, 1, 10, tzinfo=UTC), limit=5
            )
        where = post.call_args.kwargs["json"]["variables"]["where"]
        self.assertEqual(where["tenant_code"], {"_eq": "123abc"})
        self.assertEqual(where["published_at"]["_gte"], "2026-09-01T10:00:00")
        self.assertEqual(
            where["_and"][0]["swp_article_metadata"]["swp_article_metadata_subjects"],
            {"scheme": {"_eq": "Debunk"}},
        )

    def test_first_run_fetches_a_single_page(self):
        with mock.patch.object(
            provider_superdesk.requests,
            "post",
            return_value=superdesk_response([superdesk_article(i) for i in range(2)]),
        ) as post:
            articles = provider_superdesk.SuperdeskProvider().fetch(since=None, limit=2)
        self.assertEqual(post.call_count, 1)
        self.assertEqual(len(articles), 2)

    def test_pages_until_a_short_page(self):
        pages = [
            superdesk_response([superdesk_article(1), superdesk_article(2)]),
            superdesk_response([superdesk_article(3)]),
        ]
        offsets = []

        def fake_post(url, json, headers, timeout):
            offsets.append(json["variables"]["offset"])
            return pages[len(offsets) - 1]

        with mock.patch.object(
            provider_superdesk.requests, "post", side_effect=fake_post
        ):
            articles = provider_superdesk.SuperdeskProvider().fetch(
                since=datetime(2026, 9, 1, tzinfo=UTC), limit=2
            )
        self.assertEqual(offsets, [0, 2])
        self.assertEqual(len(articles), 3)

    def test_graphql_errors_are_raised(self):
        resp = mock.Mock(status_code=200, text='{"errors":[{"message":"boom"}]}')
        resp.json.return_value = {"errors": [{"message": "boom"}]}
        with mock.patch.object(provider_superdesk.requests, "post", return_value=resp):
            with self.assertRaises(Exception):
                provider_superdesk.SuperdeskProvider().fetch()

    def test_preshared_auth_header_sent_when_configured(self):
        with mock.patch.object(
            settings, "PESACHECK_SUPERDESK_PRESHARED_AUTH", "s3cret"
        ):
            with mock.patch.object(
                provider_superdesk.requests, "post", return_value=superdesk_response([])
            ) as post:
                provider_superdesk.SuperdeskProvider().fetch()
        self.assertEqual(post.call_args.kwargs["headers"]["x-preshared-auth"], "s3cret")

    def test_end_to_end_posts_and_records_the_source(self):
        self.run_superdesk([superdesk_article(2, day=3), superdesk_article(1, day=2)])
        self.assertEqual([d["title"] for d in self.posted], ["Post 1", "Post 2"])
        self.assertEqual(self.posted[0]["language"], "so")
        self.assertEqual(
            self.posted[0]["set_tags"], ["Somali", "Kenya", "Quick Read", "Sports"]
        )
        self.assertEqual(
            self.posted[0]["url"], "https://pesacheck.org/fact-checks/somali/post-1"
        )
        self.assertEqual(set(self.sources().values()), {"superdesk"})
        self.assertEqual(
            main.get_checkpoint(self.db, "superdesk"),
            datetime(2026, 9, 3, 10, tzinfo=UTC),
        )

    def test_rerun_posts_nothing(self):
        self.run_superdesk([superdesk_article(1)])
        self.run_superdesk([superdesk_article(1)])
        self.assertEqual(len(self.posted), 1)

    def test_switching_providers_keeps_separate_checkpoints(self):
        self.run_superdesk([superdesk_article(1, day=5)])
        settings.PESACHECK_PROVIDER = "ghost"
        self.run_ghost([ghost_post(9, day=2)])
        self.assertEqual([d["title"] for d in self.posted], ["Post 1", "Post 9"])
        self.assertEqual(self.sources(), {"uuid-1": "superdesk", f"{9:024x}": "ghost"})
        self.assertEqual(
            main.get_checkpoint(self.db, "superdesk"),
            datetime(2026, 9, 5, 10, tzinfo=UTC),
        )
        self.assertEqual(
            main.get_checkpoint(self.db, "ghost"), datetime(2026, 9, 2, 10, tzinfo=UTC)
        )


class TestMigration(unittest.TestCase):
    """A database created before the source/language columns existed."""

    OLD_SCHEMA = """CREATE TABLE pesacheck_feeds
        (title TEXT NOT NULL, pubDate TEXT NOT NULL, author TEXT NOT NULL,
         guid TEXT PRIMARY KEY, link TEXT NOT NULL, thumbnail TEXT NOT NULL,
         description TEXT NOT NULL, status TEXT DEFAULT 'Pending',
         categories TEXT DEFAULT '[]', check_project_media_id TEXT,
         check_full_url TEXT, claim_description_id TEXT)"""

    def setUp(self):
        fd, self.db_file = tempfile.mkstemp(suffix=".db", dir=TMP)
        os.close(fd)
        conn = sqlite3.connect(self.db_file)
        conn.execute(self.OLD_SCHEMA)
        conn.execute(
            "INSERT INTO pesacheck_feeds VALUES "
            "('t','2024-11-18 23:19:22','a','https://medium.com/p/1','l','','d',"
            "'Completed','[]','','','')"
        )
        conn.execute(
            "INSERT INTO pesacheck_feeds VALUES "
            "('t','2026-09-18T07:23:07.000+00:00','a','6aace4daa4a78b00073f9a6e',"
            "'l','','d','Completed','[]','','','')"
        )
        conn.commit()
        conn.close()
        settings.PESACHECK_DATABASE_NAME = self.db_file

    def test_adds_columns_and_backfills_source(self):
        db = database.PesacheckDatabase()
        conn = sqlite3.connect(self.db_file)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(pesacheck_feeds)")}
        self.assertIn("source", columns)
        self.assertIn("language", columns)
        sources = dict(conn.execute("SELECT guid, source FROM pesacheck_feeds"))
        conn.close()
        self.assertEqual(sources["https://medium.com/p/1"], "medium")
        self.assertEqual(sources["6aace4daa4a78b00073f9a6e"], "ghost")
        # The Ghost row's date becomes the Ghost checkpoint; Medium's does not.
        self.assertEqual(
            main.get_checkpoint(db, "ghost"),
            datetime.fromisoformat("2026-09-18T07:23:07.000+00:00"),
        )

    def test_is_idempotent_and_rows_still_load(self):
        database.PesacheckDatabase()
        db = database.PesacheckDatabase()
        feeds = db.get_pesacheck_feeds_by_status("Completed")
        self.assertEqual(len(feeds), 2)
        self.assertEqual({f.source for f in feeds}, {"medium", "ghost"})

    def test_legacy_medium_summary_still_uses_the_figure_rule(self):
        database.PesacheckDatabase()
        feed = database.PesacheckFeed(
            title="t",
            pubDate="",
            author="",
            guid="https://medium.com/p/2",
            link="",
            thumbnail="",
            description="<p>The summary.</p><figure><img src=x></figure>",
            status="Pending",
            categories="[]",
            source="medium",
        )
        self.assertEqual(main.extract_summary(feed), "The summary.")
        feed.description = "<p>Body only</p>"
        self.assertIsNone(main.extract_summary(feed))


class TestDatabaseWrites(Base):
    def test_failed_insert_does_not_post(self):
        with mock.patch.object(
            self.db,
            "insert_pesacheck_feed",
            side_effect=sqlite3.OperationalError("locked"),
        ):
            self.run_ghost([ghost_post(1)])
        self.assertEqual(self.posted, [])
        self.sentry_exc.assert_called_once()

    def test_failed_claim_does_not_post(self):
        with mock.patch.object(
            self.db,
            "claim_pending_feed",
            side_effect=sqlite3.OperationalError("locked"),
        ):
            self.run_ghost([ghost_post(1)])
        self.assertEqual(self.posted, [])
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Pending"})
        self.sentry_exc.assert_called_once()

    def test_failed_update_after_post_is_not_reposted(self):
        with mock.patch.object(
            self.db,
            "update_pesacheck_feed",
            side_effect=sqlite3.OperationalError("full"),
        ):
            self.run_ghost([ghost_post(1)])
        self.assertEqual(len(self.posted), 1)
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Posting"})
        self.sentry_msg.reset_mock()
        self.run_ghost([ghost_post(1)])
        self.assertEqual(len(self.posted), 1)
        levels = [c.kwargs.get("level") for c in self.sentry_msg.call_args_list]
        self.assertIn("warning", levels)

    def test_check_error_reverts_to_pending_and_retries(self):
        self.post_mock.side_effect = Exception('{"errors": ["bad"]}')
        self.run_ghost([ghost_post(1)])
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Pending"})
        self.post_mock.side_effect = lambda data: (
            self.posted.append(data),
            check_response(1),
        )[1]
        self.run_ghost([])
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Completed"})
        self.assertEqual(len(self.posted), 1)

    def test_check_timeout_leaves_posting(self):
        self.post_mock.side_effect = requests.Timeout("timed out")
        self.run_ghost([ghost_post(1)])
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


class TestBatchFailures(Base):
    def test_failed_insert_aborts_batch_and_holds_checkpoint(self):
        self.add_row("0" * 24, "2026-09-01T10:00:00.000+00:00")
        before = main.get_checkpoint(self.db, "ghost")
        older, newer = ghost_post(1, day=2), ghost_post(2, day=3)
        real_insert = self.db.insert_pesacheck_feed

        def flaky(feed):
            if feed.guid == older["id"]:
                raise sqlite3.OperationalError("database is locked")
            return real_insert(feed)

        with mock.patch.object(self.db, "insert_pesacheck_feed", side_effect=flaky):
            self.run_ghost([newer, older])
        self.assertNotIn(older["id"], self.rows())
        self.assertNotIn(newer["id"], self.rows())
        self.assertEqual(main.get_checkpoint(self.db, "ghost"), before)
        self.assertEqual(self.posted, [])
        self.run_ghost([newer, older])
        self.assertEqual([d["title"] for d in self.posted], ["Post 1", "Post 2"])

    def test_malformed_post_does_not_block_later_articles(self):
        bad = ghost_post(1, day=2)
        del bad["title"]
        self.run_ghost([ghost_post(2, day=3), bad])
        self.assertEqual([d["title"] for d in self.posted], ["Post 2"])
        self.assertIsInstance(self.sentry_exc.call_args.args[0], KeyError)

    def test_duplicate_post_across_pages_is_handled_once(self):
        dup = ghost_post(1, day=2)
        pages = [
            ghost_response([ghost_post(2, day=3), dup], next_page=2),
            ghost_response([dup, ghost_post(3, day=1)], next_page=None),
        ]
        self.add_row("0" * 24, "2026-09-01T10:00:00.000+00:00")
        with mock.patch.object(
            provider_ghost.requests,
            "get",
            side_effect=lambda url, params, **kw: pages[params["page"] - 1],
        ):
            main.main(self.db)
        self.assertEqual(
            [d["title"] for d in self.posted], ["Post 3", "Post 1", "Post 2"]
        )
        self.sentry_exc.assert_not_called()

    def test_bad_categories_leave_row_pending_without_posting(self):
        self.add_row("a" * 24, "", status="Pending")
        conn = sqlite3.connect(self.db_file)
        conn.execute("UPDATE pesacheck_feeds SET categories = 'not-json'")
        conn.commit()
        conn.close()
        self.run_ghost([])
        self.assertEqual(self.posted, [])
        self.assertEqual(self.rows(), {"a" * 24: "Pending"})

    def test_whole_run_failure_raises(self):
        with mock.patch.object(
            provider_ghost.requests, "get", side_effect=requests.ConnectionError("down")
        ):
            with self.assertRaises(requests.ConnectionError):
                main.main(self.db)
        self.assertTrue(self.sentry_msg.called)


class TestDuplicates(Base):
    def test_duplicate_is_marked_terminally_and_not_retried(self):
        self.post_mock.side_effect = check_api.DuplicateFactCheckError("dup")
        self.run_ghost([ghost_post(1)])
        self.assertEqual(self.rows(), {ghost_post(1)["id"]: "Duplicate"})
        # The in-memory feed agrees with the row, so later reads can't drift.
        self.assertEqual(
            self.db.get_pesacheck_feeds_by_status("Duplicate")[0].status, "Duplicate"
        )
        self.sentry_exc.reset_mock()
        self.post_mock.reset_mock()
        self.run_ghost([])
        self.post_mock.assert_not_called()
        self.sentry_exc.assert_not_called()

    def test_duplicates_are_summarised_once_not_reported_as_errors(self):
        self.post_mock.side_effect = check_api.DuplicateFactCheckError("dup")
        self.run_ghost([ghost_post(2, day=3), ghost_post(1, day=2)])
        self.sentry_exc.assert_not_called()
        message = self.sentry_msg.call_args.args[0]
        self.assertIn("Skipped 2 PesaCheck article(s) Check already has", message)

    def test_pending_duplicate_from_an_earlier_run_is_resolved(self):
        self.add_row("a" * 24, "", status="Pending")
        self.post_mock.side_effect = check_api.DuplicateFactCheckError("dup")
        self.run_ghost([])
        self.assertEqual(self.rows(), {"a" * 24: "Duplicate"})


class TestSummary(Base):
    def feed(self, source, description):
        return database.PesacheckFeed(
            title="t",
            pubDate="",
            author="",
            guid="g",
            link="",
            thumbnail="",
            description=description,
            status="Pending",
            categories="[]",
            source=source,
        )

    def test_provider_summary_is_used_as_is(self):
        self.assertEqual(
            main.extract_summary(self.feed("ghost", "  A claim & more ")),
            "A claim & more",
        )
        self.assertIsNone(main.extract_summary(self.feed("superdesk", "  ")))

    def test_legacy_without_figure_posts_not_found(self):
        self.add_row(
            "https://medium.com/p/1",
            "",
            status="Pending",
            description="<p>Body</p>",
            source="medium",
        )
        self.run_ghost([])
        self.assertEqual(self.posted[0]["summary"], "Not Found")


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
            self.run_ghost([ghost_post(1)])
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
            self.call_with(self.duplicate_payload)

    def test_other_graphql_errors_are_not_duplicates(self):
        with self.assertRaises(Exception) as ctx:
            self.call_with({"errors": [{"message": "Mutation rejected"}]})
        self.assertNotIsInstance(ctx.exception, check_api.DuplicateFactCheckError)

    def test_rejects_non_200(self):
        with self.assertRaises(Exception):
            self.call_with(check_response(1), status=500)


if __name__ == "__main__":
    unittest.main(verbosity=2)
