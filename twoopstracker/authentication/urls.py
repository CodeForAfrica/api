from dj_rest_auth.registration.views import ConfirmEmailView, VerifyEmailView
from django.conf.urls import include
from django.urls import path

from .views import GoogleLogin

urlpatterns = [
    path('verify-email/',
         VerifyEmailView.as_view(), name='rest_verify_email'),
    path(
        "account-confirm-email/",
        VerifyEmailView.as_view(),
        name="account_email_verification_sent",
    ),
    path("google/", GoogleLogin.as_view(), name="google_login"),
    path("registration/account-confirm-email/<str:key>/", ConfirmEmailView.as_view()),
    path("registration/", include("dj_rest_auth.registration.urls")),
    path("", include("dj_rest_auth.urls")),
]
