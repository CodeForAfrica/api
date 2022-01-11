from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from twoopstracker.db.models import TimestampedModelMixin


class Tweet(TimestampedModelMixin):
    """
    Tweet model
    """

    tweet_id = models.BigIntegerField(primary_key=True)
    content = models.CharField(max_length=1024, help_text=_("Tweet Content"))
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    retweet_id = models.BigIntegerField(blank=True, null=True)
    retweeted_user_id = models.BigIntegerField(blank=True, null=True)
    retweeted_user_screen_name = models.CharField(
        max_length=255,
        help_text=_("Twitter Account Screen Name"),
        blank=True,
        null=True,
    )
    favorite_count = models.IntegerField(default=0)
    retweet_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)
    actual_tweet = models.JSONField()
    owner = models.ForeignKey("TwitterAccount", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tweet_id}"

    @property
    def number_of_interactions(self):
        return self.favorite_count + self.retweet_count + self.reply_count


class TweetSearch(TimestampedModelMixin):
    """
    TweetSearch model
    """

    query = models.JSONField(help_text=_("Search Query"))
    name = models.CharField(
        help_text=_("The name of the Search Query"),
        null=True,
        blank=True,
        max_length=255,
    )
    owner = models.ForeignKey(
        "UserProfile", on_delete=models.CASCADE, related_name="tweet_searches"
    )

    def __str__(self):
        return f"{self.query}"

    class Meta:
        unique_together = ("query", "owner")
        verbose_name_plural = _("Tweet Searches")


class TwitterAccount(TimestampedModelMixin):
    """
    Twitter Account model
    """

    account_id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=255, help_text=_("Name of Twitter Account"), null=True, blank=True
    )
    screen_name = models.CharField(
        max_length=255,
        help_text=_("Twitter Account Screen Name"),
    )
    verified = models.BooleanField(default=False)
    protected = models.BooleanField(default=False)
    location = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    followers_count = models.IntegerField(default=0)
    friends_count = models.IntegerField(default=0)
    favourites_count = models.IntegerField(default=0)
    statuses_count = models.IntegerField(default=0)
    profile_image_url = models.URLField(max_length=255, null=True, blank=True)
    deleted = models.BooleanField(
        default=False,
        help_text=_("When deleted is true, we aren't tracking this account anymore."),
    )
    categories = models.ManyToManyField(
        "Category", related_name="twitter_accounts", blank=True
    )

    def __str__(self):
        return self.screen_name


class Category(TimestampedModelMixin):
    """
    Twitter Account Category model
    """

    name = models.CharField(max_length=255, unique=True, help_text=_("Category Name"))

    class Meta:
        verbose_name_plural = _("Categories")

    def __str__(self):
        return f"{self.name}"


class Evidence(TimestampedModelMixin):
    """
    Evidence model
    """

    account = models.ForeignKey(
        "TwitterAccount", on_delete=models.CASCADE, related_name="evidence"
    )
    url = models.URLField(
        help_text=_(
            "URL to evidence showing that this account can belong to a public list"
        ),
    )

    def __str__(self):
        return f"{self.url}"


class UserProfile(TimestampedModelMixin):
    """
    User Profile model
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )

    def __str__(self):
        return self.user.email


class TwitterAccountsList(TimestampedModelMixin):
    """
    List model
    """

    name = models.CharField(max_length=255, help_text=_("Name of Twitter List"))
    slug = models.CharField(max_length=255, help_text=_("Twitter List Slug"))
    owner = models.ForeignKey("UserProfile", on_delete=models.CASCADE)
    accounts = models.ManyToManyField("TwitterAccount", related_name="lists")
    is_private = models.BooleanField(default=True)

    class Meta:
        unique_together = ("name", "owner")

    def __str__(self):
        return self.name


class Team(TimestampedModelMixin):
    name = models.CharField(max_length=255, help_text=_("Name of Team"))
    owner = models.ForeignKey(
        "UserProfile", on_delete=models.CASCADE, help_text="Owner of the group"
    )
    twitter_accounts_lists = models.ManyToManyField(
        "TwitterAccountsList", related_name="teams"
    )
    members = models.ManyToManyField("UserProfile", related_name="teams")

    class Meta:
        unique_together = ("name", "owner")

    def __str__(self):
        return self.name
