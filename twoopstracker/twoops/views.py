from datetime import datetime

from django.contrib.postgres.search import SearchQuery, SearchVector
from rest_framework import generics

from twoopstracker.twitterclient import TwitterClient
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


def save_user(account_obj, user):
    account_obj.name = user.name
    account_obj.screen_name = user.screen_name
    account_obj.description = user.description
    account_obj.verified = user.verified
    account_obj.protected = user.protected
    account_obj.location = user.location
    account_obj.followers_count = user.followers_count
    account_obj.friends_count = user.friends_count
    account_obj.favourites_count = user.favourites_count
    account_obj.statuses_count = user.statuses_count
    account_obj.profile_image_url = user.profile_image_url

    account_obj.save()


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

    def post(self, request, *args, **kwargs):
        twitterclient = TwitterClient()

        accounts = []
        failed_accounts = []

        # Since accounts come in as a list of usernames,
        # we need to get the account details and create a TwittwerAccount in our database
        for account in request.data.get("accounts"):
            username = account.get("screen_name")
            # Get account details from twitter
            user = twitterclient.get_user(username)
            if not user:
                failed_accounts.append(username)
                continue
            account_obj, _ = TwitterAccount.objects.get_or_create(account_id=user.id)

            # Move this to a que
            save_user(account_obj, user)

            accounts.append(account_obj.account_id)

        del request.data["accounts"]
        request.data["accounts"] = accounts
        response = self.create(request, *args, **kwargs)

        if failed_accounts:
            response.data["errors"] = {
                "message": "The following accounts couldn't be processed",
                "failed_accounts": failed_accounts,
            }

        return response


class SingleTwitterList(generics.RetrieveUpdateDestroyAPIView):
    queryset = TwitterAccountsList.objects.all()
    serializer_class = TwitterAccountListSerializer

    def put(self, request, *args, **kwargs):
        twitterclient = TwitterClient()
        accounts = []
        failed_accounts = []

        for account in request.data.get("accounts"):
            username = account.get("screen_name")
            user_id = account.get("account_id")
            # Get account details from twitter
            if user_id:
                user = twitterclient.get_user(user_id, key="id")
            else:
                user = twitterclient.get_user(username)

            if not user:
                failed_accounts.append(account)
                continue
            account_obj, _ = TwitterAccount.objects.get_or_create(account_id=user.id)

            # Move this to a que
            save_user(account_obj, user)
            accounts.append(account_obj.account_id)

        del request.data["accounts"]
        request.data["accounts"] = accounts
        response = self.update(request, *args, **kwargs)

        if failed_accounts:
            response.data["errors"] = {
                "message": "The following accounts couldn't be processed",
                "failed_accounts": failed_accounts,
            }
        return response
