import datetime
import random
import string
import sys
from collections import namedtuple

from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError


TRACK_MAIN = 'dev_tracks/01. Main Theme.mp3'
TRACK_SHOP = 'dev_tracks/02. Shop Theme.mp3'
TRACK_TAROT = 'dev_tracks/03. Tarot Pack Theme.mp3'
TRACK_PLANET = 'dev_tracks/04. Planet Pack Theme.mp3'
TRACK_BOSS = 'dev_tracks/05. Boss Blind Theme.mp3'

try:
    AUDIO = {name: AudioSegment.from_file(name) for name in [TRACK_MAIN, TRACK_SHOP, TRACK_TAROT, TRACK_PLANET, TRACK_BOSS]}
except CouldntDecodeError as e:
    print('Track files are invalid. Note: If these are dummy files from the repo, read the README section "File requirements"!')
    sys.exit(1)

BASE_LENGTH = len(AUDIO[TRACK_MAIN])

State = namedtuple('State', 'theme type blind ante round')

# Logic using State type
DURATION = {
    'Pick': range(3_000, 5_000, 500),
    'Round': range(10_000, 40_000, 500),
    'Shop': range(4_000, 10_000, 500),
    'ShopEmpty': range(2_000, 4_000, 500),
    'CardPack': range(5_000, 6_000, 500),
    'JokerPack': range(5_000, 12_000, 500),
    'TarotPack': range(8_000, 16_000, 500),
    'PlanetPack': range(5_000, 8_000, 500)
}

MOVEMENT = {
    'Pick': (('Round', 'Pick',), (0.95, 0.05)),
    'Round': (('Shop', None), (0.95, 0.05)),
    'Shop': (('JokerPack', 'TarotPack', 'CardPack', 'PlanetPack', 'Pick'), (0.175, 0.175, 0.175, 0.175, 0.3)),
    'ShopEmpty': (('Pick',), (1.0,)),
    'CardPack': (('Shop',), (1.0,)), 
    'JokerPack': (('Shop',), (1.0,)), 
    'TarotPack': (('Shop',), (1.0,)),
    'PlanetPack': (('Shop',), (1.0,))
}

NEXT_BLIND = {'Small': 'Big', 'Big': 'Boss', 'Boss': 'Small'}


def get_theme(state_type, state_blind):
    if state_type == 'PlanetPack':
        return TRACK_PLANET
    if state_type in ['CardPack', 'JokerPack', 'TarotPack']:
        return TRACK_TAROT
    if state_type == 'Round' and state_blind == 'Boss':
        return TRACK_BOSS
    if state_type in ['Shop', 'ShopEmpty']:
        return TRACK_SHOP
    return TRACK_MAIN


def increase_round_difficulty(ante, is_boss):
    base_lose_chance = 0.05 if is_boss else 0.025
    mult = ante - 1
    _, (curr_win, curr_lose) = MOVEMENT['Round']
    updated_win = curr_win - (base_lose_chance * mult)
    updated_lose = curr_lose + (base_lose_chance * mult)
    return (updated_win, updated_lose)


def insert_pack_sfx(track1, track2):
    sfx1 = AUDIO[SFX_PACK][:2500] + 1
    sfx2 = AUDIO[SFX_PACK][2500:] + 1
    overlap1 = track1.overlay(sfx1, position=len(track1)-len(sfx1))
    overlap2_start = sfx2.overlay(track2[:len(sfx2)], position=0)
    overlap2 = overlap2_start + track2[len(sfx2):]
    return overlap1 + overlap2


