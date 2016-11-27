from django.utils import timezone

from .models import User, DangerLevel
from . import constants
from django.conf import settings

import twitter
import re
import datetime
import os
import json
from watson_developer_cloud import ToneAnalyzerV3

tone_analyzer = ToneAnalyzerV3(
   username='e356ea70-86b5-4a9f-ad8d-b7fb1a7093bd',
   password='YvvxePfL2pH8',
   version='2016-05-19')

f = open(os.path.join(settings.PROJECT_ROOT, 'swear_words.json'))
swear_words = json.load(f)
f.close()

regex_check = re.compile(r"\b(?:" + "|".join(swear_words) + r")\b", re.IGNORECASE)

CACHE_DURATION = datetime.timedelta(days=7)


def get_danger_level(screen_name, oauth_token):
    record = DangerLevel.objects.filter(screen_name=screen_name)
    if record and timezone.now() - record[0].last_updated < CACHE_DURATION:
        return record[0]

    user = User.objects.get(oauth_token=oauth_token)
    api = twitter.Api(consumer_key=constants.CONSUMER_KEY,
                      consumer_secret=constants.CONSUMER_SECRET,
                      access_token_key=user.oauth_token,
                      access_token_secret=user.oauth_secret)

    # Target profanities
    target_result = api.GetUserTimeline(screen_name=screen_name, count=200, trim_user=True, exclude_replies=True)
    target_profanities = calculate_profanities(target_result)

    # Calculate tone
    emotions = get_tone(target_result)
    if emotions:
        target_profanities += round(emotions['anger']/10)

    print("target tweet length", len(target_result))
    print('target:', target_profanities)

    # Friends profanities
    friends = api.GetFriends(screen_name=screen_name, total_count=100, include_user_entities=False, skip_status=True)
    print("friends length", len(friends))

    # Premature return if too little friends
    if len(friends) < 15:
        level = calculate_danger_level(target_profanities)
        return store_danger_level(screen_name, level, emotions)

    STEP = 10
    chunks = [[]]
    for i, friend in enumerate(friends):
        if i != 0 and i % STEP == 0:
            chunks.append([])
        chunks[i // STEP].append(friend)

    tweets = []
    for chunk in chunks:
        query = 'q=' + '%20OR%20'.join(['from%3A' + f.screen_name for f in chunk])
        result = api.GetSearch(raw_query=query+'&count=100&include_user_entities=false&skip_status=true&lang=en&result_type=mixed')
        tweets += result

    friends_profanities = calculate_profanities(tweets)
    print("friends", friends_profanities)

    # Final calculation
    aggregated_profanities = target_profanities + round(10 * friends_profanities / len(friends))
    danger_level = calculate_danger_level(aggregated_profanities)

    # Submit to database
    new_record = store_danger_level(screen_name, danger_level, emotions)

    # Return danger level
    return new_record


def store_danger_level(screen_name, danger_level, emotions):
    defaults = {}
    if emotions:
        defaults = {
            'level': danger_level,
            'anger_level': round(emotions['anger'] * 100),
            'disgust_level': round(emotions['disgust'] * 100),
            'sadness_level': round(emotions['sadness'] * 100),
            'last_updated': timezone.now()
        }
    else:
        defaults = {
            'level': danger_level,
            'last_updated': timezone.now()
        }
    return DangerLevel.objects.update_or_create(screen_name=screen_name, defaults=defaults)[0]


def calculate_profanities(tweets):
    swear_count = 0
    for tweet in tweets:
        if tweet.possibly_sensitive:
            swear_count += 1
        elif regex_check.search(tweet.text) is not None:
            swear_count += 1
    return swear_count


def calculate_danger_level(profanities):
    if profanities > 50:
        return 5
    elif profanities > 30:
        return 4
    elif profanities > 10:
        return 3
    elif profanities > 5:
        return 2
    else:
        return 1


def get_tone(tweets):
    combined = ' '.join([t.text for t in tweets])
    try:
        result = tone_analyzer.tone(text=combined, tones='emotion', sentences=False)
        if result:
            emotions = result['document_tone']['tone_categories'][0]['tones']
            return {
                'anger': [e for e in emotions if e['tone_id'] == 'anger'][0]['score'],
                'disgust': [e for e in emotions if e['tone_id'] == 'disgust'][0]['score'],
                'sadness': [e for e in emotions if e['tone_id'] == 'sadness'][0]['score'],
            }
    except Exception:
        pass
