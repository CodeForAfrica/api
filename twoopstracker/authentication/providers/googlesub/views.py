from django.conf import settings

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2CallbackView,
    OAuth2LoginView,
)
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .provider import GoogleSubProvider


class GoogleSubOAuth2Adapter(GoogleOAuth2Adapter):
    provider_id = GoogleSubProvider.id

    def complete_login(self, request, app, token, **kwargs):
        idinfo = id_token.verify_oauth2_token(
            token.token,
            google_requests.Request(),
            settings.TWOOPSTRACKER_GOOGLE_OAUTH2_CLIENT_ID,
        )
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer.")

        extra_data = idinfo
        login = self.get_provider().sociallogin_from_response(request, extra_data)
        return login


oauth2_login = OAuth2LoginView.adapter_view(GoogleSubOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(GoogleSubOAuth2Adapter)
