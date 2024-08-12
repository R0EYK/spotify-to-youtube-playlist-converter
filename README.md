# Spotify to YouTube Playlist Converter
This application converts Spotify playlists into YouTube playlists.

# Installation
pip install -r pip_requirements.txt

# Usage
Create app in both developers.spotify.com and Google Cloud Console 
you only need to change the the CLIENT_ID and CLIENT_SECRET for both Spotify and YouTube.
You`ll need to allow the redirect URI on Spotify for http://localhost:5000/callback
and on YouTube to allow redirect URI for http://localhost:5000/youtube_callback

Create `.env` file 

```
# Spotify API Credentials
CLIENT_ID=''
CLIENT_SECRET=''
REDIRECT_URI=http://localhost:5000/callback
AUTH_URL=https://accounts.spotify.com/authorize
TOKEN_URL=https://accounts.spotify.com/api/token
API_BASE_URL=https://api.spotify.com/v1/
SCOPE=playlist-read-private

# YouTube API Credentials
YOUTUBE_CLIENT_ID=''
YOUTUBE_CLIENT_SECRET=''
YOUTUBE_REDIRECT_URI=http://localhost:5000/youtube_callback
YOUTUBE_AUTH_URL=https://accounts.google.com/o/oauth2/auth
YOUTUBE_TOKEN_URL=https://oauth2.googleapis.com/token
YOUTUBE_SCOPES=https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.force-ssl


