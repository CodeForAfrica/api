import datetime

from django.contrib.postgres.search import SearchQuery, SearchVector
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from twoopstracker.twoops.models import Tweet, TwitterAccount, TwitterAccountsList
from twoopstracker.twoops.serializers import (
    TweetSerializer,
    TwitterAccountListSerializer,
)


def get_search_type(search_string):
    search_type = ""

    if search_string.startswith('"') and search_string.endswith('"'):
        return "phrase"
    elif search_string.startswith("(") and search_string.endswith(")"):
        return "websearch"
    elif "," in search_string:
        return "raw"
    else:
        return search_type


def refromat_search_string(search_string):
    return " | ".join(search_string.split(","))


def update_kwargs_with_account_ids(kwargs):
    accounts_ids = []
    accounts = kwargs.get("data", {}).get("accounts", [])
    for account in accounts:
        account, _ = TwitterAccount.objects.get_or_create(
            screen_name=account.get("screen_name")
        )
        accounts_ids.append(account.account_id)

    if accounts:
        kwargs["data"]["accounts"] = accounts_ids

    return kwargs


class TweetsView(generics.ListAPIView):
    serializer_class = TweetSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        query = self.request.GET.get("query")
        startDate = self.request.GET.get("startDate")
        endDate = self.request.GET.get("endDate")
        location = self.request.GET.get("location")

        tweets = Tweet.objects.filter(deleted=True)

        if not startDate:
            startDate = str(datetime.datetime.now() - datetime.timedelta(days=7))
        if startDate:
            startDate = datetime.datetime.fromisoformat(startDate)
        if endDate:
            endDate = datetime.datetime.fromisoformat(endDate)

        if query:
            if query.startswith("@"):
                # search by username
                tweets = tweets.filter(owner__screen_name=query[1:])
            else:
                search_type = get_search_type(query)
                if search_type == "raw":
                    query = refromat_search_string(query)
                vector = SearchVector("content", "actual_tweet")
                if search_type:
                    search_query = SearchQuery(query, search_type=search_type)
                else:
                    search_query = SearchQuery(query)
                tweets = tweets.annotate(search=vector).filter(search=search_query)

        if startDate:
            tweets = tweets.filter(deleted_at__gte=startDate)
        if endDate:
            tweets = tweets.filter(deleted_at__lte=endDate)
        if location:
            tweets = tweets.filter(owner__location=location)

        return tweets


class AccountsList(generics.ListCreateAPIView):
    queryset = TwitterAccountsList.objects.all()
    serializer_class = TwitterAccountListSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs = update_kwargs_with_account_ids(kwargs)

        return serializer_class(*args, **kwargs)


class SingleTwitterList(generics.RetrieveUpdateDestroyAPIView):
    queryset = TwitterAccountsList.objects.all()
    serializer_class = TwitterAccountListSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs = update_kwargs_with_account_ids(kwargs)

        return serializer_class(*args, **kwargs)
