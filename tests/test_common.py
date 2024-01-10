import pytest

from liverpool.common import (
    Color,
    Rank,
    Card,
    Run,
    Set,
    Meld,
    Deck
)


def test_color():
    pass


def test_rank():
    pass


def test_card():
    # basic construction
    c = Card.of(2, Color.HEART)
    assert c.rank == 2
    assert c.color == Color.HEART
    assert not c.is_joker

    # joker construction
    c = Card.joker()
    assert c.is_joker
    assert not c.is_materialized
    assert c.rank is None
    assert c.color is None

    # materialized joker construction
    c = Card.of(Rank.ACE, Color.SPADE, joker=True)
    assert c.is_joker
    assert c.is_materialized
    assert c.rank == Rank.ACE
    assert c.color == Color.SPADE



class TestRun:
    def test_of(self):
        # test run w/ joker_indices = None
        r = Run.of(Color.HEART, start=2, length=4)
        assert r.length == 4
        assert r.cards == (
            Card.of(2, Color.HEART),
            Card.of(3, Color.HEART),
            Card.of(4, Color.HEART),
            Card.of(5, Color.HEART)
        )

        # test run w/ joker_indices = (0, 2)
        r = Run.of(Color.HEART, start=2, length=4, joker_indices=(0, 2))
        assert r.length == 4
        assert r.cards == (
            Card.of(2, Color.HEART, joker=True),
            Card.of(3, Color.HEART),
            Card.of(4, Color.HEART, joker=True),
            Card.of(5, Color.HEART)
        )

    def test_iter(self):
        r = Run.of(Color.HEART, start=2, length=4)
        assert list(r) == [
            Card.of(2, Color.HEART),
            Card.of(3, Color.HEART),
            Card.of(4, Color.HEART),
            Card.of(5, Color.HEART)]

        r = Run.of(Color.HEART, start=2, length=4, joker_indices=(0, 2))
        assert list(r) == [
            Card.of(2, Color.HEART, joker=True),
            Card.of(3, Color.HEART),
            Card.of(4, Color.HEART, joker=True),
            Card.of(5, Color.HEART)
        ]

        r = Run.of(Color.HEART, start=Rank.JACK, length=4)
        assert list(r) == [
            Card.of(Rank.JACK, Color.HEART),
            Card.of(Rank.QUEEN, Color.HEART),
            Card.of(Rank.KING, Color.HEART),
            Card.of(Rank.ACE, Color.HEART),
        ]

    def test_iter_left_right(self):
        r = Run.of(Color.HEART, start=4, length=4)
        assert list(r.iter_left()) == [
            Card.of(3, Color.HEART),
            Card.of(2, Color.HEART),
        ]

        r = Run.of(Color.HEART, start=4, length=4, joker_indices=(0, 2))
        assert list(r.iter_left()) == [
            Card.of(3, Color.HEART),
            Card.of(2, Color.HEART),
        ]

        r = Run.of(Color.HEART, start=8, length=4)
        assert list(r.iter_right()) == [
            Card.of(Rank.QUEEN, Color.HEART),
            Card.of(Rank.KING, Color.HEART),
            Card.of(Rank.ACE, Color.HEART),
        ]

        r = Run.of(Color.HEART, start=8, length=4, joker_indices=(1,))
        assert list(r.iter_right()) == [
            Card.of(Rank.QUEEN, Color.HEART),
            Card.of(Rank.KING, Color.HEART),
            Card.of(Rank.ACE, Color.HEART),
        ]

        assert r.right == Card.of(Rank.JACK, Color.HEART)
        assert r.next_right == Card.of(Rank.QUEEN, Color.HEART)
        assert r.left == Card.of(8, Color.HEART)
        assert r.next_left == Card.of(7, Color.HEART)

    def test_equality(self):
        r1 = Run.of(Color.HEART, start=2, length=4)
        r2 = Run.of(Color.HEART, start=2, length=4)
        assert r1 == r2
        r3 = Run.of(Color.HEART, start=2, length=4, joker_indices=(0,))
        assert r1 != r3
        r4 = Run.of(Color.HEART, start=2, length=4, joker_indices=(0,))
        assert r3 == r4
        r5 = Run.of(Color.DIAMOND, start=2, length=4)
        assert r1 != r5

    def test_extend(self):
        r1 = Run.of(Color.HEART, start=2, length=4)
        c1 = Card.of(6, Color.HEART)
        r2 = r1.extend(c1)
        assert r2 == Run.of(Color.HEART, start=2, length=5)

        r1 = Run.of(Color.HEART, start=2, length=4)
        c1 = Card.of(7, Color.HEART)
        with pytest.raises(r1.InvalidExtend):
            r2 = r1.extend(c1)

        r1 = Run.of(Color.HEART, start=2, length=4)
        c1 = Card.of(6, Color.SPADE)
        with pytest.raises(r1.InvalidExtend):
            r2 = r1.extend(c1)

class TestSet:
    def test_construction(self):
        s1 = Set((
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.DIAMOND)
        ))
        assert s1.rank == Rank.ACE
        assert len(s1) == 3
        assert s1 == s1

        s2 = Set((
            Card.of(Rank.ACE, Color.HEART, joker=True),
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.DIAMOND)
        ))
        assert s2.rank == Rank.ACE
        assert s2 == s2
        assert s1 != s2

    def test_equality(self):
        s1 = Set((Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.DIAMOND)))
        s2 = Set((Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.DIAMOND)))
        assert s1 == s2
        s3 = Set((Card.of(Rank.ACE, Color.HEART, joker=True), Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.DIAMOND)))
        assert s1 != s3

    def test_iteration(self):
        s = Set((Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.DIAMOND)))
        assert list(s) == [
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.DIAMOND),
        ]

    def test_extend(self):
        s1 = Set((Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.DIAMOND)))
        c1 = Card.of(Rank.ACE, Color.SPADE)
        s2 = s1.extend(c1)
        assert s2 == Set((
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.DIAMOND),
            Card.of(Rank.ACE, Color.SPADE)))

        s1 = Set((Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.HEART), Card.of(Rank.ACE, Color.DIAMOND, joker=True)))
        c1 = Card.of(Rank.KING, Color.DIAMOND)
        with pytest.raises(s1.InvalidExtend):
            s2 = s1.extend(c1)


class TestMeld:
    pass


class TestDeck:
    def test_new_constructor(self):
        d = Deck.new(1)
        assert len(d) == 54
        d = Deck.new(2)
        assert len(d) == 54*2

    def test_transaction(self):
        d = Deck.new(1)

        # uncaught exception within the contextmanager rolls back transaction
        with pytest.raises(d.EmptyDeck):
            with d:
                for k in range(55):
                    d.pop()
        assert len(d) == 54

        # caught exception within the contextmanager commits transaction
        with d:
            try:
                for k in range(55):
                    d.pop()
            except d.EmptyDeck:
                pass
        assert len(d) == 0

    def test_pop(self):
        d = Deck.new(1)
        assert len(d) == 54
        for k in range(54):
            d.pop()
        assert len(d) == 0
        with pytest.raises(d.EmptyDeck):
            d.pop()

    def test_take(self):
        d = Deck.new(1)
        d.take(Card.joker())
        d.take(Card.joker())
        with pytest.raises(d.InvalidTake):
            d.take(Card.joker())
        d.take(Card.of(2, Color.HEART))
        with pytest.raises(d.InvalidTake):
            d.take(Card.of(2, Color.HEART))

        d = Deck.new(1)
        with pytest.raises(d.InvalidTake):
            # Can't take materialized jokers
            d.take(Card.of(2, Color.HEART, joker=True))