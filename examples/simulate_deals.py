from liverpool.common import Deck, Objective
from liverpool.hand import Hand, FastHand


def simulate(
    num_runs=1,
    num_sets=1,
    iterations=10000,
    decks=2,
    dealt_cards=10):

  total_with_sets = total_with_runs = total_with_lays = total_gone_out = 0

  for iteration in range(iterations):
    h = FastHand()
    d = Deck(count=decks)
    for _ in range(dealt_cards):
      h.put_card(d.take())

    sets = list(h.iter_sets())
    if sets:
      total_with_sets += 1

    runs = list(h.iter_runs())
    if runs:
      total_with_runs += 1

    objective = Objective(num_sets, num_runs)

    lays = list(h.iter_melds(objective))
    if lays:
      total_with_lays += 1

      if any(len(lay) == dealt_cards for lay in lays):
        for lay in lays:
          if len(lay) == dealt_cards:
            print('Dealt %s => Went out with %s' % (h, lay))
        total_gone_out += 1

  print('sets/runs/dealt %d/%d/%d iters/sets/runs/lays/out: %5d/%5d/%5d/%5d/%5d' % (
      num_sets, num_runs, dealt_cards,
      iterations, total_with_sets, total_with_runs, total_with_lays, total_gone_out))



simulate(num_sets=2, num_runs=0, dealt_cards=10)
simulate(num_sets=1, num_runs=1, dealt_cards=10)
simulate(num_sets=0, num_runs=2, dealt_cards=10)
simulate(num_sets=3, num_runs=0, dealt_cards=10)
simulate(num_sets=2, num_runs=1, dealt_cards=12)
simulate(num_sets=1, num_runs=2, dealt_cards=12)
simulate(num_sets=0, num_runs=3, dealt_cards=12)

