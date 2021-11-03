from django.db import models
from django.utils.translation import ugettext_lazy as _

from twoopstracker.db.models import TimestampedModelMixin


class Tweet(TimestampedModelMixin):
    """
    Tweet model
    """

    tweet_id = models.BigIntegerField(primary_key=True)
    # https://developer.twitter.com/en/docs/counting-characters
    content = models.CharField(max_length=280, help_text=_("Tweet Content"))
    deleted = models.BooleanField(default=False)
    retweet_id = models.BigIntegerField(null=True)
    retweeted_user_id = models.BigIntegerField(null=True)
    favorite_count = models.IntegerField(default=0)
    retweet_count = models.IntegerField(default=0)
    quote_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    actual_tweet = models.JSONField()
    owner = models.ForeignKey("TwitterAccount", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tweet_id}"

    @property
    def number_of_interactions(self):
        return self.favorite_count + self.retweet_count + self.reply_count


class TwitterAccount(TimestampedModelMixin):
    """
    Twitter Account model
    """

    account_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255, help_text=_("Name of Twitter Account"))
    screen_name = models.CharField(
        max_length=255, help_text=_("Twitter Account Screen Name")
    )
    verified = models.BooleanField(default=False)
    protected = models.BooleanField(default=False)
    location = models.CharField(max_length=255)
    description = models.TextField()
    followers_count = models.IntegerField()
    friends_count = models.IntegerField()
    favourites_count = models.IntegerField()
    statuses_count = models.IntegerField()
    profile_image_url = models.URLField(max_length=255)
    deleted = models.BooleanField(
        default=False,
        help_text=_("When deleted is true, we aren't tracking this account anymore."),
    )

    def __str__(self):
        return self.screen_name
