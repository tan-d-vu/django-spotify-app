import spotipy
from django.views.generic.base import RedirectView, TemplateView
from django.urls import reverse
import urllib
from spotifyauthh.utils import *
from .models import StatCache
from django.core.exceptions import ObjectDoesNotExist
import datetime

# Create your views here.


class HomeView(TemplateView):
    """Home page"""

    template_name = "spotifyauthh/home.html"


class LoginView(RedirectView):
    """Login page"""

    # Users shouldn't see this page at all
    def get_redirect_url(self, *args, **kwargs):
        url = super().get_redirect_url(*args, **kwargs)

        # Hijack this method to delete cache token
        delCache()

        # Redirect to callback url
        sp_auth = createOAuth()

        redirect_url = sp_auth.get_authorize_url()

        url = urllib.parse.unquote(redirect_url)

        return url


class CallbackView(RedirectView):
    """Callback page-- user shouldn't be seeing this page at all"""

    # Callback page to which users are redirected after logging in
    # Redirect to analysis url
    def get_redirect_url(self, *args, **kwargs):
        url = super().get_redirect_url(*args, **kwargs)

        # Hijack this method to cache token (for current session)
        sp_auth = createOAuth()

        # Get code from url
        code = self.request.GET.get("code", "")

        # If successful, get token
        if code != "":
            token_info = sp_auth.get_access_token(code=code)

            if token_info:
                self.request.session["token"] = token_info

                print(self.request.session["token"])

                url = reverse("stat")
                return url
        else:
            url = reverse("home")
            return url


class StatView(TemplateView):
    token_exist = True
    is_sufficient = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        print(self.request.session["token"])

        # Get cached token from session and validate
        try:
            token_info = self.request.session["token"]
            token_info = validateToken(token_info)
        except KeyError:
            self.token_exist = False
            return context

        # Recache if token info changes
        if token_info != self.request.session["token"]:
            self.request.session["token"] = token_info

        # Create Spotify obj
        sp = spotipy.Spotify(auth=token_info["access_token"])
        user_info_json = sp.me()

        # Check if user is in database
        try:
            cached_stat = StatCache.objects.get(user_info=user_info_json)
            if (
                datetime.datetime.now(datetime.timezone.utc) - cached_stat.time_cached
            ).days >= 14:
                raise StatCache.DoesNotExist

        # If not in db or been in there for long, get info from scratch and store in model
        except StatCache.DoesNotExist:
            # Top playlists
            top_playlist = get_top_playlists(sp)

            # Get top tracks data
            top_tracks = get_top_tracks(sp)
            if len(top_tracks["uri"]) != 0:
                top_audio_features = get_audio_features(sp, top_tracks["uri"])

            top_artists = get_top_artists(sp)

            cached_stat = StatCache.objects.create(
                top_artists=top_artists,
                user_info=user_info_json,
                top_tracks=top_tracks,
                top_playlist=top_playlist,
                top_audio_features=top_audio_features,
            )
            cached_stat.save()

        # Get recently played data
        top_recently_played = get_recent_tracks(sp)
        if len(top_recently_played["uri"]) != 0:
            recent_audio_features = get_audio_features(sp, top_recently_played["uri"])
            context["recent_audio_features"] = recent_audio_features

        # If there's no recently played => not enough data to analyze
        else:
            self.is_sufficient = False
            return context

        # # Get song recommendations
        # seed_genres = []
        # for i in range(0, len((cached_stat.top_artists)["genres"])):
        #     seed_genres.append(((cached_stat.top_artists)["genres"][i][0]))

        # track_rec = get_song_recommendations(
        #     sp,
        #     (cached_stat.top_artists)["uri"][:5],
        #     seed_genres,
        #     top_recently_played["uri"][:5],
        # )

        # Update other context
        context["top_recent"] = top_recently_played
        context["top_artists"] = cached_stat.top_artists
        context["user"] = user_info_json
        context["top_tracks"] = cached_stat.top_tracks
        context["top_playlist"] = cached_stat.top_playlist
        # context["pfp"] = cached_stat.user_info["images"][0]["url"]
        context["top_audio_features"] = cached_stat.top_audio_features
        # Graphs
        context["graph"] = get_polar_graph(cached_stat.top_audio_features)
        context["graph1"] = get_polar_graph(recent_audio_features)
        context["graph2"] = get_overlay_polar_graph(
            [recent_audio_features, (cached_stat.top_audio_features)]
        )

        # context["track_rec"] = track_rec

        return context

    def get_template_names(self):
        """Return template name depending on token status"""
        if self.token_exist and self.is_sufficient:
            template_name = "spotifyauthh/analysis.html"
        else:
            template_name = "spotifyauthh/error.html"
        return template_name


class LogOutView(RedirectView):
    """Log Out view"""

    # Users shouldn't see this page at all

    # Redirect to home page
    def get_redirect_url(self, *args, **kwargs):
        url = super().get_redirect_url(*args, **kwargs)
        url = reverse("home")

        # Hijack this method to delete cache token
        self.request.session.flush()
        delCache()

        return url
