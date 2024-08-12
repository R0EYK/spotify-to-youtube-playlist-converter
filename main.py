import requests
import secrets
import urllib.parse
import os
import sys # Debugging

from datetime import datetime
from flask import Flask, redirect, jsonify, session, request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Spotify API Credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
API_BASE_URL = os.getenv('API_BASE_URL')
SCOPE = os.getenv('SCOPE')

# YouTube API Credentials
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REDIRECT_URI = os.getenv('YOUTUBE_REDIRECT_URI')
YOUTUBE_AUTH_URL = os.getenv('YOUTUBE_AUTH_URL')
YOUTUBE_TOKEN_URL = os.getenv('YOUTUBE_TOKEN_URL')
YOUTUBE_SCOPES = os.getenv('YOUTUBE_SCOPES')

# Global variable
MAX_SONGS = 30 # YouTube API have some kind of a limit and I dont want to test it

class PlaylistSongs:
    def __init__(self, name, author):
        self.name = name
        self.author = author

def find_youtube_video_id(song_name, artist_name):
    search_query = f"{song_name} {artist_name}"
    
    youtube_creds = Credentials(
        token=session['youtube_access_token'],
        refresh_token=session['youtube_refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=YOUTUBE_SCOPES
    )
    youtube = build('youtube', 'v3', credentials=youtube_creds)

    search_response = youtube.search().list(
        q=search_query,
        part='snippet',
        type='video',
        maxResults=1
    ).execute()

    # Debug: Print the search results
    print(f"Search Query: {search_query}", file=sys.stderr)
    for item in search_response['items']:
        video_title = item['snippet']['title']
        video_id = item['id']['videoId']
        print(f"Found Video: {video_title} (ID: {video_id})", file=sys.stderr)

    if search_response['items']:
        return search_response['items'][0]['id']['videoId']
    return None
        

def create_youtube_playlist(title, description):
    if 'youtube_access_token' not in session:
        return redirect('/youtube_login')

    creds = Credentials(
        token=session['youtube_access_token'],
        refresh_token=session['youtube_refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=YOUTUBE_SCOPES
    )
    youtube = build('youtube', 'v3', credentials=creds)
    
    request = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title': title,
                'description': description,
            },
            'status': {
                'privacyStatus': 'private'
            }
        }
    )
    response = request.execute()
    return response['id']


