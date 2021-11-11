from django.urls import path

from .views import login

urlpatterns = [
    path("login/google/", login, name="login"),
]
