from collections import Counter
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

""" Valence scale...
80-100: Your songs are pretty happy! You must also be pretty happy! Strange...
60-79: Your music is above-average-ly happy. You are probably boring :///...
50-59: Choose a lane...
30-59: Awww your music is a little sad. Just cheer up haha!
0-29: Who hurt you?
"""
#region Authentication...
client_id = "190c59b4f1074e82bdb56ae09547ab22"
client_secret = "4391e01cc3ee4baa8ce7e591b39d980c"
redirect_uri = "http://127.0.0.1:8000/callback/"

scope = "user-follow-read user-library-read user-library-read playlist-read-private user-read-recently-played user-top-read playlist-read-collaborative"

def createOAuth():
    sp_auth = SpotifyOAuth(
        scope=scope,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )
    return sp_auth

def delCache():
    # Deleting cache file before certain views...
    if os.path.exists(".cache"):
        os.remove(".cache")


def validateToken(token_info):
    sp_auth = createOAuth()
    sp = spotipy.Spotify(auth=token_info["access_token"])
    try:
        if sp.me():
            return token_info
    except spotipy.client.SpotifyException:
        token_info = sp_auth.validate_token(token_info)
        return token_info
#endregion

def get_top_tracks(sp):
    """Return current user's top 10 tracks, along with
        - top artists
        - top albums
        - year most of the tracks are from
    accquired through top 100 tracks/ however many top tracks available
    """
    data = {"tracks": [], "uri": [], "artists": [], "albums": [], "year_released": []}
    artists = []
    albums = []
    year_released = []

    # Loop to get all top tracks
    offset = 0
    while True:
        results = sp.current_user_top_tracks(
            time_range="long_term", limit=50, offset=offset
        )

        if not results["items"]:
            break

        for item in results["items"]:
            data["uri"].append(item["uri"])

            # Only get album name if it's not a 'single'
            if item["album"]["album_type"] != "SINGLE":
                album = item["album"]["name"]
                albums.append(album)
            else:
                album = "single"
            # Track info
            track = {
                "name": item["name"],
                "album": album,
                "url": item["external_urls"]["spotify"],
                "artists": ", ".join([i["name"] for i in item["album"]["artists"]]),
                "images": item["album"]["images"][0]["url"],
            }
            artists.extend(i["name"] for i in item["album"]["artists"])
            year_released.append(item["album"]["release_date"][0:4])
            data["tracks"].append(track)

        offset += 49

    # Getting most popular artists/ albums and times they appear in list
    artists = [
        {"artist": item[0], "times_appear": item[1]}
        for item in Counter(artists).most_common()
    ]
    albums = [
        {"album": item[0], "times_appear": item[1]}
        for item in Counter(albums).most_common()
    ]
    year_released = [
        {"year": item[0], "times_appear": item[1]}
        for item in Counter(year_released).most_common()
    ]

    data["tracks"] = data["tracks"][:10]
    data["uri"] = data["uri"]
    data["artists"] = artists
    data["albums"] = albums
    data["year_released"] = year_released

    return data


def get_top_playlists(sp):
    """Get user's:
    - number of playlists
    - playlist w most songs + length
    """

    data = {"playlist_count": 0, "top_playlist": ""}

    most_track_count = 0
    playlist_count = 0
    non_local_tracks = []
    local_track = 0

    # Loop all playlists to find one with most tracks
    offset = 0
    top_playlist_uri = ""
    top_playlist_name = ""
    date_added = []
    while True:
        playlists = sp.current_user_playlists(limit=20, offset=offset)
        if not playlists["items"]:
            break

        for item in playlists["items"]:
            playlist_count += 1
            if int(item["tracks"]["total"]) > most_track_count:
                most_track_count = int(item["tracks"]["total"])
                top_playlist_uri = item["uri"]
                top_playlist_name = item["name"]

        offset += 19

    # If there's no playlist
    if playlist_count == 0:
        return None

    data["playlist_count"] = playlist_count

    # Get playlist's duration and track URIs
    duration = 0
    offset = 0
    while True:
        playlist = sp.playlist_items(
            playlist_id=top_playlist_uri, limit=100, offset=offset
        )

        if not playlist["items"]:
            break

        for item in playlist["items"]:
            # Get duration
            duration += int(item["track"]["duration_ms"])

            # Get non-local tracks' uri and count number of local tracks
            if not item["track"]["is_local"]:     
                non_local_tracks.append(item["track"]["uri"])
            else:           
                local_track += 1

            # Get time track was added to playlist
            date_added.append(item["added_at"][0:7])

        offset += 100

    top_playlist = {
        "name": top_playlist_name,
        "duration": duration,
        "track_count": most_track_count,
        "image": sp.playlist_cover_image(playlist_id=top_playlist_uri),
        "uris": non_local_tracks,
        "local_tracks" : local_track,
        "common_date_added" : Counter(date_added).most_common(1),
    }

    data["top_playlist"] = top_playlist

    return data


def get_recent_tracks(sp):
    """Return current user's recent listened artist + albums
    accquired through 50 recent tracks/ however many recent tracks available
    """
    data = {"artists": [], "albums": [], "uri": []}
    artists = []
    albums = []

    recent_tracks = sp.current_user_recently_played()
    for item in recent_tracks["items"]:
        item = item["track"]

        data["uri"].append(item["uri"])

        # Only get album name if it's not a 'single'
        if item["album"]["album_type"] != "SINGLE":
            album = item["album"]["name"]
            albums.append(album)

        artists.append(item["artists"][0]["name"])

    artists = [
        {"artist": item[0], "times_appear": item[1]}
        for item in Counter(artists).most_common()
    ]
    albums = [
        {"album": item[0], "times_appear": item[1]}
        for item in Counter(albums).most_common()
    ]

    data["artists"] = artists
    data["albums"] = albums

    return data


def get_audio_features(audio_features):
    """Get average valence+ energy+ danceability+ instrumental of a set of tracks"""
    __audio_features = {}

    for feature in audio_features:
        __audio_features["valence"] += float(feature["valence"])
        __audio_features["energy"] += float(feature["energy"])
        __audio_features["instrumentalness"] += float(feature["instrumentalness"])
        __audio_features["danceability"] += float(feature["danceability"])
        
    __audio_features["valence"] /= len(audio_features)
    __audio_features["energy"] /= len(audio_features)
    __audio_features["danceability"] /= len(audio_features)
    __audio_features["instrumentalness"] /= len(audio_features)

    return __audio_features
