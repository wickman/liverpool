import random
import sys
import time

from liverpool.common import Deck, Objective
from liverpool.generation import (
    IndexedHand,
    iter_melds,
    iter_runs_lut,
    iter_sets_lut,
    iter_runs,
    iter_sets,
    maybe_precompute,
)


def simulate(
    num_runs=1,
    num_sets=1,
    iterations=100000,
    decks=2,
    dealt_cards=10,
    set_iterator=iter_sets,
    run_iterator=iter_runs):

  start = time.time()
  total_with_sets = total_with_runs = total_with_lays = total_gone_out = 0

  for iteration in range(iterations):
    h = IndexedHand()
    d = Deck.new(count=decks)

    for _ in range(dealt_cards):
      h.put_card(d.pop())

    sets = list(set_iterator(h))
    if sets:
      total_with_sets += 1

    runs = list(run_iterator(h))
    if runs:
      total_with_runs += 1

    objective = Objective(num_sets, num_runs)

    lays = list(iter_melds(h, objective, run_iterator=run_iterator, set_iterator=set_iterator))
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
maybe_precompute()

print('Without LUTS')
simulate(num_sets=2, num_runs=0, dealt_cards=10)
simulate(num_sets=1, num_runs=1, dealt_cards=10)
simulate(num_sets=0, num_runs=2, dealt_cards=10)
simulate(num_sets=3, num_runs=0, dealt_cards=10)
simulate(num_sets=2, num_runs=1, dealt_cards=12)
simulate(num_sets=1, num_runs=2, dealt_cards=12)
simulate(num_sets=0, num_runs=3, dealt_cards=12)

print('With LUTS')
simulate(iterations=1000000, num_sets=2, num_runs=0, dealt_cards=10, run_iterator=iter_runs_lut, set_iterator=iter_sets_lut)
simulate(iterations=1000000, num_sets=1, num_runs=1, dealt_cards=10, run_iterator=iter_runs_lut, set_iterator=iter_sets_lut)
simulate(iterations=1000000, num_sets=0, num_runs=2, dealt_cards=10, run_iterator=iter_runs_lut, set_iterator=iter_sets_lut)
simulate(iterations=1000000, num_sets=3, num_runs=0, dealt_cards=10, run_iterator=iter_runs_lut, set_iterator=iter_sets_lut)
simulate(iterations=1000000, num_sets=2, num_runs=1, dealt_cards=12, run_iterator=iter_runs_lut, set_iterator=iter_sets_lut)
simulate(iterations=1000000, num_sets=1, num_runs=2, dealt_cards=12, run_iterator=iter_runs_lut, set_iterator=iter_sets_lut)
simulate(iterations=1000000, num_sets=0, num_runs=3, dealt_cards=12, run_iterator=iter_runs_lut, set_iterator=iter_sets_lut)