def create_run(seed):
    random.seed(seed)

    run = []
    num_packs = 0
    run_ante = 1
    run_round = 1
    curr_state = State(TRACK_MAIN, 'Pick', 'Boss', run_ante, run_round)

    while curr_state is not None:
        # Process current State
        is_boss = curr_state.blind == 'Boss'
        if curr_state.type == 'Round':
            run_round += 1

        curr_state_duration = random.choice(DURATION[curr_state.type])
        if run_ante == 1 and curr_state.type == 'Round':
            curr_state_duration += random.choice(range(5_000, 10_000, 1_000))

        if curr_state.type in ['CardPack', 'JokerPack', 'TarotPack', 'PlanetPack']:
            num_packs += 1
        if curr_state.type == 'Shop' and num_packs >= 2:
            curr_state = State(curr_state.theme, 'ShopEmpty', curr_state.blind, run_ante, run_round)
            num_packs = 0

        # Prepare next State
        type_choices, weights = MOVEMENT[curr_state.type]
        
        if curr_state.type == 'Round':
            weights = increase_round_difficulty(run_ante, is_boss)

        if curr_state.type == 'Pick' and curr_state.blind == 'Big':
            weights = (1.0, 0.0) # cannot skip Boss, you fool
        
        next_type = random.choices(type_choices, weights=weights, k=1)[0]

        ### Lose Round : implies last round should be extra long
        if next_type is None:
            curr_state_duration += random.choice(range(20_000, 30_000, 5_000))
        ### Win Round
        elif curr_state.type == 'Round' and is_boss:
            run_ante += 1

        # Add current State
        run.append((curr_state, curr_state_duration))
        
        # Create next State
        next_blind = NEXT_BLIND[curr_state.blind] if curr_state.type == 'Pick' else curr_state.blind
        next_theme = get_theme(next_type, next_blind)

        curr_state = State(next_theme, next_type, next_blind, run_ante, run_round) if next_type is not None else None
            
    return run


def create_track(run, filename='balatro.mp3', fade_duration=100, include_sfx=False):
    stitched_track = AudioSegment.empty()
    timestamp = 0
    prev_theme = TRACK_MAIN
    for state, segment_duration in run:
        audio = AUDIO[state.theme]
        start = (timestamp) % BASE_LENGTH
        end = (timestamp + segment_duration) % BASE_LENGTH
        if start < end:
            segment = audio[start:end]
        else:
            segment = audio[start:] + audio[:end]
        
        if include_sfx:
            if state.type in ['CardPack', 'JokerPack', 'TarotPack', 'PlanetPack']:
                stitched_track = insert_pack_sfx(stitched_track, segment)
            elif state.theme != prev_theme:
                stitched_track = stitched_track + segment.fade_in(fade_duration)
            else:
                stitched_track += segment
        else:
            if state.theme != prev_theme:
                stitched_track = stitched_track + segment.fade_in(fade_duration)
            else:
                stitched_track += segment

        prev_theme = state.theme
        timestamp += segment_duration
        
    stitched_track.export(filename, format='mp3')


def generate_random_seed(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


def format_user_seed(seed):
    cleaned = ''.join(char for char in seed if char.isalnum()).upper()
    if len(cleaned) > 8:
        return cleaned[:8]
    elif len(cleaned) < 8:
        cleaned += generate_random_seed(8-len(cleaned))
    return cleaned


if __name__ == '__main__':
    if len(sys.argv) > 1:
        seed = sys.argv[1]
        seed = format_user_seed(seed)
    else:
        seed = generate_random_seed()

    print('Creating run...')
    run = create_run(seed=seed)

    last = run[-1][0]
    packs = {'Card': 0, 'Joker': 0, 'Tarot': 0, 'Planet': 0}
    duration = 0.0
    for s, d in run:
        if s.type.endswith('Pack'):
            packs[s.type.replace('Pack', '')] += 1
        duration += d/1000
    
    duration_string = (datetime.datetime.min + datetime.timedelta(seconds=duration)).strftime("%H:%M:%S")
    run_result = f'Seed: {seed}\n  > Duration: {duration_string}\n  > Ante: {last.ante}/8\n  > Round: {last.round}\n'
    for pack, count in packs.items():
        run_result += f'  > {pack} packs: {count}\n'
    print(run_result[:-1])

    print('Creating track...')
    create_track(run)

    print('Completed!')
