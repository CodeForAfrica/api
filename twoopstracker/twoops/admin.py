from django.contrib import admin

from twoopstracker.twoops.models import Tweet, TwitterAccount

admin.site.register(
    [
        Tweet,
        TwitterAccount,
    ]
)
