from provider_ghost import GhostProvider
from provider_superdesk import SuperdeskProvider

PROVIDERS = {
    GhostProvider.name: GhostProvider,
    SuperdeskProvider.name: SuperdeskProvider,
}


def get_provider(name):
    """The configured CMS the bridge reads fact-checks from."""
    try:
        provider = PROVIDERS[name]
    except KeyError:
        known = ", ".join(sorted(PROVIDERS))
        raise ValueError(
            f"Unknown PESACHECK_PROVIDER {name!r}. Known providers: {known}"
        ) from None
    return provider()
