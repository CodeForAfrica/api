from django.contrib import admin

from twoopstracker.twoops.models import (
    AccountGroup,
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
        AccountGroup,
        Category,
    ]
)
