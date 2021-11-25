from django.contrib import admin

from twoopstracker.twoops.models import (
    Tweet,
    TweetSearch,
    TwitterAccount,
    TwitterAccountsLists,
    UserProfile,
)

admin.site.register(
    [
        Tweet,
        TweetSearch,
        TwitterAccount,
        UserProfile,
        TwitterAccountsLists,
    ]
)
