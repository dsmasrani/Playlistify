from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from app import *
from Playlistify import *


app = Flask(__name__)


app.secret_key = "nhi8yi34e"  # something random
app.config['SESSION_COOKIE_NAME'] = 'Sans Cookie'

TOKEN_INFO = "token_info"

done_message = 'Done!'
done_message_two = 'This playlist has been made in your Spotify Account!'


@app.route('/')
def homepage():
    return render_template('homepage.html')
    #return 'hi'

@app.route('/san_login')
def san_login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    session.clear()
    return redirect(auth_url)


@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('home', _external=True))


@app.route('/home')
def home():
    return render_template('san_home.html')

# dev's below

@app.route('/dev_login')
def main():
    return render_template('dev_home.html')

@app.route('/login')
def dev_login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    session.pop('TOKEN_INFO',None)
    return redirect(auth_url)

@app.route('/dev_redirect')
def dev_redirectPage():
    sp_oauth = create_spotify_oauth()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['TOKEN_INFO'] = token_info
    return redirect(url_for('options', _external=True))

@app.route('/options')
def options():
    return render_template('options.html')