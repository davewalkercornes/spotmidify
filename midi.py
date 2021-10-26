import random
from datetime import datetime

import mido

# MIDI Offsets
MIDI_SUB_COLOR = 50
MIDI_SUB_GOBO = 60
MIDI_SUB_OPTICS = 70
MIDI_SUB_MOVEMENT = 80
MIDI_SUB_BACKGROUND = 40

MIDI_RUN = 0
MIDI_FORWARD = 1
MIDI_BACK = 2
MIDI_STOP = 3

QUANTITY_COLOR = 11
QUANTITY_GOBO = 15
QUANTITY_OPTICS = 5
QUANTITY_MOVEMENT = 7
QUANTITY_BACKGROUND = 3


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
        self.optics_setting = 0
        self.move_setting = 0
        self.set_speed(is_slow)

    def set_speed(self, is_slow: bool):
        self.is_slow = is_slow
        self._update_settings()

    def set_optics(self, optics_index):
        self.optics_index = optics_index
        self._update_settings()

    def set_color(self, color_index):
        self.color_index = color_index
        self._update_settings()

    def set_movement(self, move_index):
        self.move_index = move_index
        self._update_settings()

    def _update_settings(self):
        self.color_setting = self.color_index + (0 if self.is_slow else QUANTITY_COLOR)
        self.optics_setting = self.optics_index + (
            0 if self.is_slow else QUANTITY_OPTICS
        )
        self.move_setting = self.move_index + (0 if self.is_slow else QUANTITY_MOVEMENT)


class midiControl:
    def __init__(self, debug: bool = False, sample: bool = False) -> None:
        self.midi_out = mido.open_output(  # pylint: disable=no-member
            name="SpotMIDIfy 1"
        )
        self._stopped = False
        random.seed(datetime.now().time().microsecond)

        if sample:
            self._send_samples()

        self._color_changed = True
        self._gobo_changed = True
        self._optics_changed = True
        self._movement_changed = True

        self._reset_all_subs()
        self.change = midiChange(0, 0, 0, 0, True, 100)
        self.do_change()

    def _send_samples(self):
        self._send_sample(MIDI_SUB_COLOR, "color")
        self._send_sample(MIDI_SUB_GOBO, "gobo")
        self._send_sample(MIDI_SUB_OPTICS, "optics")
        self._send_sample(MIDI_SUB_MOVEMENT, "movement")
        self._send_sample(MIDI_SUB_BACKGROUND, "backgound")

    def _send_sample(self, offset: int, name: str):
        input("Standby for {} run command.  Press enter for output...".format(name))
        self._run_sub(offset)
        input("Standby for {} stop command.  Press enter for output...".format(name))
        self._stop_sub(offset)
        input("Standby for {} forward command.  Press enter for output...".format(name))
        self._set_sub(1, offset)
        input("Standby for {} back command.  Press enter for output...".format(name))
        self._reset_sub(1, offset)

    def do_change(self):
        if self._color_changed or self._stopped:
            self._run_sub(MIDI_SUB_COLOR)
            print("      LX color {}".format(self.change.color_setting))
        if self._gobo_changed or self._stopped:
            self._run_sub(MIDI_SUB_GOBO)
            print("      LX gobo {}".format(self.change.gobo_index))
        if self._optics_changed or self._stopped:
            self._run_sub(MIDI_SUB_OPTICS)
            print("      LX optics {}".format(self.change.optics_setting))
        if self._movement_changed or self._stopped:
            self._run_sub(MIDI_SUB_MOVEMENT)
            print("      LX movement {}".format(self.change.move_setting))
        if self._stopped:
            self._stop_sub(MIDI_SUB_BACKGROUND)
            self._stopped = False
            print("      LX background set")

    def set_change(self, change: midiChange):
        if self.change.color_setting != change.color_setting:
            self._reset_sub(QUANTITY_COLOR * 2, MIDI_SUB_COLOR)
            self._set_sub(change.color_setting, MIDI_SUB_COLOR)
            self._color_changed = True
            print("      (prep lx color {})".format(change.color_setting))
        else:
            self._color_changed = False
        if self.change.gobo_index != change.gobo_index:
            self._reset_sub(QUANTITY_GOBO, MIDI_SUB_GOBO)
            self._set_sub(change.gobo_index, MIDI_SUB_GOBO)
            self._gobo_changed = True
            print("      (prep lx gobo {})".format(change.gobo_index))
        else:
            self._gobo_changed = False
        if self.change.optics_setting != change.optics_setting:
            self._reset_sub(QUANTITY_OPTICS * 2, MIDI_SUB_OPTICS)
            self._set_sub(change.optics_setting, MIDI_SUB_OPTICS)
            self._optics_changed = True
            print("      (prep lx optics {})".format(change.optics_setting))
        else:
            self._optics_changed = False
        if self.change.move_setting != change.move_setting:
            self._reset_sub(QUANTITY_MOVEMENT * 2, MIDI_SUB_MOVEMENT)
            self._set_sub(change.move_setting, MIDI_SUB_MOVEMENT)
            self._movement_changed = True
            print("      (prep lx movement {})".format(change.move_setting))
        else:
            self._movement_changed = False
        self.change = change

    def set_background_state(self):
        self._run_sub(MIDI_SUB_BACKGROUND)
        self._stop_sub(MIDI_SUB_COLOR)
        self._stop_sub(MIDI_SUB_GOBO)
        self._stop_sub(MIDI_SUB_OPTICS)
        self._stop_sub(MIDI_SUB_MOVEMENT)
        self._stopped = True
        print("      LX Change to background state")

    def generate_random_change(self, tempo: float = 100) -> midiChange:
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
        self._reset_sub(QUANTITY_OPTICS * 2, MIDI_SUB_OPTICS)
        self._reset_sub(QUANTITY_MOVEMENT * 2, MIDI_SUB_MOVEMENT)
        self._reset_sub(QUANTITY_BACKGROUND, MIDI_SUB_BACKGROUND)

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
