import pandas as pd
import requests
import numpy as np
from imblearn.over_sampling import SMOTE
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split


class Temp:

    def __init__(self, token):
        self.token = token
        self.features = pd.read_csv("/home/isac738/song-recommender-app/SpotifyFeatures.csv")
        self.json = self.get_saved_songs()
        self.df = self.get_songs()
        self.classified_df = self.classify_songs()
        self.features_name, self.balanced_classified_df = self.cleaning()
        self.recommendations = self.fitting()

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
    def get_songs(self):
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

    # Step 3: Classify Songs as Favorite in SpotifyFeatures dataset
    def classify_songs(self):
        # Create 'favorite' column (favorite = 1, not favorite = 0)
        self.features['same_artists'] = self.features.artist_name.isin(self.df.artist)
        self.features['same_track'] = self.features.track_name.isin(self.df.track)
        self.features["favorite"] = np.where((self.features["same_artists"] == True) & (self.features["same_track"] == True), 1,
                                        0)  # If both instances are True.
        classified = self.features.drop(["same_artists", "same_track"], axis=1)
        return classified

    # Step 4: Data Cleaning / Pre-processing
    def cleaning(self):
        # Removing comedy
        self.classified_df = self.classified_df[self.classified_df.genre != 'Comedy']
        df_copy = self.classified_df.copy()
        df_copy.drop(columns='track_name', inplace=True)
        # Using SMOTE
        X = df_copy.drop(columns=['favorite', 'genre', 'artist_name', 'key', 'mode', 'time_signature','track_id'])
        y = df_copy.favorite
        oversample = SMOTE()
        X, y = oversample.fit_resample(X, y)
        X['favorite'] = y
        X.head()
        c = X.corr()
        features = c.loc['favorite', :]
        return features[features > .2].index, X

    # Step 5: Model Fitting
    def fitting(self):
        # Train-Split
        X_train, X_test, y_train, y_test = train_test_split(self.balanced_classified_df[self.features_name].drop(columns='favorite'), self.balanced_classified_df.favorite, test_size=.20)
        dt = DecisionTreeClassifier(max_depth=30)
        dt.fit(X_train, y_train)
        final_prediction = dt.predict(self.classified_df[self.features_name].drop(columns='favorite'))
        self.classified_df['prediction'] = final_prediction
        self.classified_df = self.classified_df[(self.classified_df['favorite'] == 0) & (self.classified_df['prediction'] == 1)]
        print(self.classified_df[['track_name','artist_name','genre']])
        return self.classified_df[['track_name','artist_name','genre']]

        ## Idea: if F1 score is less than certain value, then return "not enough data" error

    # Step 6: Converting df to Spotify playlist
    








