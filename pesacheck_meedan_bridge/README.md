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

## How articles are picked up

Each run fetches everything published since the newest PesaCheck (Ghost) article
already stored in SQLite, paginating in pages of `PESACHECK_GHOST_POSTS_LIMIT`.
When nothing is stored yet, only the newest page is fetched, so the first run
against a fresh database does not backfill PesaCheck's whole archive.

Articles are tracked by `status`:

| Status | Meaning |
|---|---|
| `Pending` | Stored, not yet accepted by Check. Retried on every run. |
| `Posting` | Sent to Check, but the outcome could not be recorded (e.g. a timeout). **Not** retried automatically: check the article in Check, then set the row to `Completed` (with the Check ids) or back to `Pending`. Each run reports these to Sentry. |
| `Completed` | Accepted by Check, with the Check ids stored. |

### Known limitation: backdated articles

The cursor is the newest `published_at` we have stored, so an article published
with a date earlier than that is never picked up. Backdated publishing is
therefore not supported. If PesaCheck starts backdating articles, the cursor
needs to move to `updated_at` or be paired with a periodic sweep of a wider
date range (deduplicating by Ghost id).
