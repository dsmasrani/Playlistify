import spotipy
from flask import Flask, request, url_for, session, redirect, render_template
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from UserTopAnalyzer.Secrets import *
import time
import os
scope = 'user-top-read playlist-modify-public'
redirect_uri = 'http://127.0.0.1:5000/redirect'
print('Hi! Welcome to Playlistify. I will need access to your account to analyze your listening behavior and generate a playlist full of your past favorite songs!')
print('Your songs will be split into thirds by most recent favorites, recents from the past 6 months, and of all time in order by listening time')
client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
#code = request.args.get(['code'])
#sp.current_user_top_artists(time_range='long_term')
#def Client(track_id):
#    auth_manager = SpotifyClientCredentials(client_id,client_secret)
#    sp = spotipy.Spotify(auth_manager=auth_manager)
    #sp1 = spotipy.Spotify(auth_manager=SpotifyOAuth(username='firebreather3000',scope = scope,client_id=client_id,client_secret=client_secret,redirect_uri=redirect_uri))
#    topartist = sp.current_user_top_artists(time_range='short_term', limit=10)
    #topsongs = sp1.current_user_top_tracks(time_range='short_term', limit=1)
#    for item in topartist['items']:
#        print(item['name'])
#    print(topartist['items'][0]['name'])
#print(Client('6m8SIT10j41SPpPFOknTmP'))

def getTopArtist(index, limit):
    length = ['short_term', 'medium_term', 'long_term']
    token_info = get_token()
    sp1 = spotipy.Spotify(auth=token_info['access_token'])
    topartist = sp1.current_user_top_artists(time_range=length[index], limit=limit)
    return topartist

def getTopSongs(index, limit):
    length = ['short_term', 'medium_term', 'long_term']
    token_info = get_token()
    sp1 = spotipy.Spotify(auth=token_info['access_token'])
    topsongs = sp1.current_user_top_tracks(time_range=length[index], limit=limit)
    return topsongs
def generatePlaylist(name = 'Your Top Songs',description = 'Generated with love by Playlistify'):
    token_info = get_token()
    sp1 = spotipy.Spotify(auth=token_info['access_token'])
    sp1.user_playlist_create(user=get_user_id(), name=name, description=description)

def getPlaylistID():
    token_info = get_token()
    sp1 = spotipy.Spotify(auth=token_info['access_token'])
    user_playlist = sp1.user_playlists(user=get_user_id() , limit=1 , offset=0)
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

def addSongs(item):
    token_info = get_token()
    sp1 = spotipy.Spotify(auth=token_info['access_token'])
    sp1.playlist_add_items(playlist_id=getPlaylistID(),items=item)


def create_spotify_oauth():  # import client Id and client secret from the secrets file
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('dev_redirectPage', _external=True),  # url_for is good to make the url short
        #redirect_uri=redirect_uri,
        # external=True will create an absolute path
        scope=scope  # change scope to user-library-read if it doesn't work
    )

def create_spotify_oauth2():  # import client Id and client secret from the secrets file
    return SpotifyOAuth(
        username=get_user_id(),
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('dev_redirectPage', _external=True),  # url_for is good to make the url short
        #redirect_uri=redirect_uri,
        # external=True will create an absolute path
        scope=scope  # change scope to user-library-read if it doesn't work
    )

def get_token():
    token_info = session.get('TOKEN_INFO', None)  # if the value doesn't exist turn none
    if not token_info:
        return redirect(url_for('/'))
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60  # if token expiration time is past 60 seconds then refresh it
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def get_user_id():
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return str(sp.me()['id'])

app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_COOKIE_NAME'] = 'Playlistify'
TOKEN_INFO = 'a47a9l'
done_message='Done!'
done_message_two='This playlist has been made in your Spotify Account!'


@app.route('/result',methods=['POST', 'GET'])
def result():
    try:
        generatePlaylist(request.form['playlist_name'],request.form['playlist_description'])
    except:
        return render_template('options.html', error_message_artists='Make sure to fill out all Boxes!')
    try:
        numsongs = int(request.form['number_of_songs'])
    except:
        return render_template('options.html', error_message_artists='Make sure to fill out all Boxes!')
    try:
        option = int(request.form['option'])
    except:
        return render_template('options.html', error_message_artists='Make sure to fill out all Boxes!')
    if(numsongs < 3):
        numsongs = 3
    if(numsongs > 100):
        numsongs = 100
    if(option == -1):
        return render_template('options.html', error_message_artists='Make sure to fill out all Boxes!')
    elif(option == 3):
        addSongs(getSongIDs(number=numsongs))
    else:
        songIDs = []
        templist = getTopSongs(option, numsongs)
        for song in templist['items']:
            id = song['id']
            songIDs.append(id)
        addSongs(songIDs)
    i_frame_url = "https://open.spotify.com/embed/playlist/" + str(getPlaylistID())
    #return request.form['option']
    return render_template('result.html', thing_one=done_message, thing_two=done_message_two, i_frame_url=i_frame_url)
