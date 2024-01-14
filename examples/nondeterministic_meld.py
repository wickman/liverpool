from collections import defaultdict

from liverpool.algorithms import find_useful_cards
from liverpool.hand import Hand
from liverpool.common import Rank, Color, Set, Run, Meld, Card, Objective
from liverpool.game import document_utility, meld_score
from liverpool.generation import (
    iter_melds,
    IndexedHand,
)


hand = IndexedHand(
    [
        Card.of(2, Color.CLUB),
        Card.of(2, Color.CLUB),
        Card.of(3, Color.CLUB),
        Card.of(6, Color.CLUB),
        Card.of(8, Color.CLUB),
        Card.of(8, Color.CLUB),
        Card.of(9, Color.CLUB),
        Card.of(2, Color.SPADE),
        Card.of(3, Color.SPADE),
        Card.of(4, Color.SPADE),
        Card.of(4, Color.SPADE),
        Card.of(5, Color.SPADE),
        Card.of(7, Color.SPADE),
        Card.of(4, Color.HEART),
        Card.of(5, Color.HEART),
        Card.of(Rank.KING, Color.HEART),
        Card.of(Rank.KING, Color.HEART),
        Card.of(4, Color.DIAMOND),
        Card.joker(),
    ]
)


melds = defaultdict(list)
objective = Objective(1, 2)

for _ in range(10):
    if hand not in melds:
      print('Hand not in cache (hash(hand) == %d)' % hash(hand))
      melds[hand] = sorted(iter_melds(hand, objective), key=meld_score, reverse=True)
      for meld in melds[hand]:
        print('  - %s' % meld)
    else:
      print('Hand in cache (hash(hand) == %d)' % hash(hand))
      for meld in melds[hand]:
        print('  - %s' % meld)    
