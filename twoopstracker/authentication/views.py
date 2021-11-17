import requests  # type: ignore
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import get_or_create_user
from .serializers import InputSerializer


def google_get_user_info(access_token):
    response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo?access_token=" + access_token
    )
    if not response.ok:
        raise ValidationError("Failed to obtain user info from Google.")
    return response.json()


@api_view(["POST"])
def login(request):
    input_serializer = InputSerializer(data=request.data)
    input_serializer.is_valid(raise_exception=True)

    validated_data = input_serializer.validated_data

    """
    The Frontend will send a post request with the google access token of the authenticated user.
    The backend will then use the access token to get the user info from Google.
    The backend will then decide if to allow this user to login or not.
    """
    access_token = validated_data.get("access_token")

    if access_token:
        # login successful from the F.E
        user_data = google_get_user_info(access_token=access_token)
        profile_data = {
            "email": user_data["email"],
            "first_name": user_data["given_name"],
            "last_name": user_data["family_name"],
        }
        user, _ = get_or_create_user(**profile_data)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                }
            )

    return Response(input_serializer.data)
