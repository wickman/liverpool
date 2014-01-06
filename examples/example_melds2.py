from __future__ import print_function

from liverpool.common import Card, Color, Objective, Rank
from liverpool.hand import Hand, FastHand

def run(h):
  print('Hand class %s' % h.__class__)
  print()

  cards = [
    Card(2, Color.CLUB),
    Card(2, Color.HEART),
    Card(2, Color.DIAMOND),
    Card(5, Color.SPADE),
    Card(5, Color.HEART),
    Card(Rank.KING, Color.DIAMOND),
    Card.JOKER,
    Card.JOKER,
    Card.JOKER,
    Card.JOKER,
  ]

  for card in cards:
    h.put_card(card)

  objective = Objective(3, 0)

  # if set iterator returns dupes, this will be ~= 780
  for meld in h.iter_melds(objective):
    print(meld)


run(Hand())
run(FastHand())
