from django.contrib import admin

from twoopstracker.twoops.models import (
    Tweet,
    TwitterAccount,
    TwitterAccountsList,
    UserProfile,
)

admin.site.register(
    [
        Tweet,
        TwitterAccount,
        UserProfile,
        TwitterAccountsList,
    ]
)
