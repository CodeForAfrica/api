from django.urls import path

from .views import (
    AccountsList,
    AccountsListDetailView,
    AccountsLists,
    AccountsListUploadAPIView,
    TweetSearchesView,
    TweetSearchView,
    TweetsInsightsView,
    TweetsView,
    TwitterAccountCategoriesView,
    TwitterAccountsView,
)

urlpatterns = [
    path("tweets/", TweetsView.as_view(), name="tweets"),
    path("tweets/insights", TweetsInsightsView.as_view(), name="tweets_insights"),
    path("tweets/searches", TweetSearchesView.as_view(), name="tweets_searches"),
    path(
        "tweets/searches/<pk>",
        TweetSearchView.as_view(),
        name="single_saved_search",
    ),
    path("lists/", AccountsLists.as_view(), name="accounts_list"),
    path(
        "lists/upload", AccountsListUploadAPIView.as_view(), name="accounts_list_upload"
    ),
    path("lists/<pk>", AccountsList.as_view(), name="single_account_list"),
    path(
        "lists/<pk>/accounts", AccountsListDetailView.as_view(), name="accounts_in_list"
    ),
    path("accounts/", TwitterAccountsView.as_view(), name="accounts"),
    path(
        "accounts/categories/",
        TwitterAccountCategoriesView.as_view(),
        name="categories",
    ),
]
