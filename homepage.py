'''COPYRIGHT (c) 2020,2021 SANKALP VARSHNEY

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
'''

"""
Prerequisites

    pip3 install spotipy Flask Flask-Session

    // from your [app settings](https://developer.spotify.com/dashboard/applications)
    export SPOTIPY_CLIENT_ID=client_id_here
    export SPOTIPY_CLIENT_SECRET=client_secret_here
    export SPOTIPY_REDIRECT_URI='http://127.0.0.1:8080' // must contain a port
    // SPOTIPY_REDIRECT_URI must be added to your [app settings](https://developer.spotify.com/dashboard/applications)
    OPTIONAL
    // in development environment for debug output
    export FLASK_ENV=development
    // so that you can invoke the app outside of the file's directory include
    export FLASK_APP=/path/to/spotipy/examples/app.py

    // on Windows, use `SET` instead of `export`

Run app.py

    python3 -m flask run --port=8080
    NOTE: If receiving "port already in use" error, try other ports: 5000, 8090, 8888, etc...
        (will need to be updated in your Spotify app and SPOTIPY_REDIRECT_URI variable)
"""

from flask import Flask, request, url_for, session, redirect, render_template, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask_mail import Message, Mail
from app import *
from app2 import *
import uuid
import os

mail = Mail()
app = Flask(__name__)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = ''
app.config["MAIL_PASSWORD"] = ''
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)
app.secret_key = 'development key'
mail.init_app(app)
global contact_redirect
contact_redirect = False
os.environ['SPOTIPY_CLIENT_ID'] = ''
os.environ['SPOTIPY_CLIENT_SECRET'] = ''
#os.environ['SPOTIPY_REDIRECT_URI'] = 'http://127.0.0.1:5000/login'
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://playlistifyer.herokuapp.com/login'

caches_folder = './.spotify_caches/' #Cache path for clearing session
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid') #Gets path

@app.route('/about')
def about():
    global contact_redirect
    contact_redirect = False
    return render_template('about.html')
@app.route('/')
def homepage():
    global contact_redirect
    contact_redirect = True
    return render_template('homepage.html')

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('home', _external=True))
@app.route('/login_dev')
def logindev():
    return redirect('/login')

@app.route('/login_san')
def loginsan():
    return redirect('/login')
@app.route('/login')
def login():
    session.clear()
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope='user-read-currently-playing playlist-modify-private user-top-read playlist-modify-public',
        cache_path=session_cache_path(),
        show_dialog=True)
    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/home')

    if not auth_manager.get_cached_token():
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return redirect(auth_url)
    return redirect('/home')

@app.route('/home')
def home():
    try:
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    except:
        return redirect('/')
    if not auth_manager.get_cached_token():
        return redirect('/')
    return render_template('home.html')

# dev's below

@app.route('/result',methods=['POST', 'GET'])
def result():
    fail = 0 #counts number of fails to prevent empty playist creation when user hastily preses go
    try:
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    except:
        return redirect('/')
    if not auth_manager.get_cached_token():
        return redirect('/') #if no login token, redirect back to root
    try:
        playlist_name = request.form['playlist_name'] #attempts to get playlist name from form
    except:
        playlist_name = "Your Top Songs" #default fallback playlist name
        fail += 1
    try:
        playlist_description = request.form['playlist_description'] #attempts to pull playlist description
        playlist_description = playlist_description + ' | Generated with love by https://playlistifyer.herokuapp.com'
    except:
        playlist_description = 'Generated with love by Playlistifyer'
        fail += 1
    try:
        numsongs = int(request.form['number_of_songs']) #attempts to get number of songs
        if (numsongs < 1):
            return render_template('home.html', error_message_top='Number of songs too low or high!',error_message_header='Number of songs too low or high!')
        if (numsongs > 100):
            numsongs = 100
        #if greater than allowed num or less than 0, give error
    except:
        fail += 1
        return render_template('home.html', error_message_top='Make sure to enter a valid number!', error_message_header='Make sure to enter a valid number!')
    #if no num, throw error
    option = int(request.form['option']) #get option from form
    if (option == -1):
        fail += 1
        return render_template('home.html', error_message_top='Please select which time period you want!', error_message_header='Please select which time period you want!') #error message
    if (fail < 4): #if all boxes r empty
        generatePlaylist(playlist_name, playlist_description) #do not generate playlist to prevent empty playlists
    if(option == 3):
        if(numsongs < 3): #if selected option 3(All of the above), has to be 3 minimum
            numsongs = 3
        addSongs(getSongIDs(number=numsongs))
    else:
        getTopSongsinPeriod(option,numsongs) #gets top songs and gives IDs for them and adds them
    #(playlist_name) #telemetry to see what people are making
    #print(playlist_description)
    #print(numsongs)
    #print(option)
    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(getPlaylistID())
    #return request.form['option']
    return render_template('result.html', thing_one='Done!', thing_two='This playlist has been made in your Spotify Account!', i_frame_url=i_frame_url)
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    contact_name = request.form['name']
    contact_email = request.form['email']
    contact_message = request.form['message']
    msg = Message('New form response from Playlistifyer', sender='dsmasrani@gmail.com',recipients=['sankalpvarshney12@gmail.com','dsmasrani@gmail.com'])
    body = 'CONTACT NAME: ' + str(contact_name) + '\n\n' + 'CONTACT EMAIL: ' + str(contact_email) + '\n' + '\n' + 'MESSAGE BODY: ' + str(contact_message)
    msg.body = body
    mail.send(msg)
    if (contact_redirect == True):
        return render_template('/homepage.html/', success_message="Email was sent! We will get back to you shortly!")

    else:
        return render_template('/about.html/', success_message="Email was sent! We will get back to you shortly!")

