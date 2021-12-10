from django.contrib import admin

from twoopstracker.twoops.models import (
    Category,
    Evidence,
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
        Evidence,
        UserProfile,
        TwitterAccountsList,
        Category,
    ]
)
