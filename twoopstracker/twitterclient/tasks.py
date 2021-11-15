from celery import shared_task
from django.utils import timezone

from twoopstracker.twoops.models import Tweet, TwitterAccount


@shared_task
def save_tweet(tweet_data):
    tweet = Tweet(
        tweet_id=tweet_data.get("id"),
        content=tweet_data.get("tweet_text"),
        retweet_id=tweet_data.get("retweeted_status", {}).get("id"),
        retweeted_user_id=tweet_data.get("retweeted_status", {})
        .get("user", {})
        .get("id"),
        favorite_count=tweet_data.get("favorite_count"),
        retweet_count=tweet_data.get("retweet_count"),
        reply_count=tweet_data.get("reply_count"),
        quote_count=tweet_data.get("quote_count"),
        actual_tweet=tweet_data,
        owner=TwitterAccount.objects.get(account_id=tweet_data.get("user").get("id")),
    )
    tweet.save()


@shared_task
def mark_tweet_as_deleted(tweet_id):
    tweet = Tweet.objects.filter(tweet_id=tweet_id).first()
    if tweet:
        tweet.deleted = True
        tweet.deleted_at = timezone.now()
        tweet.save()
