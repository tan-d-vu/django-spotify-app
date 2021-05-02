from collections import Counter
import spotipy
from spotipy.oauth2 import SpotifyOAuth
"""
client_id = "190c59b4f1074e82bdb56ae09547ab22"
client_secret = "4391e01cc3ee4baa8ce7e591b39d980c"
redirect_uri = "http://127.0.0.1:8000"


scope = "user-follow-read user-library-read user-library-read playlist-read-private user-read-recently-played user-top-read playlist-read-collaborative"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope=scope,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )
)


recent_songs = sp.current_user_recently_played(limit=50)

#----------------------------------------#
# Recent songs

print("Recently played: ")
recent_top_artists = {}
for idx, item in enumerate(recent_songs["items"]):
    track = item["track"]
    
    if track["artists"][0]["name"] in recent_top_artists.keys():
        recent_top_artists[track["artists"][0]["name"]] += 1
    else:
        recent_top_artists[track["artists"][0]["name"]] = 1

    if (idx < 10):
        print(idx, track["artists"][0]["name"], " – ", track["name"])

v=list(recent_top_artists.values())
k=list(recent_top_artists.keys())
print("You have been listening to a lot of " + k[v.index(max(v))])

#----------------------------------------#
# Playlists

playlists = sp.current_user_playlists(offset=0)
print("Playlists: ")
while playlists:
    for i, playlist in enumerate(playlists["items"]):
        print(
            "%d %s with %d tracks"
            % (
                i + 1 + playlists["offset"],
                playlist["name"],
                playlist["tracks"]["total"],
            )
        )
    if playlists["next"]:
        playlists = sp.next(playlists)
    else:
        playlists = None

#----------------------------------------#
# Top songs
print("Top tracks: ")
top_tracks = sp.current_user_top_tracks(time_range="long_term")
sum_track_popularity = 0

for idx, item in enumerate(top_tracks["items"]):
    track = item
    print(idx, track["artists"][0]["name"], " – ", track["name"], "Popularity: ", track["popularity"])

    sum_track_popularity += track["popularity"]

print("The average popularity of your top tracks is %d/100." % (sum_track_popularity/20))

#----------------------------------------#
# Top artists
print("Top artists: ")
top_artists = sp.current_user_top_artists(time_range="long_term")

sum_artist_popularity = 0

for idx, item in enumerate(top_artists["items"]):
    artist = item
    print(idx, artist["name"], "Popularity: ", artist["popularity"] )

    sum_artist_popularity += artist["popularity"]

print("The average popularity of your top artists is %d/100." % (sum_artist_popularity/20))
"""

def get_top_tracks(sp):
    """ Return current user's top 10 tracks, along with:
        - top artists 
        - top albums 
        - year most of the tracks are from
    """ 
    data = {'tracks': [], 'uri': [], 'artists': [], 'albums': [], 'year_released' : []}
    artists = []
    albums = []
    year_released = []

    # Loop to get all top tracks
    offset = 0
    while True:
        results = sp.current_user_top_tracks(time_range='long_term', limit=50, offset=offset)
        
        if not results['items']: 
            break

        for item in (results['items']):
            data['uri'].append(item['uri'])


            if (item['album']['album_type']!='SINGLE'):
                print(item['album']['album_type'] + " " + item['name'])
                album = item['album']['name']
                albums.append(album)
            else:
                album = ''
            track = {
                    'name': item['name'], 
                    'album': album,
                    'url': item['external_urls']['spotify'], 
                    'artists': ', '.join([i['name'] for i in item['album']['artists']]),
                    'images': item['album']['images'][0]['url'],
                    }
            artists.extend(i['name'] for i in item['album']['artists'])
            year_released.append(item['album']['release_date'][0:4])
            data['tracks'].append(track)

        
        offset+=49

    print(albums)

    # Getting most popular artists/ albums and times they appear in list
    artists = [{'artist': item[0], 'times_appear': item[1]} for item in Counter(artists).most_common()]
    albums = [{'album': item[0], 'times_appear': item[1]} for item in Counter(albums).most_common()]
    year_released = [{'year': item[0], 'times_appear': item[1]} for item in Counter(year_released).most_common()]

    data['tracks'] = data['tracks'][:10]
    data['uri'] = data['uri']
    data['artists'] = artists
    data['albums'] = albums
    data['year_released'] = year_released

    return data