def generatePlaylist(name,description):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp1 = spotipy.Spotify(auth_manager=auth_manager)
    sp1.user_playlist_create(user=get_user_id(), name=name, description=description)

def get_user_id():
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp1 = spotipy.Spotify(auth_manager=auth_manager)
    return str(sp1.me()['id'])

def addSongs(item):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp1 = spotipy.Spotify(auth_manager=auth_manager)
    sp1.playlist_add_items(playlist_id=getPlaylistID(),items=item)

def getPlaylistID():
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp1 = spotipy.Spotify(auth_manager=auth_manager)
    user_playlist = sp1.user_playlists(user=get_user_id(),limit=1,offset=0)
#    for item in user_playlist:
#        print(item)
    playlist_Data = user_playlist['items'][0]
    playlist_ID = playlist_Data['id']
    return playlist_ID

def getSongIDs(number):
    songIDs = []
    number = int(number//3)
    for i in range(3):
        templist = getTopSongs(i,number)
        for song in templist['items']:
            id = song['id']
            songIDs.append(id)
    return songIDs

def getTopSongs(index, limit):
    length = ['short_term', 'medium_term', 'long_term']
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp1 = spotipy.Spotify(auth_manager=auth_manager)
    topsongs = sp1.current_user_top_tracks(time_range=length[index], limit=limit)
    return topsongs

def getTopSongsinPeriod(option,numsongs):
    songIDs = []
    templist = getTopSongs(option, numsongs)
    for song in templist['items']:
        id = song['id']
        songIDs.append(id)
    addSongs(songIDs)


@app.route('/by_categories', methods=['POST', 'GET'])
def by_categories():
    try:
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    except:
        return redirect('/')
    if not auth_manager.get_cached_token():
        return redirect('/') #if no login token, redirect back to root
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)

    playlist_name = request.form['playlist_name']
    playlist_description = request.form['playlist_description']

    # separate by commas
    category_names = request.form['genre_names']
    category_names = [x.strip() for x in category_names.split(',')]

    for i in range(len(category_names)):
        if (category_names[i].lower() == 'hip-hop'):
            category_names[i] = 'hiphop'
        if (category_names[i].lower() == 'at-home'):
            category_names[i] = 'at_home'
        if (category_names[i].lower() == 'at home'):
            category_names[i] = 'at_home'
        if (category_names[i].lower() == 'indie'):
            category_names[i] = 'indie_alt'
        if (category_names[i].lower() == 'edm'):
            category_names[i] = 'edm_dance'
        if (category_names[i].lower() == 'r&b'):
            category_names[i] = 'rnb'
        if (category_names[i].lower() == 'k-pop'):
            category_names[i] = 'kpop'
        if (category_names[i].lower() == 'christian'):
            category_names[i] = 'inspirational'
        if (category_names[i].lower() == 'in the car'):
            category_names[i] = 'in_the_car'
        if (category_names[i].lower() == 'folks & acoustic'):
            category_names[i] = 'roots'
        if (category_names[i].lower() == 'cooking & dining'):
            category_names[i] = 'dinner'

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
        # category_playlist_ids.remove('3SMjN7PQ25QcVn8XaiPvST')

        all_songs_from_playlists = []
        for x in range(int(len(category_playlist_ids))):
            try:
                all_songs_from_playlists = all_songs_from_playlists + get_playlist_songs(category_playlist_ids[x])
            except:
                pass

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
        return render_template('home.html', error_message_genres='Error! Make sure to enter the name of the genres right and separate with commas!', error_message_header='Error! Make sure to enter the name of the genres right and separate with commas!')

    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(playlist_id)
    return render_template('result.html', thing_one=done_message, thing_two=done_message_two,
                           i_frame_url=i_frame_url)

