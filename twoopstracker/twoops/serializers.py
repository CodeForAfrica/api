from django.db import IntegrityError
from rest_framework import serializers

from twoopstracker.twoops.models import (
    Evidence,
    Tweet,
    TweetSearch,
    TwitterAccount,
    TwitterAccountsList,
)


class TwitterAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccount
        fields = "__all__"


class TweetSerializer(serializers.ModelSerializer):
    def get_number_of_interactions(self, obj):
        return obj.number_of_interactions

    class Meta:
        model = Tweet
        fields = [
            "tweet_id",
            "retweet_id",
            "retweeted_user_screen_name",
            "created_at",
            "content",
            "number_of_interactions",
            "favorite_count",
            "retweet_count",
            "deleted",
            "deleted_at",
            "owner",
        ]
        depth = 1


class TweetsInsightsSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ["url"]


class TwitterAccountsListsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccountsList
        fields = ["id", "name", "created_at", "is_private", "accounts"]
        extra_kwargs = {
            "accounts": {"write_only": True},
        }


class TwitterAccountsListSerializer(TwitterAccountsListsSerializer):
    class Meta(TwitterAccountsListsSerializer.Meta):
        extra_kwargs = {
            "accounts": {"write_only": False},
        }

    def get_accounts(self, obj):
        accounts = obj.accounts.all()
        data = []
        for account in accounts:
            evidences = EvidenceSerializer(account.evidence, many=True).data
            data.append(
                {
                    "name": account.name,
                    "account_id": account.account_id,
                    "screen_name": account.screen_name,
                    "protected": account.protected,
                    "created_at": account.created_at,
                    "updated_at": account.updated_at,
                    "evidences": evidences,
                }
            )

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["accounts"] = self.get_accounts(instance)
        return data


class TwitterAccountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccount
        fields = [
            "name",
            "account_id",
            "screen_name",
            "protected",
            "created_at",
            "updated_at",
        ]


class TweetSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = TweetSearch
        fields = ["id", "created_at", "updated_at", "owner", "name", "query"]
        read_only_fields = ["id", "created_at", "updated_at", "owner"]

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            raise serializers.ValidationError(e)


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    class Meta:
        fields = ("file",)
