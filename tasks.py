from celery import Celery
from model import Model
from playlist_creation import Playlist
import time

# Instantiating Celery Object 
app = Celery()
app.config_from_object("celery_settings")

@app.task(bind=True)
def run_model(self, access_code):

    rf_model = Model(access_code)

    self.update_state(state='PROGRESS',meta={'status': "Retrieving 'Liked' Songs"})
    rf_model.df = rf_model.get_saved_songs() # Retrieving Songs
    time.sleep(5)

    self.update_state(state='PROGRESS',meta={'status': "Labeling Favorite Songs"})
    rf_model.classified_df = rf_model.classify_songs() # Labeling Favorite Songs
    time.sleep(5)

    self.update_state(state='PROGRESS',meta={'status': "Training Model..."})
    rf_model.recommendations = rf_model.fitting() # Training Model
    self.update_state(state='PROGRESS',meta={'status': "Predicting Songs"})
    time.sleep(5)
    self.update_state(state='SUCCESS',meta={'status': "Model Complete."})
    return "Model Complete."

@app.task(bind=True)
def create_playlist(self, access_code):
    pl_creation = Playlist(access_code)
    pl_creation.tuples = pl_creation.song_names()
    pl_creation.user_id = pl_creation.get_id()
    pl_creation.add_to_playlist()
    return "Created Playlist."