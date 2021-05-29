from collections import Counter
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import plotly
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from itertools import zip_longest
import itertools
import datetime

# region Authentication...
client_id = "190c59b4f1074e82bdb56ae09547ab22"
client_secret = "4391e01cc3ee4baa8ce7e591b39d980c"
redirect_uri = "https://musiztaste.herokuapp.com/callback/"

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
    else:
        return None


def get_top_tracks(sp):
    """Return current user's top 10 tracks, along with
        - top artists
        - top albums
        - year most of the tracks are from
    accquired through top 100 tracks/ however many top tracks available
    """
    data = {"tracks": [], "uri": [], "artists": [], "albums": {}, "year_released": []}
    artists = []
    albums = {}
    year_released = []

    # Loop to get all top tracks
    offset = 0
    while True:
        results = sp.current_user_top_tracks(
            time_range="long_term", limit=50, offset=offset
        )

        # Get top tracks in long/med/short term time frame
        if not results["items"]:
            break
        else:
            try:
                med_term = sp.current_user_top_tracks(
                    time_range="medium_term", limit=50, offset=offset
                )
                results["items"].extend(med_term["items"])

                short_term = sp.current_user_top_tracks(
                    time_range="short_term", limit=50, offset=offset
                )

                results["items"].extend(short_term["items"])
            except TypeError:
                pass

        for item in results["items"]:
            data["uri"].append(item["uri"])
            track = __parse_track(item)
            # Only get album name if it's not a 'single'
            if item["album"]["album_type"] != "SINGLE":
                album = item["album"]["name"]
                if album in albums:
                    albums[album]["times_appear"] += 1
                else:
                    albums[album] = {
                        "name": album,
                        "images": track["images"],
                        "times_appear": 1,
                        "url": item["album"]["external_urls"]["spotify"],
                    }
            else:
                album = "single"

            # Track info
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

    year_released = [
        {"year": item[0], "times_appear": item[1]}
        for item in Counter(year_released).most_common()
    ]

    data["tracks"] = (
        data["tracks"][:10] + data["tracks"][100:110] + data["tracks"][200:210]
    )
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
                top_playlist_url = item["external_urls"]["spotify"]

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

    # Get top playlist durations in hours+minutes from miliseconds
    duration = datetime.timedelta(minutes=int(duration / 1000 / 60))
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 60 * 60)
    minutes = int(remainder / 60)

    if hours == 0:
        duration_str = "{} minutes".format(minutes)
    else:
        duration_str = "{} hours {} minutes".format(hours, minutes)

    top_playlist = {
        "name": top_playlist_name,
        "duration": duration_str,
        "track_count": most_track_count,
        "image": sp.playlist_cover_image(playlist_id=top_playlist_uri),
        "uris": non_local_tracks,
        "local_tracks": local_track,
        "common_date_added": Counter(date_added).most_common(1),
        "url": top_playlist_url,
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

    recent_tracks = sp.current_user_recently_played(limit=50)
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


def get_audio_features(sp, uri):
    """Get average audio features of a set of tracks"""
    __audio_features = {
        "valence": 0,
        "energy": 0,
        "instrumentalness": 0,
        "danceability": 0,
        "acousticness": 0,
    }

    audio_features = []

    if len(uri) < 100:
        audio_features = sp.audio_features(uri[:100])
    else:
        for i in range(0, int(len(uri) / 10)):
            audio_features.extend(sp.audio_features(uri[(100 * i) : (100 * (i + 1))]))

    for feature in audio_features:
        if feature is not None:
            __audio_features["valence"] += float(feature["valence"])
            __audio_features["energy"] += float(feature["energy"])
            __audio_features["instrumentalness"] += float(feature["instrumentalness"])
            __audio_features["danceability"] += float(feature["danceability"])
            __audio_features["acousticness"] += float(feature["acousticness"])

    __audio_features["valence"] /= len(uri)
    __audio_features["energy"] /= len(uri)
    __audio_features["danceability"] /= len(uri)
    __audio_features["instrumentalness"] /= len(uri)
    __audio_features["acousticness"] /= len(uri)

    return __audio_features


def get_top_artists(sp):
    """Get top artists and top genres"""
    data = {
        "artists": [],
        "genres": [],
        "uri": [],
        "avrg_popularity": 0,
        "pop_rate": "",
    }
    genres = []
    offset = 0

    while True:
        results = sp.current_user_top_artists(
            time_range="long_term", limit=50, offset=offset
        )

        if not results["items"]:
            break
        else:
            try:
                med_term = sp.current_user_top_artists(
                    time_range="medium_term", limit=50, offset=offset
                )
                results["items"].extend(med_term["items"])

                short_term = sp.current_user_top_artists(
                    time_range="short_term", limit=50, offset=offset
                )

                results["items"].extend(short_term["items"])
            except TypeError:
                pass

        # Get first 10 top artists and list of genres of all top artists
        for i, item in enumerate(results["items"]):
            if i < 30:
                artist = {
                    "name": item["name"],
                    "images": item["images"][0]["url"],
                    "url": item["external_urls"]["spotify"],
                }
                if artist not in data["artists"]:
                    data["artists"].append(artist)
                    data["avrg_popularity"] += item["popularity"]

            data["uri"].append(item["uri"])
            genres.extend(item["genres"])

        offset += 50

    # Top 5 genres
    genres = Counter(genres).most_common(5)
    data["genres"] = genres
    data["avrg_popularity"] = int(data["avrg_popularity"] / len(data["artists"]))

    if 0 < data["avrg_popularity"] < 20:
        data["pop_rate"] = "your music tatse is extremely obscure."
    elif 20 < data["avrg_popularity"] < 40:
        data[
            "pop_rate"
        ] = "you probably think of yourself as very quirky. That may be true, may be not."
    elif 40 < data["avrg_popularity"] < 70:
        data["pop_rate"] = "your taste is right in the middle... Kinda centrist."
    else:
        data["pop_rate"] = "you are a total normie."
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
    categories = [
        "valence",
        "energy",
        "danceability",
        "instrumentalness",
        "acousticness",
    ]

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
    """Return a dict with song recommendations
    NOTE: method returns different output each time
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
                else:
                    common_rec[track["name"]] = track

    if len(common_rec) < 10:
        return dict(itertools.islice((common_rec.update(rec)).items(), 10))
    else:
        return dict(itertools.islice(common_rec.items(), 10))
