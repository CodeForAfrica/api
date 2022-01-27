from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import PasswordResetConfirmView
from django.conf import settings
from django.shortcuts import redirect

from .providers.googlesub.views import GoogleSubOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleSubOAuth2Adapter
    client_class = OAuth2Client


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    def get(self, request, *args, **kwargs):
        uid = kwargs["uid"]
        token = kwargs["token"]
        uri = settings.TWOOPSTRACKER_CONFIRM_RESET_PASSWORD_URL.rstrip("/")
        url = f"{uri}/{uid}/{token}"
        return redirect(url)
