from liverpool.common import (
    Card,
    Color,
    Rank,
    Set,
)
from liverpool.hand import Hand


def test_set_simple():
  h1 = Hand()
  h1.put_card(Card(Color.DIAMOND, 2))
  h1.put_card(Card(Color.CLUB, 2))
  h1.put_card(Card(Color.SPADE, 2))
  sets1 = list(h1.iter_sets())

  h2 = Hand()
  h2.put_card(Card(Color.SPADE, 2))
  h2.put_card(Card(Color.CLUB, 2))
  h2.put_card(Card(Color.DIAMOND, 2))
  sets2 = list(h2.iter_sets())

  assert len(sets1) == 1
  assert len(sets2) == 1
  assert sets1 == sets2

  h1.put_card(Card.JOKER)
  sets1 = list(h1.iter_sets())
  assert len(sets1) == 5
  assert sorted(sets1) == sorted([
      Set(2, (Color.SPADE, Color.CLUB, Color.DIAMOND)),
      Set(2, (Color.SPADE, Color.CLUB, Color.DIAMOND, None)),
      Set(2, (None, Color.CLUB, Color.DIAMOND)),
      Set(2, (Color.SPADE, None, Color.DIAMOND)),
      Set(2, (Color.SPADE, Color.CLUB, None)),
  ])
