import time
import asyncio
from typing import List
import statistics
import numpy as np


import spotipy
from spotipy.oauth2 import SpotifyOAuth

from eventhook import EventHook


class NotPlayingError(Exception):
    def __init__(self):
        self.message = "Spotify not playing"


class MonitorConfig:
    def __init__(
        self,
        refresh_accuracy_seconds: float = 1.0,
        refresh_max_delay_seconds: float = 30.0,
        refresh_next_event_divisor: float = 1.5,
        not_playing_refresh_seconds: float = 5.0,
        tick_accuracy_seconds: float = 0.25,
        tick_max_delay_seconds: float = 10.0,
        tick_next_event_divisor: float = 2.0,
        section_offset_seconds: float = 0.25,
    ):
        self.refresh_accuracy_seconds = refresh_accuracy_seconds
        self.refresh_max_delay_seconds = refresh_max_delay_seconds
        self.refresh_next_event_divisor = refresh_next_event_divisor
        self.not_playing_refresh_seconds = not_playing_refresh_seconds
        self.tick_accuracy_seconds = tick_accuracy_seconds
        self.tick_max_delay_seconds = tick_max_delay_seconds
        self.tick_next_event_divisor = tick_next_event_divisor
        self.section_offset_seconds = section_offset_seconds


class spotifyMonitor:
    def __init__(
        self,
        config: MonitorConfig = MonitorConfig(),
        debug: bool = False,
    ) -> None:
        self.config = config
        self.sp = self._generate_spotify_auth()
        self.on_track_change = EventHook()
        self.on_section_change = EventHook()
        self.on_stop = EventHook()
        self.current_track = {"id": None, "progress": 0.0, "sections": []}
        self.current_section = {"id": None, "track_id": None}
        self.next_section = {"id": None, "track_id": None}
        self._loop = asyncio.get_event_loop()
        self._last_tick = self._get_tick_time()
        self.debug = debug
        self._ticking = False
        self._playing = False

    def start(self):
        try:
            self._loop.call_soon(self._refresh)
            self._loop.run_forever()
        finally:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()

    def stop(self):
        self._loop.stop()

    def _generate_spotify_auth(self) -> spotipy.Spotify:
        scope = "user-read-playback-state"
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=scope,
                client_id="397df7bde7e64245bf93014ce0d36b4f",
                client_secret="5d7d498988714957990b45afa47fdd36",
                redirect_uri="http://127.0.0.1:9090",
            )
        )

    def _refresh(self):
        try:
            self._refresh_track_status()
            self._playing = True
            if self.debug:
                print("         Refresh {}".format(self.current_track["progress"]))
            if self._ticking == False:
                self._last_tick = self._get_tick_time()
                self._ticking = True
                self._loop.call_soon(self._tick)

            delay = (
                self.current_track["duration"] - self.current_track["progress"]
            ) / self.config.refresh_next_event_divisor
            if delay > self.config.refresh_max_delay_seconds:
                delay = self.config.refresh_max_delay_seconds
            elif delay < self.config.refresh_accuracy_seconds:
                delay = self.config.refresh_accuracy_seconds
        except NotPlayingError:
            if self._playing:
                self._playing = False
                self.on_stop.fire()

            delay = 5
            if self.debug:
                print("         Refresh (not playing)")

        self._loop.call_later(delay=delay, callback=self._refresh)

    def _tick(self):
        if self._playing:
            this_tick = self._get_tick_time()
            self.current_track["progress"] += (this_tick - self._last_tick) / 1000
            self._last_tick = this_tick
            if self.debug:
                print("         Tick {}".format(self.current_track["progress"]))

            current_section_id = self._calculate_current_section_id(self.current_track)

            if current_section_id != self.current_section["id"]:
                section_info = self._calculate_section_info(
                    self.current_track, current_section_id
                )
                self._trigger_section_change(self.current_track, section_info)
                self.current_section = section_info["current_section"]
                self.next_section = section_info["next_section"]

            delay = (
                self.next_section["start"] - self.current_track["progress"]
            ) / self.config.tick_next_event_divisor
            if delay > self.config.tick_max_delay_seconds:
                delay = self.config.tick_max_delay_seconds
            elif delay < self.config.tick_accuracy_seconds:
                delay = self.next_section["start"] - self.current_track["progress"]

            if delay < 0:
                delay = self.config.tick_accuracy_seconds
            self._loop.call_later(delay=delay, callback=self._tick)
        else:
            self._ticking = False

    def _get_tick_time(self) -> float:
        return time.time_ns() // 1000000

    def _refresh_track_status(self):
        current_track = self._get_current_track_status()
        track_change = self.current_track["id"] != current_track["id"]

        section_info = self._calculate_section_info(current_track)
        section_change = (
            self.current_section["id"] != section_info["current_section"]["id"]
            or self.current_section["track_id"]
            != section_info["current_section"]["track_id"]
        )

        if track_change:
            self._trigger_track_change(current_track, section_info)
        elif section_change:
            self._trigger_section_change(current_track, section_info)

        self.current_track = current_track
        self._last_tick = self._get_tick_time()
        self.current_section = section_info["current_section"]
        self.next_section = section_info["next_section"]

    def _trigger_track_change(self, track, section_info):
        self.on_track_change.fire(
            previous_track=self.current_track,
            current_track=track,
            current_section=section_info["current_section"],
            next_section=section_info["next_section"],
        )

    def _trigger_section_change(self, track, section_info):
        self.on_section_change.fire(
            current_track=track,
            current_section=section_info["current_section"],
            next_section=section_info["next_section"],
        )

    def _get_current_track_status(self) -> dict:
        track = self._get_spotify_currently_playing()

        if track["id"] != self.current_track["id"]:
            track_info = self._get_spotify_track_info(track_id=track["id"])
            current_track = {**track, **track_info}
        else:
            current_track = self.current_track
            current_track["progress"] = track["progress"]

        return current_track

    def _calculate_section_info(self, track, current_section_id: int = None) -> dict:
        if not current_section_id:
            current_section_id = self._calculate_current_section_id(track)
        track_sections = track["sections"]

        section = {
            **{"id": current_section_id, "track_id": track["id"]},
            **track_sections[current_section_id],
        }
        if current_section_id + 1 < len(track_sections):
            next_section = track_sections[current_section_id + 1]
        else:
            next_section = {
                "id": 0,
                "track_id": None,
                "tempo": None,
                "loudness": None,
                "start": track["duration"],
            }
        return {"current_section": section, "next_section": next_section}

    def _calculate_current_section_id(self, track) -> int:
        current_section_id = 0
        for index, section in enumerate(track["sections"]):
            if section["start"] < track["progress"]:
                current_section_id = index
            if section["start"] > track["progress"]:
                break

        return current_section_id

    def _get_spotify_currently_playing(self) -> dict:
        # print("            CALL to currently_playing")
        try:
            result = self.sp.currently_playing()
            if result:
                if result["is_playing"]:
                    return {
                        "id": result["item"]["id"],
                        "name": result["item"]["name"],
                        "artist": result["item"]["artists"][0]["name"],
                        "duration": result["item"]["duration_ms"] / 1000,
                        "progress": result["progress_ms"] / 1000,
                    }
                else:
                    raise NotPlayingError
            else:
                raise NotPlayingError
        # FIXME - Add 401 error here
        except ValueError:
            return {
                "id": None,
                "name": None,
                "artist": None,
                "duration": None,
                "progress": None,
            }

    def _get_spotify_track_info(self, track_id) -> dict:
        # print("            CALL to audio_analysis")
        try:
            result = self.sp.audio_analysis(track_id=track_id)
            for section in result["sections"]:
                section["start"] = section["start"] - self.config.section_offset_seconds

            loudnesses = [
                section["loudness"]
                for section in result["sections"]
                if "loudness" in section
            ]
            return {
                "id": track_id,
                "duration": result["track"]["duration"],
                "tempo": result["track"]["tempo"],
                "loudness": result["track"]["loudness"],
                "key": result["track"]["key"],
                "sections": result["sections"],
                "sections_loudness_mean": np.mean(loudnesses),
                "sections_loudness_upperq": np.quantile(loudnesses, 0.75),
            }
        # FIXME - Add 401 error here
        except ValueError:
            return {"tempo": None, "loudness": None, "sections": List()}
