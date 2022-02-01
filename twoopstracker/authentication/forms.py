from allauth.account import app_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import ResetPasswordForm as DefaultPasswordResetForm
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str, user_username
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


class CustomResetPasswordForm(DefaultPasswordResetForm):
    def save(self, request, **kwargs):
        current_site = get_current_site(request)
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", default_token_generator)

        for user in self.users:

            uid = user_pk_to_url_str(user)
            token = token_generator.make_token(user)
            frontend_url = settings.TWOOPSTRACKER_PASSWORD_RESET_URL.rstrip("/")
            password_reset_url = f"{frontend_url}/{uid}/{token}"

            context = {
                "current_site": current_site,
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
