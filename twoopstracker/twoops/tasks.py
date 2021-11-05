from celery import shared_task
from celery.utils.log import get_task_logger

from twoopstracker.twoops.models import TwitterAccount

logger = get_task_logger(__name__)


@shared_task
def save_user(account_id, user):
    twitter_account = TwitterAccount.objects.get(account_id=account_id)
    twitter_account.name = user.get("name")
    twitter_account.screen_name = user.get("screen_name")
    twitter_account.description = user.get("description")
    twitter_account.verified = user.get("verified")
    twitter_account.protected = user.get("protected")
    twitter_account.location = user.get("location")
    twitter_account.followers_count = user.get("followers_count")
    twitter_account.friends_count = user.get("friends_count")
    twitter_account.favourites_count = user.get("favourites_count")
    twitter_account.statuses_count = user.get("statuses_count")
    twitter_account.profile_image_url = user.get("profile_image_url")

    twitter_account.save()
    logger.info(f"Saved twitter account: {twitter_account.name} for monitoring")
