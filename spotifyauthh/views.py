import spotipy
from django.views.generic.base import RedirectView, TemplateView
from django.urls import reverse
import urllib
from spotifyauthh.utils import *
import plotly
import plotly.express as px
import pandas as pd
# Create your views here.

class HomeView(TemplateView):
    """Home page"""

    template_name = "home.html"

class LoginView(RedirectView):
    """Login page"""
    # Users shouldn't see this page at all
    delCache()

    # Redirect to callback url
    sp_auth = createOAuth()

    redirect_url = sp_auth.get_authorize_url()

    redirect_url = urllib.parse.unquote(redirect_url)

    url = redirect_url


class CallbackView(RedirectView):
    """ Callback page-- user shouldn't be seeing this page at all """
    # Callback page to which users are redirected after logging in
    # Redirect to analysis url
    def get_redirect_url(self, *args, **kwargs):
        url = super().get_redirect_url(*args, **kwargs)

        # Hijack this method to cache token
        sp_auth = createOAuth()

        # Get code from url
        code = self.request.GET.get("code", "")

        # If successful, get token
        if code != "":
            token_info = sp_auth.get_access_token(code=code)

        if token_info:
            self.request.session.clear()
            self.request.session["token"] = token_info
            self.request.session.modified = True

            url = reverse("test")
            return url
        # TODO: Handle failed callback    
        else:
            url = reverse("home")
            return url


class LogOutView(RedirectView):
    """Log Out view"""

    # Users shouldn't see this page at all

    # Redirect to home page
    def get_redirect_url(self, *args, **kwargs):
        url = super().get_redirect_url(*args, **kwargs)
        url = reverse("home")

        # Hijack this method to delete cache token
        self.request.session.clear()
        delCache()

        return url

class TestView(TemplateView):
    token_exist = True
    is_sufficient = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get cached token from session and validate
        try:
            token_info = self.request.session["token"]
            token_info = validateToken(token_info)

            # Recache if token info changes
            if token_info != self.request.session["token"]:
                self.request.session.clear()
                self.request.session["token"] = token_info
                self.request.session.modified = True

            # Create Spotify obj and get information
            sp = spotipy.Spotify(auth=token_info["access_token"])
            user_info_json = sp.me()

            top_playlist = get_top_playlists(sp)

            # Get recently played data
            top_recently_played = get_recent_tracks(sp)
            if len(top_recently_played["uri"]) != 0:
                __recent_audio_features = sp.audio_features(top_recently_played["uri"])
                recent_audio_features = get_audio_features(__recent_audio_features)
                context["recent_audio_features"] = recent_audio_features
            # If there's no recently played => not enough data
            else:
                self.is_sufficient = False
                return context

            # Get top tracks data
            top_tracks = get_top_tracks(sp)
            if len(top_tracks["uri"]) != 0:
                __top_audio_features = sp.audio_features(top_tracks["uri"])
                top_audio_features = get_audio_features(__top_audio_features)
                context["top_audio_features"] = top_audio_features

            context["user"] = user_info_json
            context["token_info"] = token_info
            context["top_tracks"] = top_tracks
            context["top_playlist"] = top_playlist
            context["top_recent"] = top_recently_played
            context["graph"] = getGraph(top_audio_features)

            return context
        except KeyError:
            self.token_exist = False
            return context
    
    def get_template_names(self):
        """ Return template name depending on token status"""
        if self.token_exist and self.is_sufficient:
            template_name = "home.html"
        else: 
            template_name = "error.html"
        return template_name



def getGraph(features):
    # Return radar graph from a dict of audio features
    # {'valence': x, 'energy': y, 'danceability': z, 'instrumentalness': m}
    df = pd.DataFrame(dict(r = list(features.values()), theta = list(features.keys())))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, width = 700, height = 700, range_r =[0,1])
    fig.update_traces(fill='toself')
    graph_div = plotly.offline.plot(fig, auto_open = False, output_type="div")

    return graph_div
