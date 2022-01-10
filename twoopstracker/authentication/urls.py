from django.conf.urls import include
from django.urls import path

from .views import GoogleLogin

urlpatterns = [
    path("google/", GoogleLogin.as_view(), name="google_login"),
    path("registration/", include("dj_rest_auth.registration.urls")),
    path("", include("dj_rest_auth.urls")),
]
