from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from .providers.googlesub.views import GoogleSubOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleSubOAuth2Adapter
    client_class = OAuth2Client
