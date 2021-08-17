# Importing libraries
import pandas as pd
import requests
import json


class Playlist: 
   
    # Initializing Class 
    def __init__(self, token):
        self.token = token
        self.recommendations = pd.read_csv("recommendations.csv")

    # Step 1: Get list of tuples containing song and artist names from csv file.
    def song_names(self):
        df = self.recommendations
        tuple_list = list(zip(df.track_name, df.artist_name))
        return tuple_list

    # Step 2: Get user ID
    def get_id(self):
        query = "https://api.spotify.com/v1/me"
        response = requests.get(
            query,
            headers={
                "Authorization": "Bearer {}".format(self.token)
            }
        )
        response_json = response.json()
        return response_json['id']

    # Helper Function: Creating playlist on Spotify
    def create_playlist(self):
        request_body = json.dumps({
            "name": "What's Popping? - Recommendations",
            "description": "brand new whip just hopped in.",
            "public": True
        })
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.token)
            }
        )
        response_json = response.json()
        # playlist id
        return response_json["id"]

    # Helper Function: Get each song's Spotify uri
    def get_spotify_uri(self, song, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}&type=track&offset=0&limit=1".format(song, artist)
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # URI
        uri = songs[0]["uri"]
        return uri

    # Step 3: Add songs to Spotify Playlist
    def add_to_playlist(self):
        uris = []

        # Loop through tuples and get URIs
        for i, j in self.tuples:
            try:
                uris.append(self.get_spotify_uri(i, j))
            except:
                "Song not found!"

        # Create new playlist
        playlist_id = self.create_playlist()

        # Populate playlist
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.token)
            }
        )
        response_json = response.json()
        return response_json

# if __name__ == "__main__":
#     token = "BQD9swEuvr3V4bMtiqcUSlopVa5WuzTLln_CRODBaJKyrsVkukf8ZnvAPXOt3D1JHwWTIHn8tkmqqBUfytDm-nIGTxr4crACOfGakfz-IcqFGGmxBb8qz7KjwP2mv2Bz4XIQms1g2RWgORHmQ-50AxZcmgwbsItY2og_vy4ppco7TMf4Y3lz0y33V2u4j68HifdY174qj5wnAyLW2RKCnRaWArLLTycSrMAvd6W75JzGmLg"
#     playlist = Playlist(token)
#     playlist.tuples = playlist.song_names()
#     playlist.user_id = playlist.get_id()
#     playlist.add_to_playlist()

