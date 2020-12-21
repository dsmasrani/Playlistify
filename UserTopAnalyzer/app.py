from flask import Flask, request, url_for, session, redirect, render_template
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from UserTopAnalyzer import Playlistify
app = Flask(__name__)
app.secret_key = 'as8907nj'
app.config['SESSION_COOKIE_NAME'] = 'Dev Masrani'

TOKEN_INFO = 'token_info'\

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/spotify')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('home', _external=True))

@app.route('/home')
def home():
    return render_template('home.html')


def create_spotify_oauth():  # import client Id and client secret from the secrets file
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('redirectPage', _external=True),  # url_for is good to make the url short
        # external=True will create an absolute path
        scope=scope  # change scope to user-library-read if it doesn't work
    )
