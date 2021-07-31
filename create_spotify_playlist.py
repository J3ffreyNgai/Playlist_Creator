import googleapiclient.discovery
import json

import youtube_dl

from secret import spotify_id, spotify_token, api_key
from urllib.parse import urlparse, parse_qs
import requests


class CreatePlaylist:

    def __init__(self):
        self.user_id = spotify_id
        self.spotify_token = spotify_token
        self.api_key = api_key
        self.url = "https://www.youtube.com/watch?v=dY0MYPogyDs&list=PLilMZ_AoO7FsA07dzE7M9N0LkUIGX8-eH"
        self.song_info = {}
        self.cannot_find = {}

    # Gets the songs from youtube playlist
    def get_youtube_playlist(self):

        # Get the id of the url link
        query = parse_qs(urlparse(self.url).query, keep_blank_values=True)
        playlist_id = query["list"][0]
        print(playlist_id)
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=self.api_key)

        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50
        )
        response = request.execute()

        playlist_items = []
        while request is not None:
            response = request.execute()
            playlist_items += response["items"]
            request = youtube.playlistItems().list_next(request, response)

        for song in playlist_items:
            link = 'https://www.youtube.com/watch?v={}'.format(song["snippet"]["resourceId"]["videoId"])
            try:
                video = youtube_dl.YoutubeDL({}).extract_info(link, download=False)
                try:
                    name = video["track"]
                    artist = video["artist"]
                    self.song_info[song["snippet"]["title"]] = {
                        "url": link,
                        "song_name": name,
                        "artist": artist,
                        "spotify_uri": self.get_spotify_link(artist, name)
                    }
                except KeyError:
                    self.cannot_find[song["snippet"]["title"]] = {
                        "url": link
                    }
            except:
                self.cannot_find[song["snippet"]["title"]] = {
                    "url": link
                }


    # Gets the spotify link for songs using title and artist
    def get_spotify_link(self, artist, song_name):
        query = "https://api.spotify.com/v1/search?q=track:{}%20artist:{}&type=track&limit=10&offset=0".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)

            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # This will return the first track in the list of possible tracks
        return songs[0]["uri"]

    # Creates new spotify playlist
    def create_playlist(self):

        request_data = json.dumps({
            "name": "New Playlist",
            "description": "New playlist description",
            "public": True
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)

            }
        )
        response_json = response.json()

        return response_json["id"]

    # Adds songs to playlist
    def add_songs(self):
        self.get_youtube_playlist()
        uris = []
        for song,info in self.song_info.items():
            uris.append(info["spotify_uri"])

        playlist_id = self.create_playlist()

        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)

            }
        )
        response_json = response.json()
        return response_json
