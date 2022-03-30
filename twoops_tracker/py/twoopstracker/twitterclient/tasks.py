import logging

from celery import shared_task
from django.utils import timezone
from twoopstracker.twoops.models import Tweet, TwitterAccount

logger = logging.getLogger(__name__)


@shared_task
def save_tweet(tweet_data):
    owner = TwitterAccount.objects.filter(
        account_id=tweet_data.get("user").get("id")
    ).first()
    if owner:
        tweet = Tweet(
            tweet_id=tweet_data.get("id"),
            content=tweet_data.get("tweet_text"),
            retweet_id=tweet_data.get("retweeted_status", {}).get("id"),
            retweeted_user_screen_name=tweet_data.get("retweeted_status", {})
            .get("user", {})
            .get("screen_name"),
            retweeted_user_id=tweet_data.get("retweeted_status", {})
            .get("user", {})
            .get("id"),
            favorite_count=tweet_data.get("favorite_count"),
            retweet_count=tweet_data.get("retweet_count"),
            reply_count=tweet_data.get("reply_count"),
            quote_count=tweet_data.get("quote_count"),
            actual_tweet=tweet_data,
            owner=owner,
        )
        tweet.save()
        logger.info(f"Tweet {tweet.tweet_id} saved")
    else:
        logger.warning(
            f"Received a tweet {tweet_data.get('tweet_text')} for an \
                account({ tweet_data.get('user').get('screen_name') }) we aren't tracking. "
        )


@shared_task
def mark_tweet_as_deleted(tweet_id):
    Tweet.objects.filter(tweet_id=tweet_id).update(
        deleted=True, deleted_at=timezone.now()
    )
