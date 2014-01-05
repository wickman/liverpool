from liverpool.common import Card, Color, Objective
from liverpool.hand import Hand

"""
h = Hand()
h.put_card(Card(Color.SPADE, 7))
h.put_card(Card(Color.DIAMOND, 7))
h.put_card(Card(Color.HEART, 7))
h.put_card(Card(Color.HEART, 2))
h.put_card(Card(Color.HEART, 3))
h.put_card(Card(Color.CLUB, 3))
h.put_card(Card.JOKER)
h.put_card(Card(Color.HEART, 4))
h.put_card(Card(Color.HEART, 5))

print()
print('Sets:')
for set_ in h.iter_sets():
  print(set_)

print()
print('Runs:')
for run in h.iter_runs():
  print(run)

objective = Objective(1, 1)

print()
print('1/1 Lays:')
for lay in h.iter_melds(objective):
  print(lay)
"""
