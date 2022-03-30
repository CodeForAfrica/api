from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import PasswordResetConfirmView
from django.conf.urls import include
from django.urls import path

from .views import GoogleLogin, UserDetailsView

urlpatterns = [
    path(
        "password/reset/confirm/<uid>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "account-confirm-email/",
        VerifyEmailView.as_view(),
        name="account_email_verification_sent",
    ),
    path("google/", GoogleLogin.as_view(), name="google_login"),
    path("registration/", include("dj_rest_auth.registration.urls")),
    path("user/", UserDetailsView.as_view(), name="rest_user_details"),
    path("", include("dj_rest_auth.urls")),
]
