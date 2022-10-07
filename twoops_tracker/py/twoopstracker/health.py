import datetime
from datetime import datetime,timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from twoopstracker.twoops.models import Tweet


@api_view(["GET"])
def health_check(request):
    # this can be expanded to include checks e.g
    # 1. has there been any tweets collected in the last 24 hours\
    # and if not it might indicate the system not being functional
    '''
    Check last created tweet within 6 hours
    '''
    t_now = datetime.datetime.now(timezone.utc)
    try:
        last_created_tweet = Tweet.objects.only('created_at').last()
        time_diff = t_now - last_created_tweet
        if time_diff.seconds < 21600:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
