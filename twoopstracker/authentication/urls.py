from dj_rest_auth.registration.views import VerifyEmailView
from django.conf.urls import include
from django.urls import path

from .views import GoogleLogin

urlpatterns = [
    path(
        "account-confirm-email/",
        VerifyEmailView.as_view(),
        name="account_email_verification_sent",
    ),
    path("google/", GoogleLogin.as_view(), name="google_login"),
    path("registration/", include("dj_rest_auth.registration.urls")),
    path("", include("dj_rest_auth.urls")),
]
