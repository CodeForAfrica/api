from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import PasswordResetConfirmView
from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.views.generic.base import RedirectView

from .views import GoogleLogin

urlpatterns = [
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "account-confirm-email/",
        VerifyEmailView.as_view(),
        name="account_email_verification_sent",
    ),
    path("google/", GoogleLogin.as_view(), name="google_login"),
    path(
        "registration/account-confirm-email/<str:key>/",
        RedirectView.as_view(url=f"{settings.TWOOPSTRACKER_CONFIRM_EMAIL_URL}/%(key)s"),
    ),
    path("registration/", include("dj_rest_auth.registration.urls")),
    path("", include("dj_rest_auth.urls")),
]
