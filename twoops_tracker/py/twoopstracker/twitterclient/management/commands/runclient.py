from django.core.management.base import BaseCommand
from twoopstracker.twitterclient.twitter_client import TwitterClient


class Command(BaseCommand):
    help = "Management command that Starts tweets stream client"

    def handle(self, *args, **options):
        client = TwitterClient()
        client.run()
