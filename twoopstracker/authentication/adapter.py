from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url"""
        frontend_url = settings.TWOOPSTRACKER_EMAIL_CONFRIMATION_URL.rstrip("/")
        activation_url = f"{frontend_url}/{emailconfirmation.key}"
        return activation_url
