from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from twoopstracker.twoops.models import Tweet


@api_view(["GET"])
def health_check(request):
    # this can be expanded to include checks e.g
    # 1. has there been any tweets collected in the last 24 hours\
    # and if not it might indicate the system not being functional
    try:
        first_tweet = Tweet.objects.only("tweet_id").first()
        if first_tweet:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
