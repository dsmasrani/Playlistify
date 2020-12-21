from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from app.secrets import *
import time
import random
import math
import os

app = Flask(__name__)

app.secret_key = "nhi8yi34e"  # something random
app.config['SESSION_COOKIE_NAME'] = 'Sans Cookie'

TOKEN_INFO = "token_info"

done_message='Done!'
done_message_two='This playlist has been made in your Spotify Account!'


@app.route('/')
def login():
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
    return render_template('home.html')


@app.route('/by_categories', methods=['POST', 'GET'])
def by_categories():
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])

    playlist_name = request.form['playlist_name']
    playlist_description = request.form['playlist_description']

    # separate by commas
    category_names = request.form['genre_names']
    category_names = [x.strip() for x in category_names.split(',')]

    # get user id to create playlist
    user_id = get_user_id()

    category_playlist_ids = []
    try:
        for x in range(len(category_names)):
            category_names[x] = (category_names[x].replace(" ", "")).lower()

        for x in range(len(category_names)):
            category_playlist_ids = category_playlist_ids + get_category_playlist_id(category_names[x])

        # shuffle the list to random
        random.shuffle(category_playlist_ids)

        all_songs_from_playlists = []
        for x in range(int(len(category_playlist_ids))):
            all_songs_from_playlists = all_songs_from_playlists + get_playlist_songs(category_playlist_ids[x])

        # shuffle the list to random
        random.shuffle(all_songs_from_playlists)

        if len(all_songs_from_playlists) > 100:
            cut_down = len(all_songs_from_playlists) - 100
            cut_songs_from_playlists = all_songs_from_playlists[cut_down:]
        else:
            cut_songs_from_playlists = all_songs_from_playlists

        playlist_id = create_user_playlist(playlist_name, playlist_description, user_id)
        populate_playlist(cut_songs_from_playlists, playlist_id)

    except:
        return render_template('home.html', error_message_genres='Error! Make sure to enter the name of the '
                                                                 'genres right and separate with commas!')

    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(playlist_id)
    return render_template('result.html', thing_one=done_message, thing_two=done_message_two,
                           i_frame_url=i_frame_url)


@app.route('/by_artists', methods=['POST', 'GET'])
def by_artists():
    playlist_name = request.form['playlist_name']
    playlist_description = request.form['playlist_description']

    artists_names = (request.form['artists_names']).lower()
    #  the name with commas and spaces
    artists_names = [x.strip() for x in artists_names.split(',')]

    # get user id to create playlist
    user_id = get_user_id()

    # create list for all the songs
    artist_songs_uris = []
    try:
        # for every artist, get the uri's of their songs
        for x in range(len(artists_names)):
            artist_songs_uris = artist_songs_uris + get_tracks(artists_names[x])

        # shuffle the list to random
        random.shuffle(artist_songs_uris)

        # create the playlist and populate with the list songs
        playlist_id = create_user_playlist(playlist_name, playlist_description, user_id)
        populate_playlist(artist_songs_uris, playlist_id)
    except:
        return render_template('home.html', error_message_artists='Make sure to enter the name of the artist right'
                                                                  'and separate them with a comma!')
    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(playlist_id)
    try:
        os.remove('.cache')
    except:
        pass
    return render_template('result.html', thing_one=done_message, thing_two=done_message_two, i_frame_url=i_frame_url)


