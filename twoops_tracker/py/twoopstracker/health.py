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
        last_tweet_id = Tweet.objects.values_list("tweet_id", flat=True).last()
        if last_tweet_id is not None:
            return Response({'tweet_id':last_tweet_id},status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
