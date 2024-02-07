import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template
from flask_session import Session
import uuid, os, time
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(64)
TOKEN_INFO = "token_info"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def create_spotify_oauth():
    redirect_uri = url_for("index", _external=True, _scheme=request.scheme)
    return SpotifyOAuth(
        client_id="CLIENT-ID-HERE",
        client_secret="CLIENT-SECRET-HERE",
        redirect_uri=redirect_uri,
        scope="playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public",
        show_dialog=True,
    )


@app.route("/")
def index():

    auth_manager = create_spotify_oauth()

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/")

    if not auth_manager.get_cached_token():
        auth_url = auth_manager.get_authorize_url()
        return render_template("spotify_sign_in.html", auth_url=auth_url)

    return redirect("display_playlist")


@app.route("/display_playlist")
def display_playlist():
    auth_manager = create_spotify_oauth()
    if not auth_manager.get_cached_token():
        return redirect("/")
    sp = spotipy.Spotify(auth_manager=auth_manager)
    total_spotify_playlists = sp.user_playlists(sp.me()["id"])["items"]
    spotify_playlist_names_ids = []
    for item in total_spotify_playlists:
        if item["owner"]["id"] == sp.me()["id"]:
            spotify_playlist_names_ids.append((item["name"], item["id"]))

    return render_template(
        "playlist.html", spotify_playlists=spotify_playlist_names_ids
    )


@app.route("/display_tracks", methods=["GET"])
def display_tracks():
    auth_manager = create_spotify_oauth()
    if not auth_manager.get_cached_token():
        return redirect("/")
    sp = spotipy.Spotify(auth_manager=auth_manager)
    spotify_playlist_name_id = clean(request.args.get("spotify_playlist"))
    songs_in_spotify_playlist = get_track_details(
        spotify_playlist_name_id[1], returner="name"
    )
    return render_template(
        "songs.html",
        songs_spotify_playlist=songs_in_spotify_playlist,
        spotify_playlist_name_id=spotify_playlist_name_id,
        spotify_user_id=sp.me()["id"],
    )


@app.route("/spotify_write_new_playlist", methods=["POST"])
def spotify_write_new_playlist():
    auth_manager = create_spotify_oauth()
    if not auth_manager.get_cached_token():
        return redirect("/")

    sp = spotipy.Spotify(auth_manager=auth_manager)
    spotify_user_id = sp.me()["id"]
    spotify_playlist_name_id = clean(request.form.get("spotify_playlist_name_id"))

    try:
        track_details = get_track_details(
            playlist_id=spotify_playlist_name_id[1], returner="date_uri"
        )
        track_details = list(zip(*track_details))
        track_dict = {
            convert_time_to_month_year(date): [] for date in set(track_details[0])
        }

        for date, uri in zip(track_details[0], track_details[1]):
            formatted_date = convert_time_to_month_year(date)
            track_dict[formatted_date].append(uri)
    except Exception as e:
        return str(e)

    for track_date, track_uris in track_dict.items():
        description = f"Playlist for {track_date}"
        playlist_name = track_date

        # Check if the playlist already exists
        playlist_exists = False
        for item in sp.user_playlists(spotify_user_id)["items"]:
            if item["owner"]["id"] == spotify_user_id and item["name"] == playlist_name:
                playlist_id = item["id"]
                playlist_exists = True
                break

        # If playlist doesn't exist, create a new one
        if not playlist_exists:
            sp.user_playlist_create(
                user=spotify_user_id, name=playlist_name, description=description
            )
            for item in sp.user_playlists(spotify_user_id)["items"]:
                if (
                    item["owner"]["id"] == spotify_user_id
                    and item["name"] == playlist_name
                ):
                    playlist_id = item["id"]

        # Add songs to the playlist
        spotify_add_songs(playlist_id=playlist_id, track_uris=track_uris)
        time.sleep(0.25)

    return render_template("sign_out.html")


@app.route("/sign_out")
def sign_out():
    try:
        os.remove(".cache")
        session.clear()
    except:
        pass
    return redirect("/")


def get_track_details(playlist_id, returner):
    auth_manager = create_spotify_oauth()

    sp = spotipy.Spotify(auth_manager=auth_manager)
    track_details = []
    iter = 0
    while True:
        offset = iter * 50
        iter += 1
        current = sp.playlist_tracks(playlist_id, limit=50, offset=offset)["items"]
        for item in current:
            try:
                if returner == "date_uri":
                    track_detail = item["added_at"], item["track"]["uri"]
                elif returner == "name":
                    track_detail = item["track"]["name"]

                track_details.append(track_detail)
            except Exception as e:  # case where there is user added songs locally
                pass
        if len(current) < 50:
            break
    return track_details


def clean(dirty):
    return (
        dirty[2:-2]
        .replace("', '", ",")
        .translate({ord(i): None for i in "[]"})
        .split(",")
    )


def spotify_add_songs(playlist_id, track_uris):
    auth_manager = create_spotify_oauth()
    if not auth_manager.get_cached_token():
        return redirect("/")
    sp = spotipy.Spotify(auth_manager=auth_manager)
    iter = 0
    end = False
    while True:
        pos = iter * 100
        offset = (iter + 1) * 100
        iter += 1
        if offset > len(track_uris):
            offset = len(track_uris)
            end = True
        tracks = track_uris[pos:offset]
        for i in range(3):
            try:
                sp.playlist_add_items(playlist_id=playlist_id, items=tracks)
                break
            except Exception as e:
                continue
        if end:
            break


def convert_time_to_month_year(time_str):
    dt_object = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    formatted_date = dt_object.strftime("%B %Y")

    return formatted_date


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
