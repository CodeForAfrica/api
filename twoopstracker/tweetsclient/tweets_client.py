import json
import logging

import tweepy
from django.conf import settings

from twoopstracker.twoops.models import Tweet, TwitterAccount

logger = logging.getLogger(__name__)


class TweetListener(tweepy.Stream):
    def get_accounts(self):
        accounts = []
        with open("accounts.txt", "r") as f:
            for line in f:
                accounts.append(line.strip())
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
            # Delete the tweet
            tweet = Tweet.objects.get(
                tweet_id=tweet.get("delete").get("status").get("id")
            )
            if tweet:
                tweet.deleted = True
                tweet.save()
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

            tweet = Tweet(
                tweet_id=tweet.get("id"),
                content=tweet_text,
                retweet_id=tweet.get("retweeted_status", {}).get("id"),
                retweeted_user_id=tweet.get("retweeted_status", {})
                .get("user", {})
                .get("id"),
                favorite_count=tweet.get("favorite_count"),
                retweet_count=tweet.get("retweet_count"),
                reply_count=tweet.get("reply_count"),
                quote_count=tweet.get("quote_count"),
                actual_tweet=tweet,
                owner=TwitterAccount.objects.get(
                    account_id=tweet.get("user").get("id")
                ),
            )
            tweet.save()
        return True

    def on_error(self, status_code):
        logger.error(
            f"Stream listener encountered an error with status code {status_code}"
        )

    def on_timeout(self):
        logger.error("Stream listener timed out.")


class TweetStreamClient:
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


if __name__ == "__main__":
    client = TweetStreamClient()
    client.run()
