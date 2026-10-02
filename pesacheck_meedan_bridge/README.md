# Pesacheck Meedan Bridge

A simple service to pull articles from PesaCheck and post them to Meedan Check using Meedan Graphql API. This service acts as a bridge between PesaCheck and Meedan Check, allowing for seamless transfer of articles from one platform to another.

## Getting Started

First create `.env` file in the app directory. From project root directory,

```sh
cp  pesacheck_meedan_bridge/.env.example pesacheck_meedan_bridge/.env
```

and modify the `.env` file according to your needs.

## Build

To build a `pex` binary, run:

```sh
pants package pesacheck_meedan_bridge/py:pesacheck_meedan_bridge
```

To build the docker image, run:

```sh
VERSION=$(cat pesacheck_meedan_bridge/py/VERSION) pants package pesacheck_meedan_bridge/docker:pesacheck_meedan_bridge
```

## Run

To run the built docker image, execute:

```sh
docker compose --env-file ./pesacheck_meedan_bridge/.env up pesacheck_meedan_bridge
```


To run `pex` binary, execute:

```sh
docker compose exec api-pesacheck_meedan_bridge ./pex
```

## Where articles come from

`PESACHECK_PROVIDER` selects the CMS the bridge reads:

| Provider | Reads | Needs |
|---|---|---|
| `ghost` | Ghost Content API at `{PESACHECK_URL}/ghost/api/content/posts/` | `PESACHECK_GHOST_CONTENT_API_KEY` |
| `superdesk` | Publisher's GraphQL API (`swp_article`), filtered to the tenant and to articles carrying a `Debunk` verdict | `PESACHECK_SUPERDESK_GRAPHQL_URL`, `PESACHECK_SUPERDESK_TENANT_CODE` |

Only the active provider's settings are required, so switching is a config
change plus a restart. Each article records the provider it came from in the
`source` column, and the fetch position is tracked per provider.

A provider that has no articles of its own yet — the first run after a switch —
starts from the newest article stored under *any* source, i.e. wherever the
previous provider stopped. Both CMSes hold the same fact-checks under different
ids and URLs, so starting from scratch would re-post them: Check would not
reject them as duplicates, because its signature covers the fact-check URL,
which differs between the two sites. It would also skip anything published
beyond one page since the last run.

Superdesk articles are posted to Check with a URL built from
`PESACHECK_SITE_URL` and `PESACHECK_ARTICLE_URL_TEMPLATE` (`{site}`, `{desk}`,
`{slug}`); point the site at a preview deployment to test against one.
Publisher has no canonical-URL field — `swp_redirect_route` is empty — so the
URL is assembled here, and the default keeps the Ghost-era `{site}/{slug}/`
shape that every fact-check already in Check links to. The shape matters
beyond the link: Check's duplicate signature covers the fact-check URL, so
changing it makes already-imported articles look new.

Their language comes from Superdesk directly, and the Check tags are the
language, country, content type and harm type.

## How articles are picked up

Each run fetches everything published since the newest article already stored
for the active provider, oldest first, in pages of `PESACHECK_POSTS_LIMIT` and
at most `PESACHECK_MAX_ARTICLES` per run. The cap bounds a checkpoint far in
the past — a long outage, or the first run after a provider switch — and
costs nothing: the checkpoint advances as articles are stored, so the next run
picks up where this one stopped.

When nothing is stored yet, only the newest page is fetched, so the first run
against a fresh database does not backfill PesaCheck's whole archive.

Articles are tracked by `status`:

| Status | Meaning |
|---|---|
| `Pending` | Stored, not yet accepted by Check. Retried on every run. |
| `Posting` | Sent to Check, but the outcome could not be recorded (e.g. a timeout). **Not** retried automatically: check the article in Check, then set the row to `Completed` (with the Check ids) or back to `Pending`. Each run reports these to Sentry. |
| `Completed` | Accepted by Check, with the Check ids stored. |
| `Duplicate` | Check already has this fact-check (it rejects a repeat of the same content). Terminal: never retried. The Check ids are not recorded, so find the article in Check by title if you need them. |

### Adding another provider

Add a module exposing `name`, `fetch(since, limit)` returning raw records, and
`parse(record)` returning a `provider_base.Article`; register it in
`providers.py`. `main.py` knows nothing about any particular CMS.

### Known limitation: backdated articles

The cursor is the newest `published_at` we have stored, so an article published
with a date earlier than that is never picked up. Backdated publishing is
therefore not supported. If PesaCheck starts backdating articles, the cursor
needs to move to `updated_at` or be paired with a periodic sweep of a wider
date range (deduplicating by Ghost id).
