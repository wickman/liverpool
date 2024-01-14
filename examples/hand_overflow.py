from liverpool.algorithms import find_useful_cards
from liverpool.hand import Hand
from liverpool.common import Color, Rank, Card, Objective
from liverpool.game import document_utility

h = Hand(
    [
        Card.of(2, Color.SPADE),
        Card.of(4, Color.SPADE),
        Card.of(5, Color.SPADE),
        Card.of(10, Color.CLUB),
        Card.of(10, Color.CLUB),
        Card.of(Rank.ACE, Color.CLUB),
        Card.of(5, Color.HEART),
        Card.of(6, Color.HEART),
        Card.of(Rank.KING, Color.HEART),
        Card.of(8, Color.DIAMOND),
        Card.joker(),
        Card.joker(),
    ]
)
print(h)
useful_missing, useful_existing = find_useful_cards(h, Objective(0, 3))
document_utility(h, Objective(0, 3), useful_missing, useful_existing)

h = Hand(
    [
        Card.of(2, Color.SPADE),
        Card.of(2, Color.SPADE),
        Card.of(Rank.ACE, Color.SPADE),
        Card.of(Rank.ACE, Color.SPADE),
        Card.of(2, Color.DIAMOND),
        Card.of(2, Color.DIAMOND),
        Card.of(Rank.ACE, Color.DIAMOND),
        Card.of(Rank.ACE, Color.DIAMOND),
        Card.of(2, Color.HEART),
        Card.of(2, Color.HEART),
        Card.of(Rank.ACE, Color.HEART),
        Card.of(Rank.ACE, Color.HEART),
    ]
)
print(h)
useful_missing, useful_existing = find_useful_cards(h, Objective(0, 3))
document_utility(h, Objective(0, 3), useful_missing, useful_existing)
