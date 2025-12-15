# Tidal-transition

This project is for everyone who wants to transition from Spotify to Tidal without paying money to transfer their songs. All this code does, is to transfer the liked songs of your Spotify profile into a playlist on your Tidal account. I personally think it's a shame that companies charge for this simple task. Therefore, I coded this tool for myself to transfer my data without any charges, and I felt like sharing it so everyone has the opportunity to switch to Tidal.

You can do what ever you want with this code. Feel free to change anything or build upon this code.

If you still need any convincing to leave Spotify I got [this](https://en.wikipedia.org/wiki/Criticism_of_Spotify) for you. Have fun. 

## Table of Contents
1. [Installation](#installation)
  1.1 [API Setup](#api-setup)
2. [Usage](#usage)
3. [Reliability](#reliability)

## Installation

As you can see, there are only 2 Python files in this repository. However, it's not just about running the Python files. You need to set up the Spotify Developer API and the Tidal Developer API. But don't worry—it's completely free, and you just have to change 3 variables in the ```.env``` file.

**Requirements:**
  - Python 3.13 or higher (probably also lower)
  - pip

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Setup the .env file:**
Create a .env file in this directory, that looks like this:
```
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
TIDAL_CLIENT_ID=your_tidal_client_id_here
```

### 🔑 API Setup
<b>[Spotify](https://developer.spotify.com/documentation/web-api)</b>
  1. Login with the profile you want to transfer the data from
  2. In the top rigth corner click onto you profile and enter the dashboard and create a new app
  3. As the Website you have to enter this URL ```http://127.0.0.1:8000/callback```, then you are done
  4. Go into your newly created App and get the CLIENT_ID and CLIENT_SECRET and paste them into the ```.env``` file at the corresponding location.

<b>[Tiday](https://developer.tidal.com/)</b>
  1. Login with the profile you want to tranfer the data to
  2. Go to the Dashboard in the top right corner
  3. Create a new app
  4. Copy the ``CLIENT_ID`` into the corresponding location in the ```.env``` file (no ```CLIENT_SECRET```needed)
  5. Go to the settings and add this URL ```http://localhost:8080/callback``` to the redirect URLs
  6. Add the following Scopes in the Settings ```search.write playlists.write```

## 🚀 Usage
From here on the process is pretty much straight forward. You have to execute the 2 Python files [get-spotify-data.py](./get-spotify-data.py) and [spotify-to-tidle.py](./spotify-to-tidle.py).

1. <b>Execute</b> [get-spotify-data.py](./get-spotify-data.py)
 Follow the instructions on the console and if successfull, a .json file will be created with all your Songs and info about them.
2. <b>Execute</b> [spotify-to-tidle.py](./spotify-to-tidle.py)
    All your Songs will get into a playlist called ```Spotify Songs``` on your Tidal account.

## ⚠️ Reliability
This code is far from perfect. This is just a small project I created in one evening, but it still performs well enough in my opinion.

My results: Out of around 900 songs, I transferred about 800. There were still 100 songs missing, which is why I added a feature that lists all songs that couldn't be transferred.

<b>Known issues</b>:

 - ❌ Some songs get transferred incorrectly - The code simply searches for a song and adds the first result to the playlist, so occasionally the wrong version is added. This is rare though—I had about 4 wrong songs.
 - 💔 No "Liked Songs" support - It's currently not possible to add songs to your favorites with the Tidal Developer API. I originally wanted to implement this, but the feature doesn't exist yet. The Tidal Developer API is still under development, so hopefully this feature will come in the near future. I'd be more than happy to implement it then!