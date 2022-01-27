from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.views import PasswordResetConfirmView
from dj_rest_auth.registration.views import SocialLoginView
from django.shortcuts import redirect
from django.conf import settings

from .providers.googlesub.views import GoogleSubOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleSubOAuth2Adapter
    client_class = OAuth2Client

class CusstomPasswordResetConfirmView(PasswordResetConfirmView):
    def get(self, request, *args, **kwargs):
        uid = kwargs["uid"]
        token = kwargs["token"]
        url = f"{settings.TWOOPSTRACKER_CONFIRM_RESET_PASSWORD_URL}/{uid}/{token}"
        return redirect(url)
