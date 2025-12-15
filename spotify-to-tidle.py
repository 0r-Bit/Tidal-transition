import base64
import hashlib
import os
import urllib.parse
import json
import requests
import time
import os
from dotenv import load_dotenv

from flask import Flask, request

# === CONFIGURATION ===
REDIRECT_URI = 'http://localhost:8080/callback'  # Local server callback
SCOPES = 'search.write playlists.write'  # Adjust scopes as needed
AUTH_URL = "https://login.tidal.com/authorize"
TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"

def get_client_stuff():
    load_dotenv()
    CLIENT_ID = os.getenv('TIDAL_CLIENT_ID')
    #CLIENT_SECRET = os.getenv('TIDAL_CLIENT_SECRET')
    return CLIENT_ID

# === PKCE Code Challenge ===
def generate_pkce_pair():
    # Step 1: Create a random code verifier (43–128 characters)
    verifier_bytes = os.urandom(64)  # 64 bytes = 86-character base64url
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b'=').decode()

    # Step 2: Create the S256 code challenge
    sha256_hash = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).rstrip(b'=').decode()

    return code_verifier, code_challenge

# === Flask app to catch redirect ===
app = Flask(__name__)
auth_code_result = {}

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return f"Error: {request.args['error_description']}", 400

    auth_code_result['code'] = request.args.get('code')
    return "Authorization successful. You may close this tab."

def get_tidal_access_token(CLIENT_ID:str):
    verifier, challenge = generate_pkce_pair()

    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'scope': SCOPES,
        'redirect_uri': REDIRECT_URI,
        'campaignId': 'default',  # Adjust as needed,
        'state': os.urandom(16).hex()  # Random state for CSRF protection
    }

    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print("Open this URL in your browser to authorize:")
    print(url)

    # Start local server to receive callback
    import threading
    threading.Thread(target=lambda: app.run(port=8080), daemon=True).start()

    # Wait until code is received
    import time
    while 'code' not in auth_code_result:
        time.sleep(1)

    code = auth_code_result['code']
    print(f"Received auth code: {code}")

    # Exchange code for token
    print(CLIENT_ID)
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': verifier
    }

    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        token_data = response.json()
        print("\n✅ Access token received:")
        print(token_data)
        return token_data['access_token']
    else:
        print("Failed to get token:")
        print(response.status_code, response.text)

def upload_tracks_to_tidal(access_token, json_file, playlist_id,  country_code='DE'):
    '''
    Uploads tracks from a JSON file to a Tidal playlist.
        :param access_token: Tidal API access token
        :param json_file: Path to the JSON file containing track data
        :param playlist_id: ID of the Tidal playlist to upload tracks to
        :param country_code: Country code for the Tidal API
        :return: None'''
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for track in data:
            if "name" in track:
                title = track["name"]
            if "artists" in track and len(track["artists"]) > 0:
                artist = track["artists"][0]

            # Search for the track on Tidal to get its ID
            params = {
                'countryCode': country_code,
            }
            search_headers = {
                "Authorization": f"Bearer {access_token}"
            }
            url = "https://openapi.tidal.com/v2/searchResults/" + str(title) + " " + str(artist) + "/relationships/tracks"
            url = url.replace(" ", "%20")
            search_response = requests.get(
                url,
                params=params,
                headers=search_headers
            )

            found = 0
            not_found = 0
            #API Ergebnisse prüfen
            if search_response.status_code == 200:
                search_results = search_response.json()
                if not search_results:
                    print("search results empty")
                    not_found += 1
                    continue
                try:
                    if "data" in search_results and len(search_results["data"]) > 0:
                        if search_results["data"][0]["type"] != "tracks":
                            print(f"First result is not a track for '{title}' by '{artist}'.")
                            not_found += 1
                            continue
                        track_id = search_results["data"][0]["id"]
                        print(f"Found track '{title}' by '{artist}' \t\t ID: {track_id}")
                        found += 1

                        # Add the track to the user's library
                        if add_to_playlist(access_token, track_id, playlist_id, country_code):
                            print(f"Track '{title}' by '{artist}' added to playlist successfully.")
                        else:
                            print(f"Failed to add track '{title}' by '{artist}' to playlist.")
                            not_found += 1
                            continue
                    else:
                        print(f"No tracks found for '{title}' by '{artist}'.")
                        not_found += 1
                        continue
                    time.sleep(0.1)  # Rate limiting
                except:
                    print("Error processing search results for track. Continuing to next track. | Track title: " + str(title) + " | Artist: " + str(artist))
            else:
                print(f"Failed to search for '{title}' by '{artist}'. Status: {search_response.status_code}, Response: {search_response.text}")
            
    return found, not_found

def add_to_playlist(access_token, track_id, playlist_id, country_code='DE'):
    '''
    Adds a track to a Tidal playlist.
        :param access_token: Tidal API access token
        :param track_id: ID of the track to add
        :param playlist_id: ID of the playlist to add the track to
        :param country_code: Country code for the Tidal API
        :return: 1 if successful, 0 if not
    '''
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    data = {
        "data":[
            {
                "id": track_id,
                "type": "tracks"
            }
        ]
    }
    response = requests.post(
        f"https://openapi.tidal.com/v2/playlists/{playlist_id}/relationships/items?countryCode={country_code}",
        headers=headers,
        json=data
    )

    if response.status_code == 201:
        return 1
    else:
        print(response)
        return 0

def create_playlist(access_token, title, country_code='DE'):
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    data = {
        "data": {
            "attributes": {
                "accessType": "PUBLIC",
                "description": "Spotify Library",
                "name": "Spotify Songs"
            },
            "type": "playlists"
        }
    }
    response = requests.post(f"https://openapi.tidal.com/v2/playlists?countryCode={country_code}", headers=headers, json=data)
    if response.status_code == 201:
        print(f"Playlist '{title}' created successfully.")
        return response.json()["data"]["id"]
    else:
        print(f"Failed to create playlist: {response.status_code}, {response.text}")
        return None

if __name__ == "__main__":
    CLIENT_ID = get_client_stuff()
    json_file = 'spotify_saved_tracks.json'

    access_token = get_tidal_access_token(CLIENT_ID)
    if access_token:
        print("Access token retrieved successfully!")
    else:
        print("Failed to retrieve access token.")
        exit(1)

    playlist_id = create_playlist(access_token, "Spotify Songs")
    if not playlist_id:
        print("Failed to create playlist.")
        exit(1)

    found, not_found = upload_tracks_to_tidal(access_token, json_file, playlist_id)

    print("=========================")
    print(f"Tracks found: {found}")
    print(f"Tracks not found: {not_found}")
    print("=========================")
    print("Done! You can now check your Tidal playlist.")