from rest_framework import serializers


class InputSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    redirect_url = serializers.CharField(required=False)
