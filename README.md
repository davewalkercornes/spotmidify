# spotmidify

Very rough and ready python app that polls the Spotify API for currently playing track and then creates MIDI events based on the dynamics of the track.  Originally built to send MIDI events to Freestyler but can be adapted for anything.  MIDI is connected to Freestyler using software MIDI ports (e.g. provided by LoopMIDI)  This has been used twice in a live environment and is provided without support or warrenty.

Spotify runs analysis on all songs and splits them into "sections" and has tempo, loudness and other metrics for each section.  Based on these sections we can generate MIDI events.



## spotify.py
* Polls the Spotify API for currently playing track information (and where possible next track information)
* Polls the Spotify API for currently playing track position
  * Track position is slowed if next track section is further away
  * As the next track or track section approaches polling is increased
* (Polling rates are controlled by MonitorConfig settings)
* Events on three EventHooks are created for Track Changes (or starts), Section Changes and when playback is stopped.  
  * Events contain relevant information for the track and sections

## midi.py
* Receives events from the spotify Monitor
* Based on events decides which cues within which subs need changing in Freestyler
* Will run the sub change then "cue up" the next change by resetting the position of the various subs
* MIDI commands in freestyler need to be aligned with the constant variables
  * Offsets for each sub and a Freestyler Run, Forward, Back and Stop command
  * E.g. Colour sub RUN in freestyler by default should be channel 50.  Forward for the same sub in freestyler should be channel 51.  Back 52 and stop 53.
* The number of cues in each sub also needs to be aligned.
  * By default gobo sub will randomly be selected
  * Color, optics and movement subs will expect the first X to be "slow" and the next X to be "fast"
  * E.g. by default the movement sub by default needs 7 "slow" cues and 7 "fast" cues
