"""twoopstracker URL Configuration."""

from django.contrib import admin
from django.urls import include, path

from .health import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("twoopstracker.authentication.urls")),
    path("v1/", include("twoopstracker.twoops.urls")),
    path("health/", health_check, name="health_check"),
]
