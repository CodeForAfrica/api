import requests  # type: ignore
from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
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


def verify_id_token(token):
    try:
        id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.TWOOPSTRACKER_GOOGLE_OAUTH2_CLIENT_ID,
        )
        return True
    except Exception:
        return False


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
    id_token = validated_data.get("id_token")

    if not id_token:
        raise ValidationError({"error": "No id_token was provided."})

    if verify_id_token(id_token):
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
        else:
            raise ValidationError({"error": "No access_token was provided."})
    else:
        raise ValidationError({"error": "Invalid access token."})
