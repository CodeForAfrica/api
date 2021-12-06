import logging
import os
import time

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "twoopstracker.settings")

app = Celery("twoopstracker")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

logger = logging.getLogger(__name__)


@app.task(name="start_stream_listener")
def start_stream_listener():
    from twoopstracker.twitterclient.twitter_client import TwitterClient

    logger.info("Starting stream listener")
    client = TwitterClient()
    client.run()
    time.sleep((settings.TWOOPTRACKER_STREAM_LISTENER_INTERVAL * 60) - 5)
    # disconnect stream listener since it will be restarted
    client.disconnect()


app.conf.beat_schedule = {
    "start_stream_listener": {
        "task": "start_stream_listener",
        "schedule": crontab(
            minute=f"*/{settings.TWOOPTRACKER_STREAM_LISTENER_INTERVAL}"
        ),
    },
}
