# Import packages 
from flask import Flask, request, redirect, render_template, url_for, session, jsonify
from secrets import CLIENT_ID, CLIENT_SECRET
from urllib.parse import quote
from tasks import run_model, create_playlist
import requests
import json


# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)
# Server-side Parameters
REDIRECT_URI = "http://www.whatspopping.xyz/callback/q"
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()
# In dict
auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "state": STATE,
    "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

# Instantiating Flask Object
app = Flask(__name__)
app.secret_key = "SECRET_KEY"

@app.route("/")
def home():
    # Home Page 
    return render_template('index.html')

@app.route("/login")
def index():
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/callback/q")
def callback():
    # Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    session['access_token'] = access_token
    return render_template('redirect.html')

# URL to start running model. 
@app.route('/model_task', methods=['POST'])
def model_task():
    access_code = session['access_token']
    task = run_model.apply_async(kwargs={'access_code':access_code})
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}

# URL to start creating Spotify playlist. 
@app.route('/playlist_creation',methods=['POST'])
def playlist_creation():
    access_code = session['access_token']
    task = create_playlist.apply_async(kwargs={'access_code':access_code})
    return "Completed."

# This route is in charge of reporting status.
@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = run_model.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)