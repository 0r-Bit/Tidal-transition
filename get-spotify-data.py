import requests
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
from dotenv import load_dotenv

# Replace with your Spotify API credentials
REDIRECT_URI = 'http://127.0.0.1:8000/callback'  # Local server callback
SCOPE = 'user-library-read'

# Global variable to store the authorization code
auth_code = None

def get_client_stuff():
    load_dotenv()
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    return CLIENT_ID, CLIENT_SECRET

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        # Parse the URL to get the authorization code
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/callback':
            query_params = parse_qs(parsed_url.query)
            if 'code' in query_params:
                auth_code = query_params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Authorization successful!</h1><p>You can close this window and return to your terminal.</p></body></html>')
            elif 'error' in query_params:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                error = query_params['error'][0]
                self.wfile.write(f'<html><body><h1>Authorization failed!</h1><p>Error: {error}</p></body></html>'.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass

def start_callback_server():
    server = HTTPServer(('127.0.0.1', 8000), CallbackHandler)
    server.timeout = 60  # 60 second timeout
    server.handle_request()  # Handle one request then stop
    return server

def authorize(CLIENT_ID:str, CLIENT_SECRET:str):

    # Step 1: Get authorization code
    print("Starting local callback server on http://127.0.0.1:8000/callback")
    print("Please make sure this redirect URI is added to your Spotify app settings!")
    print()

    # Start the callback server in a separate thread
    server_thread = threading.Thread(target=start_callback_server)
    server_thread.daemon = True
    server_thread.start()

    print(f"Go to the following URL to authorize:\n"
        f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}")
    print()
    print("Waiting for authorization callback...")

    # Wait for the authorization code
    start_time = time.time()
    while auth_code is None and (time.time() - start_time) < 60:
        time.sleep(0.1)

    if auth_code is None:
        print("Timeout waiting for authorization. Please try again.")
        exit(1)

    print(f"Authorization successful! Code received: {auth_code[:10]}...")

    # Step 2: Exchange authorization code for access token
    token_url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(token_url, data=payload)

    # Check for errors in token response
    if response.status_code != 200:
        print(f"Error getting access token: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)

    token_info = response.json()
    if 'error' in token_info:
        print(f"Token error: {token_info['error']}")
        if 'error_description' in token_info:
            print(f"Description: {token_info['error_description']}")
        exit(1)

    access_token = token_info['access_token']
    return access_token

def get_saved_tracks(access_token):

    # Step 3: Get saved tracks
    headers = {'Authorization': f'Bearer {access_token}'}
    tracks = []
    url = 'https://api.spotify.com/v1/me/tracks'
    params = {'limit': 50}

    while url:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        for item in data['items']:
            track = item['track']
            tracks.append({
            'name': track['name'],
            'artists': [artist['name'] for artist in track['artists']],
            'artists_ids': [artist['id'] for artist in track['artists']],
            'album': track['album']['name'],
            'id': track['id']
        })
        url = data['next']
        params = None  # Only needed for the first request

    # Save tracks to JSON file
    filename = 'spotify_saved_tracks.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, indent=2, ensure_ascii=False)

    print(f"Successfully saved {len(tracks)} tracks to '{filename}'")
    print(f"Total tracks found: {len(tracks)}")

def genres(access_token):
    with open('spotify_saved_tracks.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        for track in data:
            artist_id = track['artists_ids'][0]

            if 'genre_count' not in locals():
                genre_count = {}

            header = {
                'Authorization': f'Bearer {access_token}'
            }
            url = f'https://api.spotify.com/v1/artists/{artist_id}'
            response = requests.get(url, headers=header)

            if response.status_code == 200:
                artist_info = response.json()
                for genre in artist_info.get('genres', []):
                    genre_count[genre] = genre_count.get(genre, 0) + 1

if __name__ == "__main__":
    CLIENT_ID, CLIENT_SECRET = get_client_stuff()
    access_token = authorize(CLIENT_ID, CLIENT_SECRET)
    if not access_token:
        print("Failed to get access token.")
        exit(1)
    print("Wait until getting all your songs is finished.")
    get_saved_tracks(access_token)
    print("Done! All your saved tracks have been exported to 'spotify_saved_tracks.json'.")
