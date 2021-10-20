from django.contrib import admin

from twoopstracker.twitter.models import Tweet, TwitterAccount

admin.site.register(
    [
        Tweet,
        TwitterAccount,
    ]
)
