from pydub import AudioSegment
import random


TRACK_MAIN = 'tracks/01. Main Theme.mp3'
TRACK_SHOP = 'tracks/02. Shop Theme.mp3'
TRACK_TAROT = 'tracks/03. Tarot Pack Theme.mp3'
TRACK_PLANET = 'tracks/04. Planet Pack Theme.mp3'
TRACK_BOSS = 'tracks/05. Boss Blind Theme.mp3'

TRACK_NAMES = (TRACK_MAIN, TRACK_SHOP, TRACK_TAROT, TRACK_PLANET, TRACK_BOSS)
TRACKS = {track: AudioSegment.from_file(track) for track in TRACK_NAMES}
BASE_LENGTH = len(TRACKS[TRACK_MAIN])

MOVEMENT_LOOP = {TRACK_MAIN: ((TRACK_SHOP, TRACK_BOSS), (0.9, 0.1)),
                 TRACK_SHOP: ((TRACK_TAROT, TRACK_PLANET, TRACK_MAIN), (0.3, 0.3, 0.4)),
                 TRACK_TAROT: ((TRACK_SHOP,), (1.0,)),
                 TRACK_PLANET: ((TRACK_SHOP,), (1.0,)), 
                 TRACK_BOSS: ((TRACK_MAIN, None), (0.9, 0.1))}

MOVEMENT_ANTE_ONE = {TRACK_MAIN: ((TRACK_SHOP, TRACK_BOSS), (0.9, 0.1)),
                     TRACK_SHOP: ((TRACK_TAROT, TRACK_PLANET, TRACK_MAIN), (0.1, 0.1, 0.8)),
                     TRACK_TAROT: ((TRACK_SHOP,), (1.0,)),
                     TRACK_PLANET: ((TRACK_SHOP,), (1.0,)), 
                     TRACK_BOSS: ((TRACK_MAIN, None), (0.9, 0.1))}

MODIFIER_MOVEMENT_BOSS = 0.1

DURATION_LOOP = {TRACK_MAIN: range(15_000, 45_000, 1_000),
                 TRACK_SHOP: range(5_000, 20_000, 1_000),
                 TRACK_TAROT: range(5_000, 10_000, 2_000),
                 TRACK_PLANET: range(5_000, 10_000, 2_000),
                 TRACK_BOSS: range(15_000, 45_000, 1_000)}

DURATION_ANTE_ONE = {TRACK_MAIN: range(30_000, 45_000, 1_000),
                     TRACK_SHOP: range(2_000, 6_000, 1_000),
                     TRACK_TAROT: range(5_000, 10_000, 2_000),
                     TRACK_PLANET: range(5_000, 10_000, 2_000),
                     TRACK_BOSS: range(15_000, 45_000, 1_000)}


def generate_skeleton_game():
    skeleton = []
    curr_state = TRACK_MAIN
    boss_count = 0

    # game loop
    while curr_state is not None:
        if boss_count == 0:
            state_duration = random.choice(DURATION_ANTE_ONE[curr_state])
        else:
            state_duration = random.choice(TRACK_DURATIONS[curr_state])

        skeleton.append((curr_state, state_duration))

        if boss_count == 0:
            next_choices, next_weights = MOVEMENT_ANTE_ONE[curr_state]
        else:
            next_choices, next_weights = MOVEMENT_LOOP[curr_state]

        if curr_state == TRACK_BOSS:
            modifier = MODIFIER_MOVEMENT_BOSS * boss_count
            next_weights = (next_weights[0]-modifier, next_weights[1]+modifier)
            boss_count += 1
        
        next_state = random.choices(next_choices, weights=next_weights, k=1)[0]
        
        curr_state = next_state
    
    return skeleton


def create_track(skeleton, filename='balatro.mp3', fade_duration=50):
    stitched_track = AudioSegment.empty()
    timestamp = 0
    for track_name, track_duration in skeleton:
        track = TRACKS[track_name]
        start = (timestamp) % BASE_LENGTH
        end = (timestamp + track_duration) % BASE_LENGTH
        if start < end:
            segment = track[start:end]
        else:
            segment = track[start:] + track[:end]
        
        if fade_duration > 0:
            segment = segment.fade_in(fade_duration).fade_out(fade_duration)
        
        timestamp += track_duration
        
        stitched_track += segment
    stitched_track.export(filename, format='mp3')


#skeleton = generate_skeleton_game()
#create_track(skeleton)