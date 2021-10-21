from rest_framework import generics

from twoopstracker.twitter.models import Tweet
from twoopstracker.twitter.serializers import TweetSerializer


class TweetsView(generics.ListAPIView):
    serializer_class = TweetSerializer
    queryset = Tweet.objects.all()
