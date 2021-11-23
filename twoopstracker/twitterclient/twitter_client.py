import logging

import tweepy
from django.conf import settings

logger = logging.getLogger(__name__)


class TwitterClient:
    def __init__(self):
        self.auth = tweepy.OAuthHandler(
            settings.TWOOPSTRACKER_CONSUMER_KEY, settings.TWOOPSTRACKER_CONSUMER_SECRET
        )
        self.auth.set_access_token(
            settings.TWOOPSTRACKER_ACCESS_TOKEN,
            settings.TWOOPSTRACKER_ACCESS_TOKEN_SECRET,
        )
        self.api = tweepy.API(self.auth)

        try:
            username = self.api.verify_credentials().screen_name
            logger.info("@" + username + " is authenticated")
        except tweepy.errors.TweepyException as e:
            logger.error(e)

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
