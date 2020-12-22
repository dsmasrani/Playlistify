'''COPYRIGHT (c) 2020,2021 DEV MASRANI

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

import os
from flask import Flask, session, request, redirect, render_template
from flask_session import Session
import spotipy
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

os.environ['SPOTIPY_CLIENT_ID'] = '' #Secrets found in the secrets.py folder
os.environ['SPOTIPY_CLIENT_SECRET'] = ''
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://127.0.0.1/login'

caches_folder = './.spotify_caches/' #Cache path for clearing session
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid') #Gets path

@app.route('/')
def main():
    return render_template('home.html') #initial path
@app.route('/options')
def optionselect():
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path()) #gets token for OAuth
    if not auth_manager.get_cached_token():
        return redirect('/') #if no token, redirect back home
    return render_template('options.html') #render options.html
@app.route('/result',methods=['POST', 'GET'])
def result():
    fail = 0 #counts number of fails to prevent empty playist creation when user hastily preses go
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/') #if no login token, redirect back to root
    try:
        playlist_name = request.form['playlist_name'] #attempts to get playlist name from form
    except:
        playlist_name = "Your Top Songs" #default fallback playlist name
        fail += 1
    try:
        playlist_description = request.form['playlist_description'] #attempts to pull playlist description
        playlist_description = playlist_description + ' | Generated with love by https://Playlistify-dev.herokuapp.com'
    except:
        playlist_description = 'Generated with love by Playlistify'
        fail += 1
    try:
        numsongs = int(request.form['number_of_songs']) #attempts to get number of songs
        if (numsongs > 100 or numsongs < 1):
            return render_template('options.html', error_message_artists='Number of songs too low or high!')
        #if greater than allowed num or less than 0, give error
    except:
        fail += 1
        return render_template('options.html', error_message_artists='Make sure to enter a valid number!')
    #if no num, throw error
    option = int(request.form['option']) #get option from form
    if (option == -1):
        fail += 1
        return render_template('options.html', error_message_artists='Please select which time period you want!') #error message
    if (fail < 4): #if all boxes r empty
        generatePlaylist(playlist_name, playlist_description) #do not generate playlist to prevent empty playlists
    if(option == 3):
        if(numsongs < 3): #if selected option 3(All of the above), has to be 3 minimum
            numsongs = 3
        addSongs(getSongIDs(number=numsongs))
    else:
        getTopSongsinPeriod(option,numsongs) #gets top songs and gives IDs for them and adds them
    print(playlist_name) #telemetry to see what people are making
    print(playlist_description)
    print(numsongs)
    print(option)
    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(getPlaylistID())
    session.clear()
    #return request.form['option']
    return render_template('result.html', thing_one='Done!', thing_two='This playlist has been made in your Spotify Account!', i_frame_url=i_frame_url)

    #return 'done'
@app.route('/login')
def index():
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
        return redirect('/options')

    if not auth_manager.get_cached_token():
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return redirect(auth_url)
    return redirect('/options')

@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except TypeError:
        pass
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

@app.route('/playlists')
def playlists():
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/login')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()


@app.route('/currently_playing')
def currently_playing():
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/login')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route('/current_user')
def current_user():
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/login')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()

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

'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT", 8080)))
