import random
from datetime import time

import mido

# MIDI Offsets
MIDI_SUB_COLOR = 50
MIDI_SUB_GOBO = 60
MIDI_SUB_OPTICS = 70
MIDI_SUB_MOVEMENT = 80

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

        self.color_setting = color_index + (QUANTITY_COLOR if is_slow else 0)
        self.gobo_setting = gobo_index
        self.optics_setting = optics_index
        self.color_setting = move_index + (QUANTITY_MOVEMENT if is_slow else 0)


class midiControl:
    def __init__(self) -> None:
        self.midi_out = mido.open_output(  # pylint: disable=no-member
            name="SpotMIDIfy 1"
        )
        random.seed(time.microsecond)

        self.this_change = self.gerandom_change()
        self.next_change = self.generate_random_change()
        # RESET ALL SUBS
        self._reset_sub(QUANTITY_COLOR * 2, MIDI_SUB_COLOR)
        self._reset_sub(QUANTITY_GOBO, MIDI_SUB_GOBO)
        self._reset_sub(QUANTITY_OPTICS, MIDI_SUB_OPTICS)
        self._reset_sub(QUANTITY_MOVEMENT * 2, MIDI_SUB_MOVEMENT)

    def do_change(self):
        pass

    def set_change(self, this_chanage: midiChange, next_change: midiChange):
        self.this_change = this_chanage
        self.next_change = next_change

    def generate_random_change(tempo: float = 100) -> midiChange:
        return midiChange(
            color_index=random.randint(1, QUANTITY_COLOR),
            gobo_index=random.randint(1, QUANTITY_GOBO),
            optics_index=random.randint(1, QUANTITY_OPTICS),
            move_index=random.randint(1, QUANTITY_MOVEMENT),
            is_slow=False,
            tempo=tempo,
        )

    def _midi_send(self, note):
        self.midi_out.send(mido.Message("note_on", note=note, velocity=127))
        self.midi_out.send(mido.Message("note_on", note=note, velocity=0))

    def change_color(self):
        # Find a new color that is DIFFERENT
        new_color = random.randint(1, QUANTITY_COLOR)
        while self.cur_color == new_color:
            new_color = random.randint(1, QUANTITY_COLOR)
        self.cur_color = new_color
        self.send_color_change()

    def send_color_change(self):
        if self.is_fade:
            color = self.cur_color
        else:
            color = self.cur_color + QUANTITY_COLOR

        if color != self.cur_color_setting:
            print("      Changed color to: {}".format(color))
            self._set_sub(color - 1, MIDI_SUB_COLOR)
            self._midi_send(note=MIDI_SUB_COLOR)  # start
            self._reset_sub(QUANTITY_COLOR * 2, MIDI_SUB_COLOR)
            self.cur_color_setting = color

    def change_speed(self, slow: bool):
        self.is_fade = slow
        self.is_slow = slow
        self.send_color_change()
        # self.send_movement_change()

    def change_movement(self):
        self.cur_move = random.randint(1, QUANTITY_COLOR)
        self.send_color_change()

    def send_movement_change(self):
        self._reset_sub(QUANTITY_MOVEMENT * 2, QUANTITY_MOVEMENT)
        if self.is_slow:
            move = self.cur_move
        else:
            move = self.cur_move + QUANTITY_MOVEMENT

        if move != self.cur_move_setting:
            self._set_sub(move, QUANTITY_MOVEMENT)
            self._midi_send(note=QUANTITY_MOVEMENT)  # start
            self.cur_move_setting = move

    def change_gobo(self):
        pass
