# Generated by Django 3.2 on 2021-05-25 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StatCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('top_artists', models.JSONField()),
                ('user_info', models.JSONField()),
                ('top_tracks', models.JSONField()),
                ('top_playlist', models.JSONField()),
                ('top_audio_features', models.TextField()),
                ('time_cached', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]