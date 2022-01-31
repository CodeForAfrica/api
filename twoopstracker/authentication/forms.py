from allauth.account import app_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import ResetPasswordForm as DefaultPasswordResetForm
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str, user_username
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


class CustomResetPasswordForm(DefaultPasswordResetForm):
    def save(self, request, **kwargs):
        email = self.cleaned_data["email"]

        if not self.users:
            self._send_unknown_account_mail(request, email)
        else:
            self._send_password_reset_mail(request, email, self.users, **kwargs)
        return

    def _send_unknown_account_mail(self, request, email):
        signup_url = settings.TWOOPSTRACKER_SIGNUP_URL
        context = {
            "current_site": get_current_site(request),
            "email": email,
            "request": request,
            "signup_url": signup_url,
        }
        get_adapter(request).send_mail("account/email/unknown_account", email, context)

    def _send_password_reset_mail(self, request, email, users, **kwargs):
        token_generator = kwargs.get("token_generator", default_token_generator)

        for user in users:

            token = token_generator.make_token(user)
            frontend_url = settings.TWOOPSTRACKER_PASSWORD_RESET_URL.rstrip("/")
            uid = user_pk_to_url_str(user)
            password_reset_url = f"{frontend_url}/{uid}/{token}"

            context = {
                "current_site": get_current_site(request),
                "user": user,
                "password_reset_url": password_reset_url,
                "request": request,
            }
            if (
                app_settings.AUTHENTICATION_METHOD
                != app_settings.AuthenticationMethod.EMAIL
            ):
                context["username"] = user_username(user)
            get_adapter(request).send_mail(
                "account/email/password_reset_key", email, context
            )
        return email
