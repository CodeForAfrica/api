from django.contrib import admin

from twoopstracker.twoops.models import (
    Tweet,
    TweetSearch,
    TwitterAccount,
    TwitterAccountsList,
    UserProfile,
)

admin.site.register(
    [
        Tweet,
        TweetSearch,
        TwitterAccount,
        UserProfile,
        TwitterAccountsList,
    ]
)