@app.route('/by_artists', methods=['POST', 'GET'])
def by_artists():
    try:
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    except:
        return redirect('/')
    if not auth_manager.get_cached_token():
        return redirect('/') #if no login token, redirect back to root
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
        return render_template('home.html', error_message_artists='Make sure to enter the name of the artist right and separate them with a comma!',
                               error_message_header='Make sure to enter the name of the artist right and separate them with a comma!')

    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(playlist_id)
    return render_template('result.html', thing_one=done_message, thing_two=done_message_two, i_frame_url=i_frame_url)


# get playlist by one track reference
@app.route('/by_one_track', methods=['POST', 'GET'])
def by_one_track():
    try:
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    except:
        return redirect('/')
    if not auth_manager.get_cached_token():
        return redirect('/') #if no login token, redirect back to root
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)

    playlist_name = request.form['playlist_name']
    playlist_description = request.form['playlist_description']

    # get user id to create playlist
    user_id = get_user_id()

    try:
        track_name = (request.form['one_track_name']).lower()

        if '-' in track_name:
            track_name = track_name.split('-')
            try:
                track_name[0] = track_name[0].strip()
            except:
                pass
            try:
                track_name[1] = track_name[1].strip()
            except:
                pass
            print(track_name[0])
            print(track_name[1])
            artist_id = get_track_artist(track_name[1])
        else:
            print('ffsdfsdfsdfsdfsd')
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
        return render_template('home.html', error_message_one_track="Cant seem to find the track! Check spelling!", error_message_header='Cant seem to find the track! Check spelling!')

    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(playlist_id)
    return render_template('result.html', thing_one=done_message, thing_two=done_message_two, i_frame_url=i_frame_url)

def get_tracks(name):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)

    artist_id = get_artist_id(name, sp)

    song_names = get_artist_songs(artist_id, sp)

    return song_names

def get_artist_id(name, sp):
    return sp.search(q=name, limit=5, offset='0', type='artist')['artists']['items'][0]['id']

def get_artist_songs(artist_id, sp):
    songs = sp.artist_top_tracks(artist_id=artist_id, country="US")['tracks']
    song_names = []
    for item in songs:
        song_names.append(item['uri'])
    return song_names

def create_user_playlist(playlist_name, playlist_description, user_id):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)
    sp.user_playlist_create(user=user_id, name=playlist_name, public=True, collaborative=False, description=(playlist_description + ' | Generated with love by http://playlistifyer.herokuapp.com'))
    return sp.user_playlists(user=user_id, limit=10, offset=0)['items'][0]['id']

def populate_playlist(song_uris,playlist_id):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)
    sp.playlist_add_items(playlist_id=playlist_id, items=song_uris, position=None)

def get_track_artist(track_name):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return str(sp.search(q=track_name, limit=5, offset=0, type='track')['tracks']['items'][0]['album']['artists'][0]['uri'])

def get_related_artists(artist_id):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)
    total_related_artists = sp.artist_related_artists(artist_id=artist_id)['artists']
    total_artist_uris = []
    for artist in total_related_artists:
        total_artist_uris.append(artist['uri'])
    return total_artist_uris

def get_category_playlist_id(category_id):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)
    total_playlists = sp.category_playlists(category_id=category_id, limit=10, offset=0)['playlists']['items']
    total_ids = []
    for item in total_playlists:
        total_ids.append(item['id'])
    return total_ids

def get_playlist_songs(playlist_id):
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    sp = spotipy.Spotify(auth_manager=auth_manager)
    total_songs = sp.playlist(playlist_id=playlist_id, fields=None)['tracks']['items']
    total_song_uri = []
    for item in total_songs:
        total_song_uri.append(item['track']['uri'])

    return total_song_uri




