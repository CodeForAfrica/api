from rest_framework import serializers


class TokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    id_token = serializers.CharField()


class InputSerializer(serializers.Serializer):
    tokens = TokenSerializer()
    provider = serializers.CharField()
