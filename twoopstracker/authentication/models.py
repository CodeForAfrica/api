from django.contrib.auth.models import AbstractUser

from twoopstracker.db.models import TimestampedModelMixin


class User(TimestampedModelMixin, AbstractUser):
    pass
