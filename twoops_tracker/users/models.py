from django.contrib.auth.models import AbstractUser

from twoops_tracker.db.models import TimestampedModelMixin


class TwoopsUser(TimestampedModelMixin, AbstractUser):
    pass
