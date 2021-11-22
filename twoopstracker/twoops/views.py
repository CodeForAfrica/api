import datetime

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Count
from django.db.models.functions import Trunc
from rest_framework import generics

from twoopstracker.twoops.models import (
    Tweet,
    TweetSearch,
    TwitterAccount,
    TwitterAccountsList,
    UserProfile,
)
from twoopstracker.twoops.serializers import (
    TweetSearchSerializer,
    TweetSerializer,
    TweetsInsightsSerializer,
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

    def get_queryset(self):
        query = self.request.GET.get("query")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        location = self.request.GET.get("location")

        tweets = Tweet.objects.filter(deleted=True)

        if not start_date:
            start_date = str(
                (
                    datetime.date.today()
                    - datetime.timedelta(
                        days=settings.TWOOPSTRACKER_SEARCH_DEFAULT_DAYS_BACK
                    )
                )
            )
        if start_date:
            start_date = datetime.date.fromisoformat(start_date)
        if end_date:
            end_date = datetime.date.fromisoformat(end_date)

        if query:
            if query.startswith("@"):
                # search by username
                tweets = tweets.filter(owner__screen_name__iexact=query[1:])
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

        if start_date:
            tweets = tweets.filter(deleted_at__gte=start_date)
        if end_date:
            tweets = tweets.filter(deleted_at__lte=end_date)
        if location:
            tweets = tweets.filter(owner__location=location)

        return tweets


class TweetsInsightsView(TweetsView):
    pagination_class = None

    def get_serializer(self, *args, **kwargs):
        today = datetime.date.today()
        start_date = datetime.date.fromisoformat(
            self.request.GET.get(
                "start_date",
                str(
                    (
                        today
                        - datetime.timedelta(
                            days=settings.TWOOPSTRACKER_SEARCH_DEFAULT_DAYS_BACK
                        )
                    )
                ),
            )
        )
        end_date = datetime.date.fromisoformat(
            self.request.GET.get("end_date", str(today))
        )

        query_set = (
            self.get_queryset()
            .annotate(start_date=Trunc("deleted_at", "day"))
            .values("start_date")
            .annotate(count=Count("start_date"))
            .order_by("start_date")
        )
        days_counts = [
            {"date": str(query["start_date"].date()), "count": query["count"]}
            for query in query_set
        ]
        for day in range((end_date - start_date).days):
            current_date = str(start_date + datetime.timedelta(days=day))

            if not any(
                [day_count["date"] == current_date for day_count in days_counts]
            ):
                days_counts.append({"date": current_date, "count": 0})

        serializer = TweetsInsightsSerializer(data=days_counts, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer


class TweetSearchesView(generics.ListCreateAPIView):
    serializer_class = TweetSearchSerializer

    def get_queryset(self):
        user_profile = UserProfile.objects.get(user=self.request.user)
        return TweetSearch.objects.filter(owner=user_profile)

    def perform_create(self, serializer):
        user_profile = UserProfile.objects.get(user=self.request.user)
        serializer.save(owner=user_profile)


class TweetSearchView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TweetSearchSerializer

    def get_queryset(self):
        user_profile = UserProfile.objects.get(user=self.request.user)
        return TweetSearch.objects.filter(owner=user_profile)


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
