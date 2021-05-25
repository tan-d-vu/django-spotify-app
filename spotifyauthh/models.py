from django.db import models
from django.db.models.base import Model, ModelBase

# Create your models here.
class StatCache(models.Model):
    top_artists = models.JSONField()
    user_info = models.JSONField()
    top_tracks = models.JSONField()
    top_playlist = models.JSONField()
    top_audio_features = models.JSONField()
    time_cached = models.DateTimeField(auto_now_add=True)
