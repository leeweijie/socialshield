from django.db import models

# Create your models here.


class DangerLevel(models.Model):
    screen_name = models.CharField(max_length=200, primary_key=True)
    level = models.IntegerField()
    last_updated = models.DateTimeField('Date and time of when this entry was last updated')
    anger_level = models.IntegerField(default=0)
    disgust_level = models.IntegerField(default=0)
    sadness_level = models.IntegerField(default=0)

    def __str__(self):
        return "{} {}".format(self.screen_name, self.level)


class User(models.Model):
    oauth_token = models.CharField(max_length=200, primary_key=True)
    oauth_secret = models.CharField(max_length=200)

    def __str__(self):
        return self.oauth_token + ' ' + self.oauth_secret

