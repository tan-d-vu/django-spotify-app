from collections import Counter
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import plotly
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from itertools import zip_longest

""" Valence scale...
80-100: Your songs are pretty happy! You must also be pretty happy! Strange...
60-79: Your music is above-average-ly happy. You are probably boring :///...
50-59: Choose a lane...
30-59: Awww your music is a little sad. Just cheer up haha!
0-29: Who hurt you?
"""
# region Authentication...
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


# endregion

def __parse_track(track_info):
    """Return track info from a payload entry"""
    if track_info is not None:
        return {
            "name": track_info["name"],
            "url": track_info["external_urls"]["spotify"],
            "artists": ", ".join([i["name"] for i in track_info["album"]["artists"]]),
            "images": track_info["album"]["images"][0]["url"],
        }
    else: return None

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
            track = __parse_track(item)
            track["album"] = album

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
            if (
                item["track"] is not None
            ):  # Has to check because apparently it can be None???
                duration += int(item["track"]["duration_ms"])

                # Get non-local tracks' uri and count number of local tracks
                try:
                    if not item["track"]["is_local"]:
                        non_local_tracks.append(item["track"]["uri"])
                    else:
                        local_track += 1
                except KeyError:
                    pass

                # Get time track was added to playlist
                date_added.append(item["added_at"][0:7])

        offset += 100

    top_playlist = {
        "name": top_playlist_name,
        "duration": duration,
        "track_count": most_track_count,
        "image": sp.playlist_cover_image(playlist_id=top_playlist_uri),
        "uris": non_local_tracks,
        "local_tracks": local_track,
        "common_date_added": Counter(date_added).most_common(1),
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
        if (
            item["track"] is not None
        ):  # Has to check because apparently it can be None???
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
    __audio_features = {
        "valence": 0,
        "energy": 0,
        "instrumentalness": 0,
        "danceability": 0,
    }

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


def get_top_artists(sp):
    """Get top artists and top genres"""
    data = {"artists": [], "genres": [], "uri": []}
    genres = []
    offset = 0

    while True:
        results = sp.current_user_top_artists(
            time_range="long_term", limit=50, offset=offset
        )

        if not results["items"]:
            break

        # Get first 10 top artists and list of genres of all top artists
        for i, item in enumerate(results["items"]):
            if i < 10:
                artist = {
                    "name": item["name"],
                    "images": item["images"][0]["url"],
                    "url": item["external_urls"]["spotify"],
                }
                data["artists"].append(artist)

            data["uri"].append(item["uri"])
            genres.extend(item["genres"])

        offset += 50

    # Top 5 genres
    genres = Counter(genres).most_common(5)
    data["genres"] = genres
    data["artists"] = data["artists"]

    return data


# region Data visualization
def get_polar_graph(features):
    # Return polar graph from a dict of audio features
    # {'valence': x, 'energy': y, 'danceability': z, 'instrumentalness': m}
    df = pd.DataFrame(dict(r=list(features.values()), theta=list(features.keys())))
    fig = px.line_polar(
        df, r="r", theta="theta", line_close=True, width=700, height=700, range_r=[0, 1]
    )
    fig.update_traces(fill="toself")
    graph_div = plotly.offline.plot(fig, auto_open=False, output_type="div")

    return graph_div


def get_overlay_polar_graph(features):
    # Return overlay polar graph from a list of dicts of audio features
    categories = ["valence", "energy", "danceability", "instrumentalness"]

    fig = go.Figure()

    data = {"r": [], "theta": [], "set": []}
    for i, feature in enumerate(features):
        data["r"].extend(list(feature.values()))
        data["theta"].extend(list(feature.keys()))
        data["set"] += [str("set" + str(i))] * len(feature)

    df = pd.DataFrame(data=data)

    fig = px.line_polar(
        df,
        r="r",
        theta="theta",
        color="set",
        line_close=True,
        width=700,
        height=700,
        range_r=[0, 1],
    )

    fig.update_traces(fill="toself")

    graph_div = plotly.offline.plot(fig, auto_open=False, output_type="div")
    return graph_div


# endregion

"""
Un-cache-able parts: recent songs+ rec based on recent songs

Cache-able parts: everything else
Direction: Create a model with all fields needed to be cache
Save user's uri + time the data was initially cached
=> re-fetch every 2 weeks?

Just plain model should work.

Doesn't have to worry about unauthorized users because /analysis/ is redirected from 
callback url
"""


def get_song_recommendations(sp, seed_artists, seed_genres, seed_tracks):
    """ Return a list of dictionaries with:
        - Songs rec that appear in artist based, genres based, tracks based 
            rec function
        - Songs that appear multiple times in each rec function
    """

    common_rec = {}
    rec = {}
    artist_based_rec = sp.recommendations(seed_artists=seed_artists, limit=100)
    # Note: If user's genres are too niche, there may not be any genres-based rec
    genre_based_rec = sp.recommendations(seed_genres=seed_genres, limit=100)
    track_based_rec = sp.recommendations(seed_tracks=seed_tracks, limit=100)

    for items in zip_longest(
        artist_based_rec["tracks"],
        genre_based_rec["tracks"],
        track_based_rec["tracks"],
    ):
        # Track info
        for item in items:
            if item is not None:
                track = __parse_track(item)
                if (track["name"]) not in rec and len(rec) < 10:
                    rec[track["name"]] = track
                else: common_rec[track["name"]] = track
    
    print(common_rec)

    return [rec, common_rec]
