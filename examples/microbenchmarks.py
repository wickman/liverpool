from contextlib import contextmanager
from collections import defaultdict
import time
import sys

from liverpool.common import (
    Card,
    Color,
    Rank,
    Run,
    Set,
    Deck
)
from liverpool.hand import Hand
from liverpool.generation import (
    iter_sets,
    iter_runs,
    maybe_precompute,
    iter_sets_lut,
    iter_runs_lut,
    IndexedHand,
    iter_melds,
)
from liverpool.game import Game


ITERS = 1000000
if len(sys.argv) > 1:
    ITERS = int(sys.argv[1])



@contextmanager
def timed(msg):
    start = time.time()
    reported_values = {}
    yield reported_values
    end = time.time()
    print('%-40s %10s (%7s/iter) {%s}' % (
        msg + ':',
        '%.1fms' % (1000.0 * (end - start)),
        '%.1fus' % (1000000.0 * (end - start) / ITERS),
        ', '.join('%s=%s' % (k, v) for k, v in reported_values.items())))


def generate_combo_set(iterator, num_combos=ITERS, seed=1):
    combos = []
    Deck.seed(seed)

    hands = 0
    while len(combos) < num_combos:
       d = Deck.new(count=2)
       h = IndexedHand.from_deck(d, 10)
       for s in iterator(h):
          combos.append(s)
       hands += 1
    
    return combos[0:num_combos], hands


def generate_combos(iterator, num_combos=ITERS, seed=1):
    Deck.seed(seed)
    combos = 0
    for _ in range(num_combos):
       d = Deck.new(count=2)
       h = IndexedHand.from_deck(d, 10)
       for s in iterator(h):
          combos += 1
    
    return combos


def generate_melds(objective, run_iter, set_iter, num_melds=ITERS, seed=1):
    Deck.seed(seed)
    combos = 0
    for _ in range(num_melds):
       d = Deck.new(count=2)
       h = IndexedHand.from_deck(d, 10)
       for m in iter_melds(h, objective, run_iterator=run_iter, set_iterator=set_iter):
         combos += 1
    
    return combos


def deal_cards(num_hands=ITERS, hand_impl=Hand, seed=1):
    Deck.seed(seed)

    for _ in range(num_hands):
        d = Deck.new(count=2)
        h = hand_impl.from_deck(d, 10)

    return


maybe_precompute()

with timed('dealing cards'):
    deal_cards()

with timed('dealing cards (indexed)'):
    deal_cards(hand_impl=IndexedHand)

with timed('generating sets') as rv:
    combos = generate_combos(iter_sets)
    rv['combos'] = combos

with timed('generating sets (lut)') as rv:
    combos = generate_combos(iter_sets_lut)
    rv['combos'] = combos

with timed('generating runs') as rv:
    combos = generate_combos(iter_runs)
    rv['combos'] = combos

with timed('generating runs (lut)') as rv:
    combos = generate_combos(iter_runs_lut)
    rv['combos'] = combos

for objective, cards in Game.TRICKS:
    with timed('generating melds     (%s)' % objective) as rv:
        combos = generate_melds(objective, iter_runs, iter_sets)
        rv['combos'] = combos
    with timed('generating melds lut (%s)' % objective) as rv:
        combos = generate_melds(objective, iter_runs_lut, iter_sets_lut)
        rv['combos'] = combos

sets, _ = generate_combo_set(iter_sets)
sets_lut, _ = generate_combo_set(iter_sets_lut)
runs, _ = generate_combo_set(iter_runs)
runs_lut, _ = generate_combo_set(iter_runs_lut)

with timed('comparing sets') as rv:
    rv['equal'] = sets == sets_lut

with timed('comparing runs') as rv:
    rv['equal'] = runs == runs_lut

sd = defaultdict(int)
with timed('hashing sets') as rv:
    for s in sets:
        sd[s] += 1
    rv['unique'] = len(sd)

rd = defaultdict(int)
with timed('hashing runs') as rv:
    for r in runs:
        rd[r] += 1
    rv['unique'] = len(rd)

with timed('sorting sets'):
    sets.sort()

with timed('sorting runs'):
    runs.sort()
