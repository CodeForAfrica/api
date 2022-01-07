"""twoopstracker URL Configuration
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("twoopstracker.authentication.urls")),
    path("v1/", include("twoopstracker.twoops.urls")),

    # NOTE(kilemensi): This is a temporary test fix for
    # Reverse for 'socialaccount_signup' not found. 'socialaccount_signup' is not a valid view function or pattern name.
    path('accounts/', include('allauth.urls')),
]
