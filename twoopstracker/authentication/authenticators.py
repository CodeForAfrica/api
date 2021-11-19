import requests  # type: ignore
from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import get_or_create_user


class GoogleAuthenticator:
    def authenticate(self, access_token, id_token):
        if self.verify_id_token(id_token):
            # login successful from the F.E
            user_data = self.google_get_user_info(access_token=access_token)
            profile_data = {
                "email": user_data["email"],
                "first_name": user_data["given_name"],
                "last_name": user_data["family_name"],
            }
            user, _ = get_or_create_user(**profile_data)
            if user:
                refresh = RefreshToken.for_user(user)
                return {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                }
        else:
            raise ValidationError({"error": "Invalid access token."})

    def verify_id_token(self, token):
        try:
            id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.TWOOPSTRACKER_GOOGLE_OAUTH2_CLIENT_ID,
            )
            return True
        except Exception:
            return False

    def google_get_user_info(self, access_token):
        response = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo?access_token=" + access_token
        )
        if not response.ok:
            raise ValidationError({"error": "Failed to obtain user info from Google."})
        return response.json()
