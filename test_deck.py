from liverpool.common import Deck, Objective
from liverpool.hand import Hand



def simulate(
    num_runs=1,
    num_sets=1,
    iterations=100000,
    decks=2,
    dealt_cards=10):

  total_with_sets = total_with_runs = total_with_lays = total_gone_out = 0

  for iteration in range(iterations):
    h = Hand()
    d = Deck(count=decks)
    for _ in range(dealt_cards):
      h.put_card(d.take())

    #print('%5d :: %s' % (iteration, h))

    sets = list(h.iter_sets())
    if sets:
      total_with_sets += 1
      #print('Sets:')
      #for set_ in sets:
      #  print(set_)

    runs = list(h.iter_runs())
    if runs:
      total_with_runs += 1
      #print('Runs:')
      #for run in runs:
      #  print(run)

    objective = Objective(num_sets, num_runs)

    lays = list(h.iter_lays(objective))
    if lays:
      total_with_lays += 1

      if any(len(lay) == dealt_cards for lay in lays):
        total_gone_out += 1

      #print('%d/%d Lays:' % (num_sets, num_runs))
      #for lay in lays:
      #  print(lay)

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

