from collections import namedtuple
import sys
import random
import datetime
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError


TRACK_MAIN = 'tracks/01. Main Theme.mp3'
TRACK_SHOP = 'tracks/02. Shop Theme.mp3'
TRACK_TAROT = 'tracks/03. Tarot Pack Theme.mp3'
TRACK_PLANET = 'tracks/04. Planet Pack Theme.mp3'
TRACK_BOSS = 'tracks/05. Boss Blind Theme.mp3'

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
    'Shop': range(4_000, 7_000, 500),
    'ShopEmpty': range(2_000, 3_000, 500),
    'CardPack': range(5_000, 6_000, 500),
    'JokerPack': range(5_000, 12_000, 500),
    'TarotPack': range(8_000, 16_000, 500),
    'PlanetPack': range(5_000, 8_000, 500)
}

MOVEMENT = {
    'Pick': (('Round', 'Pick',), (0.95, 0.05)),
    'Round': (('Shop', None), (0.95, 0.05)),
    'Shop': (('JokerPack', 'TarotPack', 'CardPack', 'PlanetPack', 'Pick'), (0.35, 0.1, 0.1, 0.1, 0.35)),
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


def create_run():
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


def create_track(run, filename='balatro.mp3', fade_duration=50):
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
        
        if state.theme != prev_theme:
            segment = segment.fade_in(fade_duration).fade_out(fade_duration)
        prev_theme = state.theme

        timestamp += segment_duration
        
        stitched_track += segment
    stitched_track.export(filename, format='mp3')


if __name__ == '__main__':
    print('Creating run...')
    run = create_run()

    last = run[-1][0]
    packs = {'Card': 0, 'Joker': 0, 'Tarot': 0, 'Planet': 0}
    duration = 0.0
    for s, d in run:
        if s.type.endswith('Pack'):
            packs[s.type.replace('Pack', '')] += 1
        duration += d/1000
    
    duration_string = (datetime.datetime.min + datetime.timedelta(seconds=duration)).strftime("%H:%M:%S")
    run_result = f'  > Duration: {duration_string}\n  > Ante: {last.ante}/8\n  > Round: {last.round}\n'
    for pack, count in packs.items():
        run_result += f'  > {pack} packs: {count}\n'
    print(run_result[:-1])

    print('Creating track...')
    create_track(run)

    print('Completed!')
