from rest_framework import generics

from twoopstracker.twoops.models import Tweet
from twoopstracker.twoops.serializers import TweetSerializer


class TweetsView(generics.ListAPIView):
    serializer_class = TweetSerializer
    queryset = Tweet.objects.all()
