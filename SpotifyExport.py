from spotipy.oauth2 import SpotifyOAuth
import spotipy
import settings
import html
from urllib.parse import urlparse


class Spotify:
    def __init__(self):
        conf = settings['spotify']
        client_credentials_manager = SpotifyOAuth(client_id=conf['client_id'], client_secret=conf['client_secret'], scope="user-library-read", redirect_uri="http://localhost")
        self.api = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def getSpotifyPlaylist(self, url):
        playlistId = get_id_from_url(url)
        if len(playlistId) != 22:
            raise Exception('Bad playlist id: ' + playlistId)

        results = self.api.playlist(playlistId)
        name = results['name']
        total = int(results['tracks']['total'])
        tracks = build_results(results['tracks']['items'])
        count = len(tracks)
        print(f"Spotify tracks: {count}/{total}")

        while count < total:
            more_tracks = self.api.playlist_items(playlistId, offset=count, limit=100)
            tracks += build_results(more_tracks['items'])
            count = count + 100
            print(f"Spotify tracks: {len(tracks)}/{total}")

        return {'tracks': tracks, 'name': name, 'description': html.unescape(results['description'])}

    def getSpotifyLikedTracks(self):
        results = []
        playlists = self.api.current_user_saved_tracks(20)
        while playlists:
            for i, playlist in enumerate(playlists['items']):

                result = build_result(playlist);

                results.append(result)

            if playlists['next']:
                playlists = self.api.next(playlists)
            else:
                playlists = None

        return results

    def getUserPlaylists(self, user):
        pl = self.api.user_playlists(user)['items']
        count = 1
        more = len(pl) == 50
        while more:
            results = self.api.user_playlists(user, offset=count * 50)['items']
            pl.extend(results)
            more = len(results) == 50
            count = count + 1

        return [p for p in pl if p['owner']['id'] == user and p['tracks']['total'] > 0]

    def get_tracks(self, url):
        tracks = []
        url_parts = parse_url(url)
        path = url_parts.path.split('/')
        id = path[2]
        if 'album' == path[1]:
            album = self.api.album(id)
            tracks.extend(build_results(album['tracks']['items'], album['name']))
        elif 'track' == path[1]:
            track = self.api.track(id)
            tracks.extend(build_results([track]))
        return tracks


def build_results(tracks, album=None):
    results = []
    for track in tracks:

        result = build_result(track, album)

        if result is not None:
            results.append(result)

    return results

def build_result(track, album=None):
    if 'track' in track:
        track = track['track']
    
    album_name = album if album else track['album']['name']

    return {
        'artist': ' '.join([artist['name'] for artist in track['artists']]),
        'name': track['name'],
        'album': album_name,
        'duration': track['duration_ms']/1000
    }


def get_id_from_url(url):
    url_parts = parse_url(url)
    return url_parts.path.split('/')[2]


def parse_url(url):
    return urlparse(url)
