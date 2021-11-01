from django.urls import path

from .views import TweetsView

urlpatterns = [
    path("tweets/", TweetsView.as_view(), name="tweets"),
]
