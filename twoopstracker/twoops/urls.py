from django.urls import path

from .views import AccountsList, SingleTwitterList, TweetsView

urlpatterns = [
    path("tweets/", TweetsView.as_view(), name="tweets"),
    path("lists/", AccountsList.as_view(), name="accounts_list"),
    path("lists/<pk>", SingleTwitterList.as_view(), name="single_account_list"),
]
