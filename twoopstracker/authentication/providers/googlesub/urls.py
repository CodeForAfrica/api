from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import GoogleSubProvider


urlpatterns = default_urlpatterns(GoogleSubProvider)
