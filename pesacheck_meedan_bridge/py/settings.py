from environs import Env
import sentry_sdk


env = Env()
env.read_env()


PESACHECK_SENTRY_DSN = env("PESACHECK_SENTRY_DSN", None)
PESACHECK_SENTRY_ENVIRONMENT = env("PESACHECK_SENTRY_ENVIRONMENT", "local")
PESACHECK_SENTRY_TRACES_SAMPLE_RATE = env("PESACHECK_SENTRY_TRACES_SAMPLE_RATE", 1.0)

PESACHECK_RSS2JSON_API_KEY = env("PESACHECK_RSS2JSON_API_KEY")
PESACHECK_URL = env("PESACHECK_URL")

PESACHECK_CHECK_URL = env("PESACHECK_CHECK_URL")
PESACHECK_CHECK_TOKEN = env("PESACHECK_CHECK_TOKEN")
PESACHECK_CHECK_WORKSPACE_SLUG = env("PESACHECK_CHECK_WORKSPACE_SLUG")


if PESACHECK_SENTRY_DSN:
    sentry_sdk.init(
        dsn=PESACHECK_SENTRY_DSN,
        environment=PESACHECK_SENTRY_ENVIRONMENT,
        traces_sample_rate=PESACHECK_SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=1.0
    )
    