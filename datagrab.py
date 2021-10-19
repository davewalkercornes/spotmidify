from spotify import spotifyMonitor

monitor = spotifyMonitor()

# playlists = monitor._get_current_user_playlists()
# for playlist in playlists:
tracks_info = []
tracks = monitor._get_playlist("7DnACkveVMy4PUm8Kh188x")
for track in tracks:
    features = monitor._get_spotify_track_features(track["id"])
    tracks_info.append({**track, **features})

tracks = monitor._get_playlist("1oYUzdgWOWZBza6utNilDG")
for track in tracks:
    features = monitor._get_spotify_track_features(track["id"])
    tracks_info.append({**track, **features})


import csv

with open(
    "track_data.csv", "w", newline=""
) as f:  # You will need 'wb' mode in Python 2.x
    w = csv.DictWriter(f, tracks_info[0].keys())
    w.writeheader()
    w.writerows(tracks_info)
