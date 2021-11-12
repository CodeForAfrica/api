import requests  # type: ignore
from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken

from .models import get_or_create_user
from .serializers import InputSerializer

TWOOPSTRACKER_BACKEND_URL = settings.TWOOPSTRACKER_BACKEND_URL
TWOOPSTRACKER_FRONTEND_LOGIN_URL = settings.TWOOPSTRACKER_FRONTEND_LOGIN_URL


def google_get_access_token(code, redirect_uri):
    data = {
        "code": code,
        "client_id": settings.TWOOPSTRACKER_GOOGLE_OAUTH2_CLIENT_ID,
        "client_secret": settings.TWOOPSTRACKER_GOOGLE_OAUTH2_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    response = requests.post("https://www.googleapis.com/oauth2/v4/token", data=data)
    return response.json()["access_token"]


def google_get_user_info(access_token):
    response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo?access_token=" + access_token
    )
    if not response.ok:
        raise ValidationError("Failed to obtain user info from Google.")
    return response.json()


@api_view(["GET", "POST"])
def login(request):
    input_serializer = InputSerializer(data=request.GET)
    input_serializer.is_valid(raise_exception=True)

    validated_data = input_serializer.validated_data

    if validated_data.get("code"):
        # login successful
        access_token = google_get_access_token(
            validated_data.get("code"),
            redirect_uri=f"{TWOOPSTRACKER_BACKEND_URL}/auth/login/google/",
        )
        user_data = google_get_user_info(access_token=access_token)
        profile_data = {
            "email": user_data["email"],
            "first_name": user_data["given_name"],
            "last_name": user_data["family_name"],
        }
        user, _ = get_or_create_user(**profile_data)
        if user:
            refresh = RefreshToken.for_user(user)
            response = redirect(
                f"{TWOOPSTRACKER_FRONTEND_LOGIN_URL}?access_token={str(refresh.access_token)}\
                    &refresh_token={str(refresh)}"
            )
            return response
    elif validated_data.get("error"):
        return redirect(
            f"{TWOOPSTRACKER_FRONTEND_LOGIN_URL}?error={validated_data.get('error')}"
        )
