from liverpool.common import (
    Card,
    Color,
    Objective,
    Rank,
    Set,
)
from liverpool.generation import iter_melds, iter_sets
from liverpool.hand import Hand


def test_set_simple():
  h1 = Hand()
  h1.put_card(Card(2, Color.DIAMOND))
  h1.put_card(Card(2, Color.CLUB))
  h1.put_card(Card(2, Color.SPADE))
  sets1 = list(iter_sets(h1))

  h2 = Hand()
  h2.put_card(Card(2, Color.SPADE))
  h2.put_card(Card(2, Color.CLUB))
  h2.put_card(Card(2, Color.DIAMOND))
  sets2 = list(iter_sets(h2))

  assert len(sets1) == 1
  assert len(sets2) == 1
  assert sets1 == sets2

  h1.put_card(Card.JOKER)
  sets1 = list(iter_sets(h1))
  assert len(sets1) == 5
  assert sorted(sets1) == sorted([
      Set(2, (Color.SPADE, Color.CLUB, Color.DIAMOND)),
      Set(2, (Color.SPADE, Color.CLUB, Color.DIAMOND, None)),
      Set(2, (None, Color.CLUB, Color.DIAMOND)),
      Set(2, (Color.SPADE, None, Color.DIAMOND)),
      Set(2, (Color.SPADE, Color.CLUB, None)),
  ])


def test_lay_regression1():
  """Set iterator should not return duplicates."""
  h = Hand()
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
  assert len(list(iter_melds(h, objective))) == 39
