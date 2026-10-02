import sentry_sdk
from environs import Env

env = Env()
env.read_env()


PESACHECK_SENTRY_DSN = env("PESACHECK_SENTRY_DSN", None)
PESACHECK_SENTRY_ENVIRONMENT = env("PESACHECK_SENTRY_ENVIRONMENT", "local")
PESACHECK_SENTRY_TRACES_SAMPLE_RATE = env("PESACHECK_SENTRY_TRACES_SAMPLE_RATE", 1.0)

# Initialise Sentry before reading required settings so that a missing
# variable is reported instead of failing silently on import.
if PESACHECK_SENTRY_DSN:
    sentry_sdk.init(
        dsn=PESACHECK_SENTRY_DSN,
        environment=PESACHECK_SENTRY_ENVIRONMENT,
        traces_sample_rate=PESACHECK_SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=1.0,
    )

# Which CMS to read fact-checks from: "ghost" or "superdesk". Each provider
# validates its own settings, so only the active one's are required.
PESACHECK_PROVIDER = env("PESACHECK_PROVIDER", "ghost")

# Page size, and the number of articles a run with no checkpoint fetches.
# Falls back to the old Ghost-only name so existing deployments keep theirs.
PESACHECK_POSTS_LIMIT = env.int(
    "PESACHECK_POSTS_LIMIT", env.int("PESACHECK_GHOST_POSTS_LIMIT", 15)
)

# Ceiling on one run when catching up from a checkpoint. Without it, a
# checkpoint far in the past (a long outage, or the first run after switching
# provider) would import years of articles, posting all of them to Check.
# Catch-up then continues on the next run, since the checkpoint advances.
PESACHECK_MAX_ARTICLES = env.int("PESACHECK_MAX_ARTICLES", 100)

# Public site, used to build the article URL posted to Check.
PESACHECK_SITE_URL = env("PESACHECK_SITE_URL", "https://pesacheck.org")

# How a Superdesk article's public URL is built, as a template over
# {site}, {desk} (the Publisher route slug) and {slug}. The default is the
# Ghost-era shape, which is what every fact-check already in Check links to;
# switch it to "{site}/fact-checks/{desk}/{slug}" once the new site serves
# that as the canonical URL.
PESACHECK_ARTICLE_URL_TEMPLATE = env("PESACHECK_ARTICLE_URL_TEMPLATE", "{site}/{slug}/")

# Ghost
PESACHECK_URL = env("PESACHECK_URL", "https://pesacheck.org")
PESACHECK_GHOST_CONTENT_API_KEY = env("PESACHECK_GHOST_CONTENT_API_KEY", None)

# Superdesk (Publisher's GraphQL API)
PESACHECK_SUPERDESK_GRAPHQL_URL = env("PESACHECK_SUPERDESK_GRAPHQL_URL", None)
PESACHECK_SUPERDESK_TENANT_CODE = env("PESACHECK_SUPERDESK_TENANT_CODE", None)
# Shared secret a Cloudflare WAF rule matches to skip bot protection.
PESACHECK_SUPERDESK_PRESHARED_AUTH = env("PESACHECK_SUPERDESK_PRESHARED_AUTH", None)

PESACHECK_CHECK_URL = env("PESACHECK_CHECK_URL")
PESACHECK_CHECK_TOKEN = env("PESACHECK_CHECK_TOKEN")
PESACHECK_CHECK_WORKSPACE_SLUG = env("PESACHECK_CHECK_WORKSPACE_SLUG")
PESACHECK_DATABASE_NAME = env("PESACHECK_DATABASE_NAME")
