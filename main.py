from spotify import spotifyMonitor
from midi import midiControl


def start():
    monitor.on_track_change += print_track_change
    monitor.on_section_change += print_section_change
    monitor.on_track_change += handle_track_change
    monitor.on_section_change += handle_section_change
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
    previous_section: dict, current_section: dict, next_section: dict
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


def handle_track_change(
    previous_track: dict, current_track: dict, current_section: dict, next_section: dict
):
    # Change color
    # Change gobo
    # Change movement
    # Change optics
    # Charge speed
    # Change tempo
    pass


def handle_section_change(
    previous_section: dict, current_section: dict, next_section: dict
):
    # Change tempo
    # Loudness:
    #   lower 1/2 - speed to slow
    #   upper 1/2 - speed to fast
    #

    # Change speed
    # Change optics OR gobo if little diff in loudness
    # Change movement if big diff in loudness AND not cross speed threshold
    pass


monitor = spotifyMonitor(debug=True)
midi = midiControl()

if __name__ == "__main__":
    start()
