import datetime

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Count
from django.db.models.functions import Trunc
from rest_framework import generics

from twoopstracker.twitterclient.twitter_client import TwitterClient
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

twitterclient = TwitterClient()


def save_accounts(users):
    accounts_ids = []

    accounts_ids = []
    twitter_accounts = []
    for user in users:
        twitter_account, _ = TwitterAccount.objects.get_or_create(account_id=user.id)
        twitter_account.name = user.name
        twitter_account.screen_name = user.screen_name
        twitter_account.description = user.description
        twitter_account.verified = user.verified
        twitter_account.protected = user.protected
        twitter_account.location = user.location
        twitter_account.followers_count = user.followers_count
        twitter_account.friends_count = user.friends_count
        twitter_account.favourites_count = user.favourites_count
        twitter_account.statuses_count = user.statuses_count
        twitter_account.profile_image_url = user.profile_image_url
        twitter_accounts.append(twitter_account)
        accounts_ids.append(user.id)

    TwitterAccount.objects.bulk_update(
        twitter_accounts,
        [
            "name",
            "screen_name",
            "description",
            "verified",
            "protected",
            "location",
            "followers_count",
            "friends_count",
            "favourites_count",
            "statuses_count",
            "profile_image_url",
        ],
    )

    return accounts_ids


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
    accounts = kwargs.get("data", {}).get("accounts", [])

    screen_names = [acc.get("screen_name") for acc in accounts if "screen_name" in acc]
    twitter_accounts = []
    if screen_names:
        twitter_accounts = twitterclient.get_users(screen_names)

    if accounts and twitter_accounts:
        kwargs["data"]["accounts"] = save_accounts(twitter_accounts)

    return kwargs


class TweetsView(generics.ListAPIView):
    serializer_class = TweetSerializer

    def get_queryset(self):
        query = self.request.GET.get("query")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        location = self.request.GET.get("location")

        twitter_accounts_lists = TwitterAccountsList.objects.filter(is_private=False)
        twitter_accounts = set()
        user = self.request.user

        if user.is_authenticated:
            user_profile = UserProfile.objects.get(user=user)
            twitter_accounts_lists = twitter_accounts_lists.union(
                TwitterAccountsList.objects.filter(owner=user_profile)
            )

        for twitter_accounts_list in twitter_accounts_lists:
            for twitter_account in twitter_accounts_list.accounts.all().values_list(
                "account_id", flat=True
            ):
                twitter_accounts.add(twitter_account)

        tweets = Tweet.objects.filter(
            deleted=True, owner__account_id__in=twitter_accounts
        )

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

        return tweets.order_by("-deleted_at")


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

        insights = {
            str(query["start_date"].date()): query["count"] for query in query_set
        }
        for day in range((end_date - start_date).days):
            current_date = str(start_date + datetime.timedelta(days=day))
            insights.setdefault(current_date, 0)

        # we can now return it in the expected [{'date': xxx, 'count': xxx}, ...] structure
        data = [{"date": i, "count": insights[i]} for i in sorted(insights)]

        serializer = TweetsInsightsSerializer(data=data, many=True)
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

    def perform_create(self, serializer):
        user_profile = UserProfile.objects.get(user=self.request.user)
        serializer.save(owner=user_profile)


class SingleTwitterList(generics.RetrieveUpdateDestroyAPIView):
    queryset = TwitterAccountsList.objects.all()
    serializer_class = TwitterAccountListSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs = update_kwargs_with_account_ids(kwargs)

        return serializer_class(*args, **kwargs)
