from typing import List

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from twoopstracker.db.models import TimestampedModelMixin


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        extra_fields = {"is_staff": False, "is_superuser": False, **extra_fields}
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields = {**extra_fields, "is_staff": True, "is_superuser": True}
        user = self.create_user(email, password, **extra_fields)
        return user


class User(TimestampedModelMixin, AbstractUser):
    username = None
    email = models.EmailField(max_length=254, unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: List[str] = []

    objects = UserManager()


def get_or_create_user(email, **kwargs):
    user = User.objects.filter(email=email).first()
    if user:
        return user, False
    return User.objects.create_user(email, **kwargs), True
