import json
import logging

import tweepy
from django.conf import settings

from twoopstracker.twoops.models import TwitterAccount

from .tasks import mark_tweet_as_deleted, save_tweet

logger = logging.getLogger(__name__)


class TweetListener(tweepy.Stream):
    def get_accounts(self):
        accounts = TwitterAccount.objects.filter(deleted=False).values_list(
            "account_id"
        )
        return accounts

    def on_connect(self):
        logger.info("Stream listener connected.")
        return True

    def on_connection_error(self):
        logger.error("Stream listener encountered a connection error.")
        return True

    def on_data(self, data):
        logger.info("Tweet data received.")
        tweet = json.loads(data)
        if "delete" in tweet:
            logger.info(
                f'Queued delete notification for user {tweet.get("delete").get("status").get("user_id")} \
                    for tweet {tweet.get("delete").get("status").get("id")}'
            )
            # Mark the tweet as Deleted
            mark_tweet_as_deleted.delay(tweet.get("delete").get("status").get("id"))
        else:
            # Create the tweet in to our database
            tweet_text = tweet.get("extended_tweet", {}).get(
                "full_text", tweet.get("text")
            )
            if tweet.get("retweeted_status"):
                tweet_text = (
                    tweet.get("retweeted_status")
                    .get("extended_tweet", {})
                    .get("full_text", tweet.get("text"))
                )

            tweet["tweet_text"] = tweet_text
            save_tweet.delay(tweet)
        return True

    def on_error(self, status_code):
        logger.error(
            f"Stream listener encountered an error with status code {status_code}"
        )

    def on_timeout(self):
        logger.error("Stream listener timed out.")


class TwitterClient:
    def __init__(self):
        self.consumer_key = settings.TWOOPSTRACKER_CONSUMER_KEY
        self.consumer_secret = settings.TWOOPSTRACKER_CONSUMER_SECRET
        self.access_token = settings.TWOOPSTRACKER_ACCESS_TOKEN
        self.access_token_secret = settings.TWOOPSTRACKER_ACCESS_TOKEN_SECRET

        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        api = tweepy.API(auth)
        try:
            username = api.verify_credentials().screen_name
            logger.info("@" + username + " is authenticated")
        except tweepy.errors.TweepyException:
            logger.error("Invalid credentials")

    def stream_forever(self):
        stream = TweetListener(
            self.consumer_key,
            self.consumer_secret,
            self.access_token,
            self.access_token_secret,
        )
        stream.filter(follow=stream.get_accounts())

    def run(self):
        self.stream_forever()
