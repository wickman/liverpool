from __future__ import print_function

from liverpool.common import Card, Color, Objective
from liverpool.generation import iter_sets, iter_runs, iter_melds
from liverpool.hand import Hand

h = Hand()
h.put_card(Card(7, Color.SPADE))
h.put_card(Card(7, Color.DIAMOND))
h.put_card(Card(7, Color.HEART))
h.put_card(Card(2, Color.HEART))
h.put_card(Card(3, Color.HEART))
h.put_card(Card(3, Color.CLUB))
h.put_card(Card.JOKER)
h.put_card(Card(4, Color.HEART))
h.put_card(Card(5, Color.HEART))

print()
print('Sets:')
for set_ in iter_sets(h):
  print(set_)

print()
print('Runs:')
for run in iter_runs(h):
  print(run)

objective = Objective(1, 1)

print()
print('1/1 Melds:')
for lay in iter_melds(h, objective):
  print(lay)
