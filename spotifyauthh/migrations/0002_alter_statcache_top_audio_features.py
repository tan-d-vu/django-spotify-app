# Generated by Django 3.2 on 2021-05-25 23:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spotifyauthh', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statcache',
            name='top_audio_features',
            field=models.JSONField(),
        ),
    ]