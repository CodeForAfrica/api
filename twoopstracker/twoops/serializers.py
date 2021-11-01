from rest_framework import serializers

from twoopstracker.twoops.models import Tweet, TwitterAccount, TwitterAccountsList


class TwitterAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccount
        fields = "__all__"


class TweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tweet
        fields = "__all__"
        depth = 1


class TwitterAccountListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccountsList
        fields = "__all__"
