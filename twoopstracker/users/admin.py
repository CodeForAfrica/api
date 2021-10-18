from django.contrib import admin

from twoopstracker.users.models import User

admin.site.register(
    [
        User,
    ]
)
