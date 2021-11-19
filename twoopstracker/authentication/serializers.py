from rest_framework import serializers


class InputSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=False)
    id_token = serializers.CharField(required=False)
