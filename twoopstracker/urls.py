"""twoopstracker URL Configuration
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("twoopstracker.authentication.urls")),
    path("v1/", include("twoopstracker.twoops.urls")),
]
