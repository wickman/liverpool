import pytest

from liverpool.common import (
    Card,
    Color,
    Objective,
    Rank,
    Run,
    Set,
)
from liverpool.generation import iter_melds, iter_sets, Extend, extend_from, iter_extends, iter_adds
from liverpool.hand import Hand


def test_set_simple():
  h1 = Hand()
  h1.put_card(Card.of(2, Color.DIAMOND))
  h1.put_card(Card.of(2, Color.CLUB))
  h1.put_card(Card.of(2, Color.SPADE))
  sets1 = list(iter_sets(h1))

  h2 = Hand()
  h2.put_card(Card.of(2, Color.SPADE))
  h2.put_card(Card.of(2, Color.CLUB))
  h2.put_card(Card.of(2, Color.DIAMOND))
  sets2 = list(iter_sets(h2))

  assert len(sets1) == 1
  assert len(sets2) == 1
  assert sets1 == sets2

  h1.put_card(Card.joker())
  sets1 = list(iter_sets(h1))
  assert len(sets1) == 5
  assert sorted(sets1) == sorted([
    Set.of(2, [Color.DIAMOND, Color.CLUB, Color.SPADE]),
    Set.of(2, [Color.DIAMOND, Color.CLUB, Color.SPADE, None]),
    Set.of(2, [         None, Color.CLUB, Color.SPADE]),
    Set.of(2, [Color.DIAMOND,       None, Color.SPADE]),
    Set.of(2, [Color.DIAMOND, Color.CLUB,        None]),
  ])
  assert sorted(sets1) == sorted([
      Set((Card.of(2, Color.SPADE), Card.of(2, Color.CLUB), Card.of(2, Color.DIAMOND))),
      Set((Card.of(2, Color.SPADE), Card.of(2, Color.CLUB), Card.of(2, Color.DIAMOND), Card.of(2, Color.SPADE, joker=True))),
      Set((Card.of(2, Color.SPADE, joker=True), Card.of(2, Color.CLUB), Card.of(2, Color.DIAMOND))),
      Set((Card.of(2, Color.SPADE), Card.of(2, Color.SPADE, joker=True), Card.of(2, Color.DIAMOND))),
      Set((Card.of(2, Color.SPADE), Card.of(2, Color.CLUB), Card.of(2, Color.SPADE, joker=True))),
  ])


def test_lay_regression1():
  """Set iterator should not return duplicates."""
  h = Hand()
  cards = [
    Card.of(2, Color.CLUB),
    Card.of(2, Color.HEART),
    Card.of(2, Color.DIAMOND),
    Card.of(5, Color.SPADE),
    Card.of(5, Color.HEART),
    Card.of(Rank.KING, Color.DIAMOND),
    Card.joker(),
    Card.joker(),
    Card.joker(),
    Card.joker(),
  ]

  for card in cards:
    h.put_card(card)

  objective = Objective(3, 0)

  assert len(list(iter_melds(h, objective))) == 26

def test_extend_from():
    # no-op extend raises InvalidExtend
    r1 = Run.of(Color.HEART, start=2, jokers=4*[False])
    r2 = Run.of(Color.HEART, start=2, jokers=4*[False])
    with pytest.raises(ValueError):
      e = extend_from(r1, r2)

    # extend right
    r2 = Run.of(Color.HEART, start=2, jokers=5*[False])
    e = extend_from(r1, r2)
    assert e.run == r1
    assert e.left == []
    assert e.right == [Card.of(6, Color.HEART)]

    # extend left
    r1 = Run.of(Color.HEART, start=3, jokers=4*[False])
    r2 = Run.of(Color.HEART, start=2, jokers=5*[False])
    e = extend_from(r1, r2)
    assert e.run == r1
    assert e.left == [Card.of(2, Color.HEART)]
    assert e.right == []

    # extend left and right
    r1 = Run.of(Color.HEART, start=3, jokers=4*[False])
    r2 = Run.of(Color.HEART, start=2, jokers=6*[False])
    e = extend_from(r1, r2)
    assert e.run == r1
    assert e.left == [Card.of(2, Color.HEART)]
    assert e.right == [Card.of(7, Color.HEART)]

def test_iter_extends():
  h = Hand()
  cards = [
    Card.of(2, Color.CLUB),
    Card.of(2, Color.HEART),
    Card.of(2, Color.DIAMOND),
  ]
  for card in cards:
    h.put_card(card)
  
  run = Run.of(Color.HEART, start=3, jokers=4*[False])

  all_extends = list(iter_extends(h, run))
  assert len(all_extends) == 2
  assert all_extends[0].run == run
  assert all_extends[0].left == all_extends[0].right == []
  assert all_extends[1].run == run
  assert all_extends[1].left == [Card.of(2, Color.HEART)]
  assert all_extends[1].right == []

def test_iter_adds():
  h = Hand()
  cards = [
    Card.of(2, Color.CLUB),
    Card.of(3, Color.HEART),
  ]
  for card in cards:
    h.put_card(card)
  
  s = Set.of(2, [Color.CLUB, Color.HEART, Color.DIAMOND])

  all_adds = list(iter_adds(h, s))
  assert len(all_adds) == 2
  assert all_adds[0] == []
  assert all_adds[1] == [Card.of(2, Color.CLUB)]
