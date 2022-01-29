from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse


from allauth.account import app_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import \
    ResetPasswordForm as DefaultPasswordResetForm
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str, user_username


class CustomResetPasswordForm(DefaultPasswordResetForm):
    def save(self, request, **kwargs):
        email = self.cleaned_data["email"]
        current_site = get_current_site(request)

        if not self.users:
            self._send_unknown_account_mail(request, email, current_site)
        else:
            self._send_password_reset_mail(request, email, current_site, self.users, **kwargs)
        return 
    def _send_unknown_account_mail(self, request, email, current_site):
        signup_url = settings.TWOOPSTRACKER_SIGNUP_URL
        context = {
            "current_site": current_site,
            "email": email,
            "request": request,
            "signup_url": signup_url,
        }
        get_adapter(request).send_mail("account/email/unknown_account", email, context)

    def _send_password_reset_mail(self, request, email, current_site, users, **kwargs):
        token_generator = kwargs.get("token_generator", default_token_generator)

        for user in users:

            temp_key = token_generator.make_token(user)
            path = reverse(
                'password_reset_confirm',
                args=[user_pk_to_url_str(user), temp_key],
            )
            frontend_url = settings.TWOOPSTRACKER_FRONTEND_API_URL.rstrip("/")
            password_reset_url = f"{frontend_url}{path}"

            context = {
                'current_site': current_site,
                'user': user,
                'password_reset_url': password_reset_url,
                'request': request,
            }
            if app_settings.AUTHENTICATION_METHOD != app_settings.AuthenticationMethod.EMAIL:
                context['username'] = user_username(user)
            get_adapter(request).send_mail(
                'account/email/password_reset_key', email, context
            )
        return email