import logging

import tweepy
from django.conf import settings

from twoopstracker.twoops.models import TwitterAccount

from .tasks import mark_tweet_as_deleted, save_tweet

logger = logging.getLogger(__name__)


class TweetListener(tweepy.Stream):
    def get_accounts(self):
        accounts = TwitterAccount.objects.filter(deleted=False).values_list(
            "account_id", flat=True
        )
        return list(accounts)[:5000]

    def on_connect(self):
        logger.info("Stream listener connected.")
        return True

    def on_connection_error(self):
        logger.error("Stream listener encountered a connection error.")
        return True

    def on_status(self, tweet):
        # Create the tweet in to our database
        tweet = tweet._json
        tweet_text = tweet.get("extended_tweet", {}).get("full_text", tweet.get("text"))
        if tweet.get("retweeted_status"):
            tweet_text = (
                tweet.get("retweeted_status")
                .get("extended_tweet", {})
                .get("full_text", tweet.get("text"))
            )

        tweet["tweet_text"] = tweet_text
        save_tweet.delay(tweet)

    def on_delete(self, status_id, user_id):
        logger.info(
            f"Queued delete notification for user {user_id} \
                for tweet {status_id}"
        )
        # Mark the tweet as Deleted
        mark_tweet_as_deleted.delay(status_id)

    def on_data(self, data):
        super().on_data(data)

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
        if hasattr(self, "stream"):
            logger.info("Disconnecting existing stream listener.")
            self.stream.disconnect()
            return
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        self.api = tweepy.API(auth)
        try:
            username = self.api.verify_credentials().screen_name
            logger.info("@" + username + " is authenticated")
        except tweepy.errors.TweepyException:
            logger.error("Invalid credentials")

    def get_user(self, user, key="screen_name"):
        try:
            if key == "screen_name":
                return self.api.get_user(screen_name=user)
            elif key == "id":
                return self.api.get_user(user_id=user)
        except tweepy.errors.TweepyException as e:
            logger.error(e)
            return None

    def get_users(self, screen_names):
        return self.api.lookup_users(screen_name=screen_names)

    def run(self):
        self.stream = TweetListener(
            self.consumer_key,
            self.consumer_secret,
            self.access_token,
            self.access_token_secret,
        )
        self.stream.filter(follow=self.stream.get_accounts(), threaded=True)

    def disconnect(self):
        self.stream.disconnect()
