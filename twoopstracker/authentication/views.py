from allauth.socialaccount import signals
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import UserDetailsView as BaseUserDetailsView
from rest_framework.generics import RetrieveUpdateDestroyAPIView

from .providers.googlesub.views import GoogleSubOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleSubOAuth2Adapter
    client_class = OAuth2Client


class UserDetailsView(BaseUserDetailsView, RetrieveUpdateDestroyAPIView):
    def perform_destroy(self, instance):
        social_account = SocialAccount.objects.filter(user=instance).first()
        if social_account:
            # NOTE(kilemensi): Since we're deleting it, skip any validation
            #                  such as
            # https://github.com/pennersr/django-allauth/blob/0.47.0/allauth/socialaccount/adapter.py
            social_account.delete()
            signals.social_account_removed.send(
                sender=SocialAccount,
                request=self.request,
                socialaccount=social_account,
            )

        return super().perform_destroy(instance)
