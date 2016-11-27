from django.shortcuts import render
from requests_oauthlib import OAuth1Session
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import constants
from . import serializers
from . import models
from . import helper


# Create your views here.
def index(request):
    return render(request, 'socialshield/index.html')


@api_view(['GET'])
def get_auth_url(request):
    oauth_client = OAuth1Session(constants.CONSUMER_KEY,
                                 client_secret=constants.CONSUMER_SECRET,
                                 callback_uri=constants.AUTH_CALLBACK)
    oauth_client.fetch_request_token(constants.REQUEST_TOKEN_URL)
    url = oauth_client.authorization_url(constants.AUTHORIZATION_URL)
    response = serializers.AuthUrlSerializer({'url': url})
    return Response(response.data)


def authorize(request):
    oauth_client = OAuth1Session(constants.CONSUMER_KEY, client_secret=constants.CONSUMER_SECRET,
                                 resource_owner_key=request.GET['oauth_token'],
                                 verifier=request.GET['oauth_verifier'])

    resp = oauth_client.fetch_access_token(constants.ACCESS_TOKEN_URL)

    models.User.objects.update_or_create(oauth_token=resp.get('oauth_token'), defaults={
        'oauth_secret': resp.get('oauth_token_secret')
    })

    return render(request, 'socialshield/authorized.html', {'token': resp.get('oauth_token')})


def tone(request):
    record = helper.get_danger_level(
        screen_name=request.GET['screen_name'],
        oauth_token=None
    )
    return render(request, 'socialshield/tone.html', {
        'anger': record.anger_level,
        'disgust': record.disgust_level,
        'sadness': record.sadness_level
    })


def test(request):
    return render(request, 'socialshield/test.html')


@api_view(['GET'])
def get_danger_level(request):
    record = helper.get_danger_level(
        screen_name=request.GET['screen_name'],
        oauth_token=request.GET['oauth_token']
    )
    response = serializers.DangerLevelSerializer({
        'level': record.level,
        'anger_level': record.anger_level,
        'disgust_level': record.disgust_level,
        'sadness_level': record.sadness_level,
    })
    return Response(response.data)
