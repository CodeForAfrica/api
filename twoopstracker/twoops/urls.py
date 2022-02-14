from django.urls import path

from .views import (
    AccountsList,
    AccountsListUploadAPIView,
    TweetSearchesView,
    TweetSearchView,
    TweetsInsightsView,
    TweetsView,
    TwitterAccountCategoriesView,
    TwitterAccountsLists,
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
    path("lists/", TwitterAccountsLists.as_view(), name="twitter_accounts_list-list"),
    path(
        "lists/upload", AccountsListUploadAPIView.as_view(), name="accounts_list_upload"
    ),
    path("lists/<pk>", AccountsList.as_view(), name="acccounts_list-detail"),
    path("accounts/", TwitterAccountsView.as_view(), name="tweeter_account-list"),
    path(
        "accounts/categories/",
        TwitterAccountCategoriesView.as_view(),
        name="categories",
    ),
]
