from pydub import AudioSegment
import random


TRACK_MAIN = 'tracks/01. Main Theme.mp3'
TRACK_SHOP = 'tracks/02. Shop Theme.mp3'
TRACK_TAROT = 'tracks/03. Tarot Pack Theme.mp3'
TRACK_PLANET = 'tracks/04. Planet Pack Theme.mp3'
TRACK_BOSS = 'tracks/05. Boss Blind Theme.mp3'

TRACK_NAMES = (TRACK_MAIN, TRACK_SHOP, TRACK_TAROT, TRACK_PLANET, TRACK_BOSS)

TRACKS = {track: AudioSegment.from_file(track) for track in TRACK_NAMES}

MOVEMENT = {TRACK_MAIN: [TRACK_SHOP],
            TRACK_SHOP: [TRACK_TAROT, TRACK_PLANET, TRACK_MAIN, TRACK_BOSS],
            TRACK_TAROT: [TRACK_SHOP],
            TRACK_PLANET: [TRACK_SHOP],
            TRACK_BOSS: [TRACK_SHOP]}

BASE_LENGTH = len(TRACKS[TRACK_MAIN])


def generate_uniform(track_length=300_000, segment_duration=30_000, fade_duration=0):
    stitched_track = AudioSegment.empty()
    for start in range(0, track_length, segment_duration):
        end = start + segment_duration
        selected_track = TRACKS[random.choice(TRACK_NAMES)]

        start_mod = start % BASE_LENGTH
        end_mod = end % BASE_LENGTH

        if start_mod < end_mod:
            segment = selected_track[start_mod:end_mod]
        else:
            segment = selected_track[start_mod:] + selected_track[:end_mod]

        if fade_duration > 0:
            segment = segment.fade_in(fade_duration).fade_out(fade_duration)

        stitched_track += segment

    stitched_track = stitched_track[:track_length]
    return stitched_track


#TODO
def generate_skeleton_uniform(track_length=300_000):
    skeleton = []
    return skeleton



#track = generate_uniform().export('balatro_track.mp3', format='mp3')