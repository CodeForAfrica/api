from django.urls import path

from .views import (
    AccountsList,
    AccountsLists,
    FileUploadAPIView,
    TweetSearchesView,
    TweetSearchView,
    TweetsInsightsView,
    TweetsView,
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
    path("lists/upload", FileUploadAPIView.as_view(), name="accounts_list_upload"),
    path("lists/<pk>", AccountsList.as_view(), name="single_account_list"),
    path("accounts/", TwitterAccountsView.as_view(), name="accounts"),
]
