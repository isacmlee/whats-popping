# Importing libraries
import pandas as pd
import requests
import numpy as np
from imblearn.over_sampling import SMOTENC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import json


class Model:

    def __init__(self, token):
        self.token = token
        self.features = pd.read_csv("data/SpotifyFeatures.csv")

    # Step 1: Get "Saved Songs" and add to Pandas Dataframe 
    def get_saved_songs(self):
        # Initial request to start while loop 
        query = f"https://api.spotify.com/v1/me/tracks?offset=0&limit=50"
        response = requests.get(
            query,
            headers={
                "Authorization": "Bearer {}".format(self.token)
            }
        )
        response_json = response.json()
        df = self.get_info(response_json)
        # as long as df rows isn't less than 50, keep sending requests to retrieve "liked songs"
        final_df = df.copy()
        offset = 50 

        while df.shape[0] == 50: 
            query = f"https://api.spotify.com/v1/me/tracks?offset={offset}&limit=50"
            response = requests.get(
                query,
                headers={
                    "Authorization": "Bearer {}".format(self.token)
                }
            )
            temp_json = response.json()
            df = self.get_info(temp_json)
            final_df = final_df.append(df)
            offset+=50 

        return final_df

    # Function inside get_saved_songs()
    def get_info(self, response_json):
        tracks = []
        artists = []
        album_cover_urls = []
        preview_urls = []
        for i in response_json['items']:
            song = i['track']['name']
            artist = i['track']['album']['artists'][0]['name']
            album_cover_url = i['track']['album']['images'][0]['url']
            preview_url = i['track']['preview_url']
            tracks.append(song)
            artists.append(artist)
            album_cover_urls.append(album_cover_url)
            preview_urls.append(preview_url)

        # Creating dataframe
        df = pd.DataFrame(list(zip(tracks, artists)), columns=['track', 'artist'])
        df['album_cover_url'] = album_cover_urls
        df['preview_url'] = preview_urls
        return df

    # Step 2: Classify Songs as Favorite in SpotifyFeatures.csv
    def classify_songs(self):
        # Create 'favorite' column (favorite = 1, not favorite = 0)
        self.features['same_artists'] = self.features.artist_name.isin(self.df.artist)
        self.features['same_track'] = self.features.track_name.isin(self.df.track)
        self.features["favorite"] = np.where((self.features["same_artists"] == True) & (self.features["same_track"] == True), 1,0)
        # If both instances are True.
        classified_df = self.features.drop(["same_artists", "same_track"], axis=1)
        return classified_df


    # Step 3: Cleaning / Model Fitting
    def fitting(self):
        # Getting only relevant features
        df_copy = self.classified_df[
            ['genre', 'popularity', 'danceability', 'instrumentalness', 'favorite']].copy()

        # Train/Split Data
        X_train, X_test, y_train, y_test = train_test_split(df_copy.drop(columns='favorite'), df_copy.favorite, test_size=.20)

        # SMOTE-ENC
        smote_nc = SMOTENC(categorical_features=[0],k_neighbors=3)
        X_resampled, y_resampled = smote_nc.fit_resample(X_train, y_train)
        X_re_test, y_re_test = smote_nc.fit_resample(X_test, y_test)

        # Pipeline
        cat_feats = ['genre']
        cat_transformer = Pipeline([
            ('one-hot', OneHotEncoder())
        ])
        preproc = ColumnTransformer(transformers=[('cat', cat_transformer, cat_feats)], remainder='passthrough')

        # Model
        rf = Pipeline(steps=[('preprocessor', preproc), ('RandomForest', RandomForestClassifier(n_estimators=5))])
        rf.fit(X_resampled, y_resampled)
        test_preds = rf.predict(X_re_test)

        # Getting F1 score to show User their accuracy score
        # f1 = f1_score(y_re_test, test_preds)

        # Getting Predictions
        preds = rf.predict(self.classified_df[['genre', 'popularity', 'danceability', 'instrumentalness']])
        self.classified_df['preds'] = preds
        self.classified_df = self.classified_df[(self.classified_df['favorite'] == 0) & (self.classified_df['preds'] == 1)]
        recommendations = self.classified_df[['track_name', 'artist_name', 'genre']].sample(n=10)  
        recommendations.to_csv('recommendations.csv')
        return recommendations
    

# if __name__ == "__main__":
#     token = "BQBuZ7V7_K2lOzLsLi3Wx6abBV2CkwUbGsJgYhvthO-mAdx1rad7bjU97usbH2oyWjp1x4UywhFsLt9S7PQkcGnhEVNPpS9935fqEz6CvpiqrgtqFNkmQRs6qWm_pKc-HUScE2dnHV67RcasZHLATnOJv2zHqrzDxoiYv-JtZxPe2i_qXSX2cQVHv9WS243c4og5A64sBORyahUmGkpjzOyB_Aih0Ls_PInVDWah_Qy8RXA"
#     model = Model(token)
#     model.df = model.get_saved_songs()
#     print(model.df)
#     print(model.df.preview_url.values)
#     # model.classified_df = model.classify_songs()
#     # model.recommendations = model.fitting() 
#     # print(model.recommendations)