@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Spotify-To-YouTube App</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #f0f0f0;
                }
                .container {
                    text-align: center;
                    background: white;
                    padding: 50px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                }
                .login-button {
                    padding: 10px 20px;
                    font-size: 16px;
                    color: white;
                    background-color: #1DB954;
                    border: none;
                    border-radius: 4px;
                    text-decoration: none;
                    cursor: pointer;
                }
                .login-button:hover {
                    background-color: #1aa34a;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to my Spotify-To-YouTube App</h1>
                <a href="/login" class="login-button">Login with Spotify</a>
            </div>
        </body>
    </html>
    '''

@app.route('/youtube_login')
def youtube_login():
    params = {
        'client_id': YOUTUBE_CLIENT_ID,
        'response_type': 'code',
        'scope': YOUTUBE_SCOPES,
        'redirect_uri': YOUTUBE_REDIRECT_URI,
        'access_type': 'offline',
        'prompt': 'consent'  # Ensures that the refresh token is returned
    }
    auth_url = f"{YOUTUBE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/youtube_callback')
def youtube_callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': YOUTUBE_REDIRECT_URI,
            'client_id': YOUTUBE_CLIENT_ID,
            'client_secret': YOUTUBE_CLIENT_SECRET
        }

        response = requests.post(YOUTUBE_TOKEN_URL, data=req_body)
        token_info = response.json()
        
        if 'access_token' in token_info and 'refresh_token' in token_info:
            session['youtube_access_token'] = token_info['access_token']
            session['youtube_refresh_token'] = token_info['refresh_token']
            session['youtube_expires_at'] = datetime.now().timestamp() + token_info['expires_in']
            
            return redirect('/playlists')

    return jsonify({"error": "Authorization code not found."})

@app.route('/login')
def login():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': SCOPE,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True  # For debugging, need to remove after.
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:  # If unsuccessful login, Spotify returns an error.
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:  # If successful login, handle the authorization code.
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)  # Exchange code for access token.
        token_info = response.json()
        
        # Check if the response contains the necessary tokens
        if 'access_token' in token_info and 'refresh_token' in token_info and 'expires_in' in token_info:
            session['access_token'] = token_info['access_token']
            session['refresh_token'] = token_info['refresh_token']
            session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']  # Store expiry time as a timestamp.

            return redirect('/playlists')
        else:
            return jsonify({"error": "Failed to retrieve tokens."})

    return jsonify({"error": "Authorization code not found."})

@app.route('/playlists' , methods=['GET', 'POST'])
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']: # Check if access token expired
        return redirect('/refresh-token')
    
    if request.method == 'POST':
        selected_playlist = request.form.get('playlist_id')
        if selected_playlist:
            return redirect(f'/convert/{selected_playlist}')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists' , headers=headers)
    playlists = response.json().get('items', [])
    playlist_options = ''.join(
                f'<input type="radio" id="{playlist["id"]}" name="playlist_id" value="{playlist["id"]}">'
                f'<label for="{playlist["id"]}">{playlist["name"]}</label><br>'
                for playlist in playlists
            )
            
    html_content = f'''
            <html>
                <head><title>Your Playlists</title></head>
                <body>
                    <h1>Your Playlists</h1>
                    <form method="post">
                        {playlist_options}
                        <br>
                        <button type="submit">Convert to YouTube Playlist</button>
                    </form>
                </body>
            </html>
            '''
    return html_content


@app.route('/convert/<playlist_id>')
def convert_playlist(playlist_id):
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session.get('expires_at', 0):
        return redirect('/refresh-token')

    # Check if the user is authenticated with YouTube
    if 'youtube_access_token' not in session:
        return redirect('/youtube_login')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    # Fetch playlist details from Spotify
    playlist_response = requests.get(f"{API_BASE_URL}playlists/{playlist_id}", headers=headers)
    playlist_data = playlist_response.json()
    playlist_name = playlist_data.get('name', 'Converted Playlist')

    # Fetch the playlist tracks
    tracks_response = requests.get(f"{API_BASE_URL}playlists/{playlist_id}/tracks", headers=headers)
    tracks = tracks_response.json().get('items', [])
    tracks = tracks[:MAX_SONGS] # Trimming tracks to a certain amount to avoid passing YouTube API limits


    # Create a YouTube playlist with the correct title
    youtube_playlist_id = create_youtube_playlist(f"Converted from Spotify: {playlist_name}", "Playlist converted from Spotify")

    youtube_creds = Credentials(
        token=session['youtube_access_token'],
        refresh_token=session['youtube_refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=YOUTUBE_SCOPES
    )
    youtube = build('youtube', 'v3', credentials=youtube_creds)

    not_found_songs = []  # To keep track of songs not found on YouTube

    # Add each track to the YouTube playlist
    for track in tracks:
        song_name = track["track"]["name"]
        song_artist = track["track"]["artists"][0]["name"]
        
        video_id = find_youtube_video_id(song_name, song_artist)
        
        if video_id:
            youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': youtube_playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            ).execute()
        else:
            not_found_songs.append(f"{song_name} by {song_artist}")

    # Report unfound songs
    not_found_report = '<br>'.join(not_found_songs) if not_found_songs else 'None'
    return f'''
        <html>
            <body>
                <h1>Playlist Created!</h1>
                <p>Playlist ID: {youtube_playlist_id}</p>
                <h2>Some songs were not found on YouTube:</h2>
                <p>{not_found_report}</p>
                <p><a href="https://www.youtube.com/playlist?list={youtube_playlist_id}">View Playlist on YouTube</a></p>
            </body>
        </html>
    '''

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']: # Check if access token expired
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'CLIENT_SECRET': CLIENT_SECRET
        }
        response = requests.post(TOKEN_URL , data=req_body)
        new_token_info = response.json()
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']  # Store expiry time as a timestamp.

        return redirect('/playlists')


if __name__ == '__main__':
    app.run(debug=True)
