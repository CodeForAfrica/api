from django.apps import AppConfig


class AuthenticatioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "twoopstracker.authentication"

    def ready(self):
        import twoopstracker.authentication.signals  # noqa
