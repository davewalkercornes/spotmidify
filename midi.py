import random
from datetime import time

import mido

# MIDI Offsets
MIDI_SUB_COLOR = 50
MIDI_SUB_GOBO = 60
MIDI_SUB_OPTICS = 70
MIDI_SUB_MOVEMENT = 80
MIDI_SUB_BACKGROUND = 90

MIDI_RUN = 0
MIDI_FORWARD = 1
MIDI_BACK = 2
MIDI_STOP = 3

QUANTITY_COLOR = 10
QUANTITY_GOBO = 16
QUANTITY_OPTICS = 8
QUANTITY_MOVEMENT = 5


class midiChange:
    def __init__(
        self,
        color_index: int,
        gobo_index: int,
        optics_index: int,
        move_index: int,
        is_slow: bool,
        tempo: float,
    ) -> None:
        self.color_index = color_index
        self.gobo_index = gobo_index
        self.optics_index = optics_index
        self.move_index = move_index
        self.is_slow = is_slow
        self.tempo = tempo
        self.color_setting = 0
        self.move_setting = 0
        self.set_speed(is_slow)

    def set_speed(self, is_slow: bool):
        self.is_slow = is_slow
        self._update_settings()

    def set_color(self, color_index):
        self.color_index = color_index
        self._update_settings()

    def set_movement(self, move_index):
        self.move_index = move_index
        self._update_settings()

    def _update_settings(self):
        self.color_setting = self.color_index + (0 if self.is_slow else QUANTITY_COLOR)
        self.move_setting = self.move_index + (0 if self.is_slow else QUANTITY_MOVEMENT)


class midiControl:
    def __init__(self) -> None:
        self.midi_out = mido.open_output(  # pylint: disable=no-member
            name="SpotMIDIfy 1"
        )
        self._first = True
        random.seed(time.microsecond)

        self._reset_all_subs()
        self.change = midiChange(0, 0, 0, 0, True, 100)
        self.do_change()

    def do_change(self):
        self._stop_sub(MIDI_SUB_BACKGROUND)
        print(
            "      LX Change color {} gobo {} optics {} movement {}".format(
                self.change.color_setting,
                self.change.gobo_index,
                self.change.optics_index,
                self.change.move_setting,
            )
        )
        self._run_sub(MIDI_SUB_COLOR)
        self._run_sub(MIDI_SUB_GOBO)
        self._run_sub(QUANTITY_OPTICS)
        self._run_sub(MIDI_SUB_COLOR)

    def set_change(self, change: midiChange):
        if self.change.color_setting != change.color_setting:
            self._reset_sub(QUANTITY_COLOR * 2, MIDI_SUB_COLOR)
            self._set_sub(change.color_setting, MIDI_SUB_COLOR)
        if self.change.gobo_index != change.gobo_index:
            self._reset_sub(QUANTITY_GOBO * 2, MIDI_SUB_GOBO)
            self._set_sub(change.color_setting, MIDI_SUB_GOBO)
        if self.change.optics_index != change.optics_index:
            self._reset_sub(QUANTITY_OPTICS * 2, MIDI_SUB_OPTICS)
            self._set_sub(change.color_setting, MIDI_SUB_OPTICS)
        if self.change.move_setting != change.move_setting:
            self._reset_sub(QUANTITY_MOVEMENT * 2, MIDI_SUB_MOVEMENT)
            self._set_sub(change.color_setting, MIDI_SUB_MOVEMENT)
        self.change = change
        print(
            "      [Prep change color {} gobo {} optics {} movement {}]".format(
                self.change.color_setting,
                self.change.gobo_index,
                self.change.optics_index,
                self.change.move_setting,
            )
        )

    def stop(self):
        self._run_sub(MIDI_SUB_BACKGROUND)
        self._stop_sub(MIDI_SUB_COLOR)
        self._stop_sub(MIDI_SUB_GOBO)
        self._stop_sub(MIDI_SUB_OPTICS)
        self._stop_sub(MIDI_SUB_MOVEMENT)

    def generate_random_change(self, tempo: float = 100) -> midiChange:
        if self._first:
            self._first = False
            self.change.tempo = tempo
            return self.change

        return midiChange(
            color_index=self.generate_random_index("color"),
            gobo_index=self.generate_random_index("gobo"),
            optics_index=self.generate_random_index("optics"),
            move_index=self.generate_random_index("movement"),
            is_slow=True,
            tempo=tempo,
        )

    def generate_random_index(self, type: str) -> int:
        if type == "color":
            quantity = QUANTITY_COLOR
        elif type == "gobo":
            quantity = QUANTITY_GOBO
        elif type == "optics":
            quantity = QUANTITY_OPTICS
        elif type == "movement":
            quantity = QUANTITY_MOVEMENT
        return random.randint(0, quantity - 1)

    def _reset_all_subs(self):
        self._reset_sub(QUANTITY_COLOR * 2, MIDI_SUB_COLOR)
        self._reset_sub(QUANTITY_GOBO, MIDI_SUB_GOBO)
        self._reset_sub(QUANTITY_OPTICS, MIDI_SUB_OPTICS)
        self._reset_sub(QUANTITY_MOVEMENT * 2, MIDI_SUB_MOVEMENT)

    def _run_sub(self, offset):
        self._midi_send(note=offset + MIDI_RUN)

    def _stop_sub(self, offset):
        self._midi_send(note=offset + MIDI_STOP)

    def _reset_sub(self, quantity, offset):
        for i in range(quantity):
            self._midi_send(note=offset + MIDI_BACK)

    def _set_sub(self, quantity, offset):
        for i in range(quantity):
            self._midi_send(note=offset + MIDI_FORWARD)

    def _midi_send(self, note):
        self.midi_out.send(mido.Message("note_on", note=note, velocity=127))
        self.midi_out.send(mido.Message("note_on", note=note, velocity=0))
