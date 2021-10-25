import copy
import random
from datetime import datetime

from spotify import spotifyMonitor
from midi import midiControl, midiChange


def start():
    monitor.on_track_change += print_track_change
    monitor.on_section_change += print_section_change
    monitor.on_stop += print_stop
    monitor.on_track_change += handle_track_change
    monitor.on_section_change += handle_section_change
    monitor.on_stop += handle_stop
    try:
        monitor.start()
    except:
        print("An error occured")


def print_track_change(
    previous_track: dict, current_track: dict, current_section: dict, next_section: dict
):
    print(
        "Track {} lasting {}. Tempo {} Loudness {}".format(
            current_track["name"],
            current_track["duration"],
            current_track["tempo"],
            current_track["loudness"],
        )
    )
    print_section_change(None, current_section, next_section)


def print_section_change(
    current_track: dict, current_section: dict, next_section: dict
):
    print(
        "   Section {} start {} end {} - lasting {}. Tempo {} Loudness {} Key {}".format(
            current_section["id"],
            current_section["start"],
            next_section["start"],
            current_section["duration"],
            current_section["tempo"],
            current_section["loudness"],
            current_section["key"],
        )
    )


def print_stop():
    print("Playback stopped")


def handle_track_change(
    previous_track: dict, current_track: dict, current_section: dict, next_section: dict
):
    this_change = midi.generate_random_change()
    if current_track["name"] == "How Long Will I Love You - Bonus Track":
        this_change.set_color(0)
        this_change.gobo_index = 0
        this_change.set_optics(0)
        this_change.set_movement(0)
        this_change.set_speed(True)
    else:
        this_change.set_speed(calculate_is_slow(current_track, current_section))
    midi.set_change(this_change)
    handle_section_change(current_track, current_section, next_section)


def handle_section_change(
    current_track: dict, current_section: dict, next_section: dict
):
    midi.do_change()
    next_change = midi_change_from_section(
        midi.change, current_track, next_section, current_section
    )
    midi.set_change(next_change)


def handle_stop():
    midi.set_background_state()


def calculate_is_slow(track: dict, section: dict) -> bool:
    if track["energy"] < 0.4:
        return True

    # if "sections_loudness_mean" in ["track"]:
    #     mean_loudness = track["sections_loudness_mean"]
    # else:
    #     mean_loudness = track["loudness"]

    section_loudness = section["loudness"] or -100

    if section_loudness < -10:
        is_slow = True
    elif section_loudness < track["loudness"] - 2.5:
        is_slow = True
        is_slow = True
    else:
        is_slow = False
    return is_slow


def midi_change_from_section(
    base_change: midiChange, track: dict, section: dict, previous_section: dict
) -> midiChange:
    # Change tempo
    # Loudness:
    #   lower 1/2 - speed to slow
    #   upper 1/2 - speed to fast
    #   OR
    #   from 3rd 1/4 to 4th 1/4 - change movement
    #   OR
    #   Change optics OR gobo (random)
    change = copy.deepcopy(base_change)
    change.tempo = section["tempo"]

    if track["energy"] < 0.4:
        return change

    change.set_speed(calculate_is_slow(track, section))
    if change.is_slow != base_change.is_slow:
        # If speed has changed then just leave it at that
        return change

    if change.is_slow:
        # If slow either change optics or gobo
        if random.randint(1, 2) == 1:
            change.set_optics(midi.generate_random_index("optics"))
        else:
            change.gobo_index = midi.generate_random_index("gobo")
        return change

    if random.randint(1, 2) == 1:
        change.set_movement(midi.generate_random_index("movement"))
        change.gobo_index = midi.generate_random_index("gobo")
    else:
        change.set_optics(midi.generate_random_index("optics"))
        change.gobo_index = midi.generate_random_index("gobo")
    return change


monitor = spotifyMonitor()
midi = midiControl()
random.seed(datetime.now().time().microsecond)

if __name__ == "__main__":
    start()
