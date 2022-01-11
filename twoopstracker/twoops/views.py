import csv
import datetime
import io
import json
from collections import defaultdict

import tablib
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Count, Q
from django.db.models.functions import Lower, Trunc
from django.db.utils import IntegrityError
from django.http import HttpResponse
from rest_framework import filters, generics, response, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from twoopstracker.twitterclient.twitter_client import TwitterClient
from twoopstracker.twoops.models import (
    Category,
    Evidence,
    Tweet,
    TweetSearch,
    TwitterAccount,
    TwitterAccountsList,
)
from twoopstracker.twoops.permissions import IsOwner
from twoopstracker.twoops.serializers import (
    AccountsListUploadSerializer,
    TweetSearchSerializer,
    TweetSerializer,
    TweetsInsightsSerializer,
    TwitterAccountCategoriesSerializer,
    TwitterAccountsListSerializer,
    TwitterAccountsListsSerializer,
    TwitterAccountsSerializer,
)

twitterclient = TwitterClient()


def save_accounts(users, evidence_links={}, categories={}):
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
        category = categories.get(user.screen_name)
        category = Category.objects.filter(name__iexact=category).first()
        if category:
            category.twitter_accounts.add(twitter_account)
        twitter_accounts.append(twitter_account)
        accounts_ids.append(user.id)
        evidence_link = evidence_links.get(user.screen_name)
        if evidence_link:
            Evidence.objects.get_or_create(account=twitter_account, url=evidence_link)

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
    # TODO(esirk) : Add more search types
    # search_type = ""

    # if search_string.startswith('"') and search_string.endswith('"'):
    #     return "phrase"
    # elif search_string.startswith("(") and search_string.endswith(")"):
    #     return "websearch"
    # else:
    #     return search_type
    return "websearch"


def refromat_search_string(search_string):
    return " | ".join(search_string.split(","))


def get_twitter_accounts(screen_names):
    twitter_accounts = []
    if screen_names:
        # Twitter API Returns fully-hydrated user objects for up to 100 users per request
        screen_names_batch = [
            screen_names[i : i + 100] for i in range(0, len(screen_names), 100)
        ]
        for screen_names in screen_names_batch:
            twitter_accounts.extend(twitterclient.get_users(screen_names))

    return twitter_accounts


def update_kwargs_with_account_ids(kwargs):
    accounts = kwargs.get("data", {}).get("accounts", [])

    screen_names = [acc.get("screen_name") for acc in accounts if "screen_name" in acc]
    twitter_accounts = get_twitter_accounts(screen_names)

    if accounts and twitter_accounts:
        kwargs["data"]["accounts"] = save_accounts(twitter_accounts)

    return kwargs


def process_file_data(data):
    result = []
    for row in data:
        accounts = row.get("accounts", [])
        # For tweets, we need to convert the OrderedDict to a json
        if row.get("owner"):
            username = row["owner"]["screen_name"]
            row[
                "original_tweet"
            ] = f"https://twitter.com/{username}/status/{row['tweet_id']}"
            row["username"] = username
            row["owner"] = json.dumps(row["owner"])
            result.append(row)

        elif accounts:
            # Convert to the UPLOAD csv format
            repository = "Private" if row.get("is_private") else "Public"
            row = {"list_name": row["name"]}

            for acc in accounts:
                row["username"] = acc.get("screen_name")
                row["repository"] = repository
                row["evidence"] = "\n".join(
                    list(
                        acc.get("evidence")
                        .all()
                        .values_list("url", flat=True)
                        .distinct()
                        if acc.get("evidence")
                        else ""
                    )
                )
                result.append(row)
    return result


def generate_file(data, filename, fieldnames, fileformat):
    content_type = ""

    if fileformat == "csv":
        content_type = "text/csv"
    else:
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    response = HttpResponse(content_type=content_type)
    response["Content-Disposition"] = f"attachment; filename={filename}.{fileformat}"

    file_data = process_file_data(data)
    list_val = []
    # Order rows as per column order
    for row in file_data:
        ordered_row = [row[k] for k in fieldnames]
        list_val.append(ordered_row)

    table = tablib.Dataset(*list_val, headers=fieldnames)
    response.write(table.export(fileformat))

    return response


class TweetsView(generics.ListAPIView):
    serializer_class = TweetSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ["owner__screen_name", "deleted_at", "created_at"]
    ordering = ["-deleted_at"]

    def get(self, request, *args, **kwargs):
        download = request.GET.get("download", "").lower()
        if download in ["csv", "xlsx"]:
            serializer = self.get_serializer(self.get_queryset(), many=True)
            data = serializer.data
            fieldnames = (
                [
                    "original_tweet",
                    "username",
                ]
                + list(data[0].keys())
                if len(data) > 0
                else []
            )
            return generate_file(data, "tweets", fieldnames, download)
        elif download:
            content = {"message": f"{download} not supported"}
            status_code = status.HTTP_400_BAD_REQUEST

            return Response(content, status=status_code)

        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        query = self.request.GET.get("query")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        location = self.request.GET.get("location")
        category = self.request.GET.get("category")

        twitter_accounts_lists = TwitterAccountsList.objects.filter(is_private=False)
        twitter_accounts = set()
        user = self.request.user

        if user.is_authenticated:
            twitter_accounts_lists = TwitterAccountsList.objects.filter(
                Q(is_private=False)
                | Q(owner=user.userprofile)
                | Q(teams__members__user_id=user.userprofile.user_id)
            ).distinct()

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
        if category:
            tweets = tweets.filter(owner__category__name=category)

        if query:
            if query.startswith("@"):
                # search by username
                tweets = tweets.filter(owner__screen_name__iexact=query[1:])
            else:
                search_type = get_search_type(query)
                vector = SearchVector("content", "owner__screen_name", "owner__name")
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
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return TweetSearch.objects.filter(owner=self.request.user.userprofile)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user.userprofile)


