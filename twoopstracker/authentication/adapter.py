from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url"""
        url = reverse("account_confirm_email", args=[emailconfirmation.key])
        frontend_api_url = settings.TWOOPSTRACKER_FRONTEND_API_URL.rstrip("/")
        activation_url = f"{frontend_api_url}{url}"
        return activation_url