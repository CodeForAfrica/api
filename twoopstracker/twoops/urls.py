from django.urls import path

from .views import Search, TweetsView

urlpatterns = [
    path("tweets/", TweetsView.as_view(), name="tweets"),
    path("search/", Search.as_view(), name="search"),
]
