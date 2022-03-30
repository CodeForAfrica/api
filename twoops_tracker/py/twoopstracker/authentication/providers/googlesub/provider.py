from allauth.socialaccount.providers.google.provider import GoogleProvider


class GoogleSubProvider(GoogleProvider):
    """The default GoogleProvider uses data["id"] to extact uid.

    However, Google have changed their API to use data["sub"] instead.
    """

    id = "google_sub"
    name = "Google Sub"

    def extract_uid(self, data):
        return str(data["sub"])


provider_classes = [GoogleSubProvider]
