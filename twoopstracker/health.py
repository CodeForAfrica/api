from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    # this can be expanded to include checks e.g
    # 1. has there been any tweets collected in the last 24 hours\
    # and if not it might indicate the system not being functional
    return Response(status=status.HTTP_200_OK)
