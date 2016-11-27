from .models import DangerLevel
from rest_framework import serializers


class DangerLevelSerializer(serializers.Serializer):
    level = serializers.IntegerField(required=True)
    anger_level = serializers.IntegerField(required=True)
    disgust_level = serializers.IntegerField(required=True)
    sadness_level = serializers.IntegerField(required=True)


class AuthUrlSerializer(serializers.Serializer):
    url = serializers.CharField(required=True, max_length=200)


# class RequestSerializer(serializers.Serializer):
#     screen_name = serializers.CharField(required=True, max_length=200)
#     oauth_token = serializers.CharField(required=True, max_length=200)