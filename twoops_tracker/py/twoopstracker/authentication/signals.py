from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from twoopstracker.twoops.models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = UserProfile(user=instance)
        user_profile.save()
