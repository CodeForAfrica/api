from rest_framework import serializers

from twoopstracker.twitter.models import Tweet, TwitterAccount


class TwitterAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccount
        fields = "__all__"


class TweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tweet
        fields = "__all__"
        depth = 1
