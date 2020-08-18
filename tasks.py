from celery import Celery
from script import Temp
import time
app = Celery()
app.config_from_object("celery_settings")


@app.task(bind=True)
def recommending(self, access_code):
    obj = Temp(access_code)

    self.update_state(state='PROGRESS',meta={'current': 25,'total': 100,'status': "Retrieving Songs"})
    time.sleep(5)
    obj.json = obj.get_saved_songs() # Retrieving Songs
    obj.df = obj.get_info()
    self.update_state(state='PROGRESS',meta={'current': 50,'total': 100,'status': "Labeling Favorite Songs"})
    time.sleep(5)
    obj.classified_df = obj.classify_songs() # Labeling Favorite Songs
    self.update_state(state='PROGRESS',meta={'current': 75,'total': 100,'status': "Recommending Songs"})
    obj.recommendations, obj.f1score = obj.fitting() # Recommending Songs
    self.update_state(state='PROGRESS',meta={'current': 90,'total': 100,'status': "Adding to Spotify"})
    obj.tuples = obj.song_names() # Adding Recommendations to Spotify
    obj.user_id = obj.get_id()
    obj.finalized = obj.add_to_playlist()
    time.sleep(1)
    return {'current': 100, 'total': 100}

@app.task()
def playlist_preview():
    return "in progress..."
