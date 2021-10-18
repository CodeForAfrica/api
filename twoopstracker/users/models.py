from django.contrib.auth.models import AbstractUser

from twoopstracker.db.models import TimestampedModelMixin


class TwoopsUser(TimestampedModelMixin, AbstractUser):
    pass
