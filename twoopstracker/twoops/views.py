from datetime import datetime

from django.contrib.postgres.search import SearchQuery, SearchVector
from rest_framework import generics

from twoopstracker.twoops.models import Tweet, TwitterAccountsList
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


class TweetsView(generics.ListAPIView):
    serializer_class = TweetSerializer

    def get_queryset(self):
        query = self.request.GET.get("query")
        startDate = self.request.GET.get("startDate")
        endDate = self.request.GET.get("endDate")
        location = self.request.GET.get("location")

        if startDate:
            startDate = datetime.fromisoformat(startDate)
        if endDate:
            endDate = datetime.fromisoformat(endDate)

        if query:
            search_type = get_search_type(query)
            if search_type == "raw":
                query = refromat_search_string(query)
            vector = SearchVector("content", "actual_tweet")
            if search_type:
                search_query = SearchQuery(query, search_type=search_type)
            else:
                search_query = SearchQuery(query)
            tweets = Tweet.objects.annotate(search=vector).filter(search=search_query)
        else:
            tweets = Tweet.objects.all()

        if startDate:
            tweets = tweets.filter(created_at__gte=startDate)
        if endDate:
            tweets = tweets.filter(created_at__lte=endDate)
        if location:
            tweets = tweets.filter(owner__location=location)
        return tweets


class AccountsList(generics.ListCreateAPIView):
    queryset = TwitterAccountsList.objects.all()
    serializer_class = TwitterAccountListSerializer


class SingleTwitterList(generics.RetrieveUpdateDestroyAPIView):
    queryset = TwitterAccountsList.objects.all()
    serializer_class = TwitterAccountListSerializer