class TweetSearchView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TweetSearchSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return TweetSearch.objects.filter(owner=self.request.user.userprofile)


class AccountsLists(generics.ListCreateAPIView):
    serializer_class = TwitterAccountsListsSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        download = request.GET.get("download", "").lower()
        if download in ["csv", "xlsx"]:
            serializer = TwitterAccountsListSerializer(self.get_queryset(), many=True)
            fieldnames = ["list_name", "username", "repository", "evidence"]

            return generate_file(
                serializer.data, "accounts_lists", fieldnames, download
            )
        elif download:
            content = {"message": f"{download} not supported"}
            status_code = status.HTTP_400_BAD_REQUEST

            return Response(content, status=status_code)

        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        return TwitterAccountsList.objects.filter(owner=self.request.user.userprofile)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs = update_kwargs_with_account_ids(kwargs)

        return serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user.userprofile)


class AccountsList(generics.RetrieveUpdateDestroyAPIView):
    queryset = TwitterAccountsList.objects.all()
    serializer_class = TwitterAccountsListSerializer
    permission_classes = [
        IsOwner,
    ]

    def get(self, request, *args, **kwargs):
        download = request.GET.get("download", "").lower()
        if download in ["csv", "xlsx"]:
            serializer = self.get_serializer(self.get_object())
            fieldnames = ["list_name", "username", "repository", "evidence"]

            return generate_file(
                [serializer.data], "accounts_lists", fieldnames, download
            )

        elif download:
            content = {"message": f"{download} not supported"}
            status_code = status.HTTP_400_BAD_REQUEST

            return Response(content, status=status_code)

        return self.retrieve(request, *args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs = update_kwargs_with_account_ids(kwargs)

        return serializer_class(*args, **kwargs)


class TwitterAccountsView(generics.ListAPIView):
    serializer_class = TwitterAccountsSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return TwitterAccount.objects.filter(
            lists__owner=self.request.user.userprofile
        ).distinct()


class TwitterAccountCategoriesView(generics.ListAPIView):
    serializer_class = TwitterAccountCategoriesSerializer
    queryset = Category.objects.all()


class AccountsListUploadAPIView(generics.CreateAPIView):
    serializer_class = AccountsListUploadSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data["file"]

        decoded_file = file.read().decode()
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        account_lists = defaultdict(list)

        errors = []
        total_accounts = 0
        all_categories = Category.objects.values_list(
            Lower("name"), flat=True
        ).distinct()
        for position, row in enumerate(reader, 1):
            total_accounts += 1
            repository = row.get("repository", "Private")
            is_private = True if repository == "Private" else False
            evidence = row.get("evidence", "")
            category = row.get("category", "")
            if category and category.lower() not in all_categories:
                errors.append(
                    {
                        "message": f"The category '{category}' isn't currently supported",
                        "details": {
                            "row": position,
                            "username": row["username"],
                            "category": category,
                        },
                    }
                )
            elif is_private or (not is_private and evidence):
                account_lists[row["list_name"]].append(
                    {
                        "username": row["username"],
                        "is_private": is_private,
                        "evidence": evidence,
                        "repo": repository,
                        "category": category,
                    }
                )
            else:
                errors.append(
                    {
                        "message": "Missing evidence for public account",
                        "details": {
                            "list_name": row["list_name"],
                            "username": row["username"],
                            "evidence": evidence,
                            "row": position,
                        },
                    }
                )

        for account_list in account_lists:
            twitter_accounts_lists = set()
            screen_names = []
            evidence_links = {}
            categories = {}
            for account in account_lists[account_list]:
                try:
                    twitter_accounts_lists.add(
                        TwitterAccountsList.objects.get_or_create(
                            name=account_list,
                            owner=request.user.userprofile,
                            is_private=account["is_private"],
                        )[0]
                    )
                    screen_names.append(account["username"])
                    evidence_links[account["username"]] = account["evidence"]
                    categories[account["username"]] = account["category"]

                except IntegrityError:
                    user = request.user.email
                    msg = f"A {account['repo']} list {account_list} already exists for {user}"
                    errors.append(
                        {
                            "message": msg,
                            "details": {
                                "list_name": account_list,
                            },
                        }
                    )

            twitter_accounts = get_twitter_accounts(screen_names)
            accounts_ids = save_accounts(twitter_accounts, evidence_links, categories)

            for twitter_accounts_list in twitter_accounts_lists:
                twitter_accounts_list.accounts.set(accounts_ids)
                twitter_accounts_list.save()

        failed_uploads = len(errors)
        return_response = {
            "lists_proccessed": {
                "success": total_accounts - failed_uploads,
                "failed": failed_uploads,
            }
        }
        if errors and account_lists:
            return_response["errors"] = errors
            status_code = status.HTTP_207_MULTI_STATUS
        elif account_lists:
            return_response["message"] = "Successfully uploaded"
            status_code = status.HTTP_201_CREATED
        else:
            return_response["errors"] = errors
            status_code = status.HTTP_400_BAD_REQUEST

        return response.Response(return_response, status=status_code)
