## Purpose

This script runs a flask webpage which offers the user to pick from any of their current spotify playlists and then creates monthly subplaylists based upon when songs were added to the playlist selected. This is intended for those, like myself, who have amassed a singular large playlist over many years and want more organization in their listening.

## Requirements

Install dependencies using

`pip install -r requirements.txt`

It's a good idea use [Conda](https://docs.conda.io/en/latest/) or [venv](https://docs.python.org/3/library/venv.html) to do this in a virtual environment.

## Spotify Developer Setup

To create a valid client-secret and client-id, simply go to `https://developer.spotify.com/` login, go to dashboard in the top right, hit create app. Under the next section name it and describe it as whatever you like, and put `http://127.0.0.1:5000` in the redirect_uri section (this is the base that main.py runs flask on locally). Lastly, click Web API and save. 

Once created click on the app, then go to settings and copy and paste the client secret and ID into the portion highlighted in main.py. Finally, run main.py and go to `http://127.0.0.1:5000` in your local browser