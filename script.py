import pandas as pd
import requests
import numpy as np
from imblearn.over_sampling import SMOTENC
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import json


class Temp:

    def __init__(self, token):
        self.token = token
        self.features = pd.read_csv("data/SpotifyFeatures.csv")

    # Step 1: Get "Saved Songs" data.
    def get_saved_songs(self):
        query = "https://api.spotify.com/v1/me/tracks?offset=0&limit=50"
        response = requests.get(
            query,
            headers={
                "Authorization": "Bearer {}".format(self.token)
            }
        )
        response_json = response.json()
        return response_json

    # Step 2: Get Artist Name and Song Name
    def get_info(self):
        tracks = []
        artists = []
        for i in self.json['items']:
            song = i['track']['name']
            artist = i['track']['album']['artists'][0]['name']
            tracks.append(song)
            artists.append(artist)
        # Creating dataframe
        df = pd.DataFrame(list(zip(tracks, artists)), columns=['track', 'artist'])
        return df

    # Step 3: Classify Songs as Favorite in SpotifyFeatures.csv
    def classify_songs(self):
        # Create 'favorite' column (favorite = 1, not favorite = 0)
        self.features['same_artists'] = self.features.artist_name.isin(self.df.artist)
        self.features['same_track'] = self.features.track_name.isin(self.df.track)
        self.features["favorite"] = np.where(
            (self.features["same_artists"] == True) & (self.features["same_track"] == True), 1,
            0)
        # If both instances are True.
        classified_df = self.features.drop(["same_artists", "same_track"], axis=1)
        return classified_df

    # Step 4: Cleaning / Model Fitting
    def fitting(self):

        # Getting only relevant features
        df_copy = self.classified_df[
            ['genre', 'popularity', 'danceability', 'instrumentalness', 'favorite']].copy()

        # Train/Split Data
        X_train, X_test, y_train, y_test = train_test_split(df_copy.drop(columns='favorite'), df_copy.favorite,
                                                            test_size=.20)
        # SMOTE-ENC
        smote_nc = SMOTENC(categorical_features=[0], random_state=0)
        X_resampled, y_resampled = smote_nc.fit_resample(X_train, y_train)
        X_re_test, y_re_test = smote_nc.fit_resample(X_test, y_test)

        # Pipeline
        cat_feats = ['genre']
        cat_transformer = Pipeline([
            ('one-hot', OneHotEncoder())
        ])
        preproc = ColumnTransformer(transformers=[('cat', cat_transformer, cat_feats)], remainder='passthrough')

        # Model
        lr = Pipeline(steps=[('preprocessor', preproc), ('LogReg', LogisticRegression(max_iter=1000))])
        lr.fit(X_resampled, y_resampled)
        test_preds = lr.predict(X_re_test)

        # Getting F1 score to show User their accuracy score
        f1 = f1_score(y_re_test, test_preds)

        # Getting Predictions
        preds = lr.predict(self.classified_df[
                               ['genre', 'popularity', 'danceability', 'instrumentalness',
                                'favorite']])
        self.classified_df['preds'] = preds
        self.classified_df = self.classified_df[(self.classified_df['favorite'] == 0) & (self.classified_df['preds'] == 1)]
        return self.classified_df[['track_name', 'artist_name', 'genre']].sample(n=20), f1  # returning only 20 songs and f1 score
        # return "hello","bob"

    # Step 5: Get list of tuples containing song and artist names from csv file.
    def song_names(self):
        df = self.recommendations
        tuple_list = list(zip(df.track_name, df.artist_name))
        return tuple_list

    # Step 6: Get user ID
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

    # Step 7: Create playlist in Spotify.
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

    # Step 9: Add songs to Spotify Playlist
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
