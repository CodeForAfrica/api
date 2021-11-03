from django.core.management.base import BaseCommand

from twoopstracker.tweetsclient.tweets_client import TweetStreamClient


class Command(BaseCommand):
    help = "Management command that Starts tweets stream client"

    def handle(self, *args, **options):
        client = TweetStreamClient()
        client.run()
