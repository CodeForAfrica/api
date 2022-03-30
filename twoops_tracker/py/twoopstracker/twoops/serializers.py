from django.db import IntegrityError
from rest_framework import serializers
from twoopstracker.twoops.models import (
    Category,
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
    original_retweet_link = serializers.SerializerMethodField()

    def get_number_of_interactions(self, obj):
        return obj.number_of_interactions

    def get_original_retweet_link(self, obj):
        if obj.retweet_id:
            return f"https://twitter.com/{obj.retweeted_user_screen_name}/status/{obj.retweet_id}"

    class Meta:
        model = Tweet
        fields = [
            "tweet_id",
            "retweet_id",
            "retweeted_user_screen_name",
            "original_retweet_link",
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
                    "profile_image_url": account.profile_image_url,
                    "profile_image_url_https": account.profile_image_url_https,
                    "evidences": evidences,
                }
            )

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if hasattr(request, "GET") and request.GET.get("download"):
            data["accounts"] = self.get_accounts(instance)
        else:
            data.pop("accounts", None)
        return data


class TwitterAccountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccount
        fields = [
            "name",
            "account_id",
            "screen_name",
            "protected",
            "profile_image_url",
            "profile_image_url_https",
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


class TwitterAccountCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class AccountsListUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    class Meta:
        fields = ("file",)
