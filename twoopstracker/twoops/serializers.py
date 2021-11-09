from rest_framework import serializers

from twoopstracker.twoops.models import Tweet, TwitterAccount, TwitterAccountsList


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
            "likes_count",
            "retweets_count",
            "replies_count",
            "deleted",
            "deleted_at",
            "owner",
        ]
        depth = 1


class TwitterAccountListSerializer(serializers.ModelSerializer):
    def get_accounts(self, obj):
        accounts = obj.accounts.all()
        data = []
        for account in accounts:
            data.append(
                {
                    "name": account.name,
                    "account_id": account.account_id,
                    "screen_name": account.screen_name,
                }
            )

        return data

    class Meta:
        model = TwitterAccountsList
        fields = ["id", "name", "created_at", "owner", "is_private", "accounts"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["accounts"] = self.get_accounts(instance)
        return data
