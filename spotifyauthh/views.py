from django.shortcuts import render, redirect
from requests import auth
import spotipy
from spotipy import oauth2
from spotipy.oauth2 import SpotifyOAuth
from django.views.generic.base import RedirectView, TemplateView
from django.urls import reverse
import urllib
from spotifyauthh.utils import *
# Create your views here.


scope = "user-follow-read user-library-read user-library-read playlist-read-private user-read-recently-played user-top-read playlist-read-collaborative"
redirect_uri = "http://127.0.0.1:8000/callback/"
client_id = "190c59b4f1074e82bdb56ae09547ab22"
client_secret = "4391e01cc3ee4baa8ce7e591b39d980c"


def createOAuth():
    sp_auth = SpotifyOAuth(
        scope=scope,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        open_browser=True,
    )
    return sp_auth

def validateToken(token_info):
    sp_auth = createOAuth()
    sp = spotipy.Spotify(auth=token_info["access_token"])
    try:
        if sp.me():
            return token_info
    except spotipy.client.SpotifyException:
        token_info = sp_auth.validate_token(token_info)
        return token_info

class HomeView(TemplateView):
    """Home page"""

    template_name = "home.html"


class LoginView(RedirectView):
    """Login page"""

    # Users shouldn't see this page at all
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
        # Get code from url
        code = self.request.GET.get("code", "")

        # If successful, create sp_auth and get token
        if code != "":
            sp_auth = createOAuth()
            token_info = sp_auth.get_access_token(code)

        if token_info:
            self.request.session["token"] = token_info
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
        del self.request.session["token"]
        self.request.session.modified = True

        return url


class TestView(TemplateView):
    token_exist = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get cached token from session and validate
        try:
            token_info = self.request.session["token"]
            token_info = validateToken(token_info)

            # Recache if token info changes
            if token_info != self.request.session["token"]:
                self.request.session["token"] = token_info
                self.request.session.modified = True

            # Create Spotify obj and get information
            sp = spotipy.Spotify(auth=token_info["access_token"])
            user_info_json = sp.me()

            data = get_top_tracks(sp)


            context["user"] = user_info_json
            context["token_info"] = token_info
            context["top_tracks"] = data

            return context
        except KeyError:
            self.token_exist = False
            return context
    
    def get_template_names(self):
        """ Return template name depending on token status"""
        if self.token_exist:
            template_name = "home.html"
        else: 
            template_name = "error.html"
        return template_name

