from django.urls import path

from .views import AccountsList, SingleTwitterList, TweetSearchesView, TweetsView

urlpatterns = [
    path("tweets/", TweetsView.as_view(), name="tweets"),
    path("tweets/searches", TweetSearchesView.as_view(), name="tweets_searches"),
    path("lists/", AccountsList.as_view(), name="accounts_list"),
    path("lists/<pk>", SingleTwitterList.as_view(), name="single_account_list"),
]
