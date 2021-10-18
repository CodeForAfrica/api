from django.contrib import admin

from twoopstracker.authentication.models import User

admin.site.register(
    [
        User,
    ]
)
