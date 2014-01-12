import random
import sys
import time

from liverpool.common import Deck, Objective
from liverpool.generation import (
    IndexedHand,
    iter_melds,
    iter_runs_lut as iter_runs,
    iter_sets_lut as iter_sets,
    #iter_runs as iter_runs,
    #iter_sets as iter_sets,
    load_luts,
)


def simulate(
    num_runs=1,
    num_sets=1,
    iterations=100000,
    decks=2,
    dealt_cards=10):

  start = time.time()
  total_with_sets = total_with_runs = total_with_lays = total_gone_out = 0

  for iteration in range(iterations):
    h = IndexedHand()
    d = Deck(count=decks)

    for _ in range(dealt_cards):
      h.put_card(d.take())

    sets = list(iter_sets(h))
    if sets:
      total_with_sets += 1

    runs = list(iter_runs(h))
    if runs:
      total_with_runs += 1

    objective = Objective(num_sets, num_runs)

    lays = list(iter_melds(h, objective, run_iterator=iter_runs, set_iterator=iter_sets))
    if lays:
      total_with_lays += 1

      if any(len(lay) == dealt_cards for lay in lays):
        # for lay in lays:
        #   if len(lay) == dealt_cards:
        #     print('Dealt %s => Went out with %s' % (h, lay))
        total_gone_out += 1

  print('sets/runs/dealt %d/%d/%d iters/sets/runs/melds/out: %5d/%5d/%5d/%5d/%5d [%.1fus/iter]' % (
      num_sets, num_runs, dealt_cards,
      iterations, total_with_sets, total_with_runs, total_with_lays, total_gone_out,
      1000000.0 * (time.time() - start) / iterations))


if len(sys.argv) == 2:
  random.seed(int(sys.argv[1]))


# preload
# load_luts()

simulate(num_sets=2, num_runs=0, dealt_cards=10)
simulate(num_sets=1, num_runs=1, dealt_cards=10)
simulate(num_sets=0, num_runs=2, dealt_cards=10)
simulate(num_sets=3, num_runs=0, dealt_cards=10)
simulate(num_sets=2, num_runs=1, dealt_cards=12)
simulate(num_sets=1, num_runs=2, dealt_cards=12)
simulate(num_sets=0, num_runs=3, dealt_cards=12)

