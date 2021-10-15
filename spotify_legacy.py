import time
from typing import List


import spotipy
from spotipy.oauth2 import SpotifyOAuth

from eventhook import EventHook


class spotifyMonitor:
    def __init__(self, accuracy_seconds: float) -> None:
        self.accuracy_seconds = accuracy_seconds
        scope = "user-read-playback-state"

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=scope,
                client_id="397df7bde7e64245bf93014ce0d36b4f",
                client_secret="5d7d498988714957990b45afa47fdd36",
                redirect_uri="http://127.0.0.1:9090",
            )
        )
        self.track_id = 0
        self.track_duration = 0.0
        self.track_progress = 0.0
        self.track_tempo = 0.0
        self.track_loudness = 0.0
        self.track_name = ""
        self.track_artist = ""
        self.stop_requested = False
        self.current_section = -1
        self.onTrackChange = EventHook()
        self.onSectionChange = EventHook()

    def start(self):
        self.stop_requested = False
        self.get_playing()
        self.run_loop()

    def stop(self):
        self.stop_requested = True

    def run_loop(self):
        while self.stop_requested == False:

            for index, section in enumerate(self.sections):
                if section["start"] < self.track_progress:
                    started_section = index
                if section["start"] > self.track_progress:
                    break

            if self.current_section != started_section:
                self.current_section = started_section

                if self.current_section + 1 >= len(self.sections):
                    next_section_start = self.track_duration
                else:
                    next_section_start = self.sections[self.current_section + 1][
                        "start"
                    ]

                self.onSectionChange.fire(
                    index=self.current_section,
                    tempo=self.sections[self.current_section]["tempo"],
                    loudness=self.sections[self.current_section]["loudness"],
                    duration=next_section_start
                    - self.sections[self.current_section]["start"],
                )

            sleep_seconds = next_section_start - self.track_progress
            if self.track_progress <= self.accuracy_seconds:
                sleep_seconds = self.accuracy_seconds
            elif sleep_seconds < self.accuracy_seconds * 5:
                sleep_seconds = self.accuracy_seconds
            else:
                sleep_seconds = sleep_seconds / 2

            print(
                "      Check - progress {}.  Next section at {}".format(
                    self.track_progress, next_section_start
                )
            )

            time.sleep(sleep_seconds)

            self.get_playing()

    def get_playing(self) -> dict:
        result = self.sp.currently_playing()
        result = self.sp.playlist("3cDOohUC9rDNOq2MQXkIEH")
        self.track_progress = result["progress_ms"] / 1000

        if self.track_id != result["item"]["id"]:
            self.track_id = result["item"]["id"]
            self.track_name = result["item"]["name"]
            self.track_artist = result["item"]["artists"][0]["name"]
            self.track_duration = result["item"]["duration_ms"] / 1000
            self.current_section = -1
            self.get_track_info(self.track_id)
            self.onTrackChange.fire(
                name=self.track_name,
                artist=self.track_artist,
                tempo=self.track_tempo,
                loudness=self.track_loudness,
            )
        self.track_remaining = self.track_duration - self.track_progress

    def get_track_info(self, track_id) -> dict:
        result = self.sp.audio_analysis(track_id=track_id)
        self.track_tempo = result["track"]["tempo"]
        self.track_loudness = result["track"]["loudness"]
        self.sections: List = result["sections"]
