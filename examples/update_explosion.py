from liverpool.hand import Hand
from liverpool.common import Rank, Color, Set, Run, Meld, Card

from liverpool.generation import (
    iter_updates_multi,
    iter_runs_lut,
    IndexedHand,
)


table_melds = {
    3: Meld(
        sets=[
            Set.of(9, colors=[Color.CLUB, Color.SPADE, Color.DIAMOND, Color.DIAMOND]),
            Set.of(
                Rank.ACE,
                colors=[Color.CLUB, Color.SPADE, Color.HEART, Color.DIAMOND, Color.DIAMOND],
            ),
        ],
        runs=[Run.of(Color.CLUB, start=4, jokers=[False, False, False, False, True, False])],
    ),
    2: Meld(
        sets=[
            Set.of(2, colors=[Color.CLUB, Color.CLUB, Color.SPADE]),
            Set.of(8, colors=[Color.SPADE, Color.HEART, Color.HEART, Color.DIAMOND]),
        ],
        runs=[Run.of(Color.SPADE, start=Rank.JACK, jokers=[False, False, False, False])],
    ),
    0: Meld(
        sets=[
            Set.of(3, colors=[Color.CLUB, Color.HEART, None]),
            Set.of(
                Rank.QUEEN, colors=[Color.CLUB, Color.CLUB, Color.SPADE, Color.HEART, Color.DIAMOND]
            ),
        ],
        runs=[Run.of(Color.SPADE, start=3, jokers=[False, False, True, False, False])],
    ),
    1: Meld(
        sets=[
            Set.of(3, colors=[Color.CLUB, Color.SPADE, Color.HEART, Color.DIAMOND, Color.DIAMOND]),
            Set.of(Rank.JACK, colors=[Color.HEART, Color.HEART, Color.DIAMOND]),
        ],
        runs=[Run.of(Color.DIAMOND, start=10, jokers=[False, False, False, False])],
    ),
}


hand = IndexedHand(
    [
        Card.of(4, Color.CLUB),
        Card.of(5, Color.CLUB),
        Card.of(6, Color.CLUB),
        Card.of(2, Color.SPADE),
        Card.of(2, Color.HEART),
        Card.of(9, Color.HEART),
        Card.of(2, Color.DIAMOND),
        Card.of(8, Color.DIAMOND),
        Card.joker(),
    ]
)


for meld_updates in iter_updates_multi(hand, table_melds, run_iterator=iter_runs_lut):
    print(meld_updates)
