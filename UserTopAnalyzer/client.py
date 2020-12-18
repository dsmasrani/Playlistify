from UserTopAnalyzer.Playlistify import *

def main():
    print_topsongs()
    generatePlaylist('Top Listened Songs70')
    print(getPlaylistID())
def print_topsongs():
    user_topArtists = getTopArtist(2,10)
    user_topSongs = getTopSongs(2,3)
    playlistid = []
    for song in user_topSongs['items']:
        name = song['name']
        artists = song['artists']
        playlistid.append(song['id'])
        artistlist = []
        for artist in artists:
            artistlist.append(artist['name'])
        print(str(name) + " " + str(artistlist))

def print_playlistinfo(playlist_id):
    playlist_data = getTrackIDs(username,playlist_id)
    print('len of playlist:' + playlist_data)
    print(playlist_data)


    #sp1.user_playlist_add_tracks()
if __name__ == "__main__":
    # execute only if run as a script
    main()
