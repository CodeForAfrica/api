from django.urls import path

from .views import (
    AccountsList,
    AccountsLists,
    AccountsListsDownload,
    TweetsDownloadView,
    TweetSearchesView,
    TweetSearchView,
    TweetsInsightsView,
    TweetsView,
)

urlpatterns = [
    path("tweets/", TweetsView.as_view(), name="tweets"),
    path("tweets/download", TweetsDownloadView.as_view(), name="tweets_download"),
    path("tweets/insights", TweetsInsightsView.as_view(), name="tweets_insights"),
    path("tweets/searches", TweetSearchesView.as_view(), name="tweets_searches"),
    path(
        "tweets/searches/<pk>",
        TweetSearchView.as_view(),
        name="single_saved_search",
    ),
    path("lists/", AccountsLists.as_view(), name="accounts_list"),
    path(
        "lists/download", AccountsListsDownload.as_view(), name="accounts_list_download"
    ),
    path("lists/<pk>", AccountsList.as_view(), name="single_account_list"),
]