# get playlist by one track reference
@app.route('/by_one_track', methods=['POST', 'GET'])
def by_one_track():
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])

    playlist_name = request.form['playlist_name']
    playlist_description = request.form['playlist_description']

    # get user id to create playlist
    user_id = get_user_id()

    try:
        track_name = (request.form['one_track_name']).lower()
        artist_id = get_track_artist(track_name)

        # get the related artist's uris
        related_artists = get_related_artists(artist_id)

        # add the songs from the related artists to a list
        related_artists_songs = []
        for x in range(len(related_artists)):
            related_artists_songs = related_artists_songs + get_artist_songs(related_artists[x], sp)

        # shuffle the list to random
        random.shuffle(related_artists_songs)

        # since the list has 200 elements and the limit is 100, we have to cut it by half
        middle_index = len(related_artists_songs)//2
        half_artists_songs = related_artists_songs[:middle_index]

        # create the playlist and populate with the list songs
        playlist_id = create_user_playlist(playlist_name, playlist_description, user_id)
        populate_playlist(half_artists_songs, playlist_id)
    except:
        return render_template('home.html', error_message_one_track="Cant seem to find the track! Check spelling!")

    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(playlist_id)
    return render_template('result.html', thing_one=done_message, thing_two=done_message_two, i_frame_url=i_frame_url)


# helper methods below to retrieve stuff from the spotify api
def get_tracks(name):
    try:
       token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")  # back to the login page

    sp = spotipy.Spotify(auth=token_info['access_token'])

    artist_id = get_artist_id(name, sp)

    song_names = get_artist_songs(artist_id, sp)

    return song_names

def get_random_cookie():
    digits = [i for i in range(0, 10)]
    random_str = ""
    for i in range(6):
        index = math.floor(random.random() * 10)
    random_str += str(digits[index])
    return random_str

def get_user_id():
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return str(sp.me()['id'])


def get_artist_id(name, sp):
    return sp.search(q=name, limit=5, offset='0', type='artist')['artists']['items'][0]['id']


def get_artist_songs(artist_id, sp):
    songs = sp.artist_top_tracks(artist_id=artist_id, country="US")['tracks']
    song_names = []
    for item in songs:
        song_names.append(item['uri'])
    return song_names


def create_user_playlist(playlist_name, playlist_description, user_id):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    sp.user_playlist_create(user=user_id, name=playlist_name, public=True, collaborative=False, description=playlist_description)
    return sp.user_playlists(user=user_id, limit=10, offset=0)['items'][0]['id']


def populate_playlist(song_uris,playlist_id):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    sp.playlist_add_items(playlist_id=playlist_id, items=song_uris, position=None)


def get_track_artist(track_name):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return str(sp.search(q=track_name, limit=5, offset=0, type='track')['tracks']['items'][0]['album']['artists'][0]['uri'])

def get_related_artists(artist_id):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    total_related_artists = sp.artist_related_artists(artist_id=artist_id)['artists']
    total_artist_uris = []
    for artist in total_related_artists:
        total_artist_uris.append(artist['uri'])
    return total_artist_uris


def get_category_playlist_id(category_id):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    total_playlists = sp.category_playlists(category_id=category_id, limit=10, offset=0)['playlists']['items']
    total_ids = []
    for item in total_playlists:
        total_ids.append(item['id'])
    return total_ids

def get_playlist_songs(playlist_id):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    total_songs = sp.playlist(playlist_id=playlist_id, fields=None)['tracks']['items']
    total_song_uri = []
    for item in total_songs:
        total_song_uri.append(item['track']['uri'])
    return total_song_uri



def get_token():
    token_info = session.get(TOKEN_INFO, None)  # if the value doesn't exist turn none
    if(token_info == None):
        print("THERE IS NO VALUE")
    print("THIS IS TOKEN INFO" + str(token_info))
    if not token_info:
        raise Exception("exception")
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60  # if token expiration time is past 60 seconds then refresh it
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info


def create_spotify_oauth():  # import client Id and client secret from the secrets file
    return SpotifyOAuth(
        client_id=clientId,
        client_secret=clientSecret,
        redirect_uri=url_for('redirectPage', _external=True),  # url_for is good to make the url short
        # external=True will create an absolute path
        #redirect_uri='https://playlist-maker-san.herokuapp.com/redirect/',
        scope="playlist-modify-public"  # change scope to user-library-read if it doesn't work
    )
