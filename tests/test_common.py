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
    pass


class TestRun:
    def test_of(self):
        # test run w/ joker_indices = None
        r = Run.of(Color.HEART, start=2, length=4)
        assert r.start == Card.of(2, Color.HEART)
        assert r.length == 4
        assert r.jokers == (False, False, False, False)

        # test run w/ joker_indices = (0, 2)
        r = Run.of(Color.HEART, start=2, length=4, joker_indices=(0, 2))
        assert r.start == Card.of(2, Color.HEART)
        assert r.length == 4
        assert r.jokers == (True, False, True, False)

    def test_iter(self):
        r = Run.of(Color.HEART, start=2, length=4)
        assert list(r) == [
            Card.of(2, Color.HEART),
            Card.of(3, Color.HEART),
            Card.of(4, Color.HEART),
            Card.of(5, Color.HEART)]

        r = Run.of(Color.HEART, start=2, length=4, joker_indices=(0, 2))
        assert list(r) == [
            Card.JOKER,
            Card.of(3, Color.HEART),
            Card.JOKER,
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
        s = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, Color.DIAMOND))
        assert s.rank == Rank.ACE
        assert s.jokers == 0
        assert s.colors == tuple(sorted((Color.HEART, Color.HEART, Color.DIAMOND)))

        s = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, None))
        assert s.rank == Rank.ACE
        assert s.jokers == 1
        assert s.colors == (Color.HEART, Color.HEART)

    def test_equality(self):
        s1 = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, Color.DIAMOND))
        s2 = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, Color.DIAMOND))
        assert s1 == s2
        s3 = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, None))
        assert s1 != s3
        s4 = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, None))
        assert s3 == s4
        s5 = Set(Rank.ACE, colors=(Color.DIAMOND, Color.HEART, Color.HEART))
        assert s1 == s5

    def test_iteration(self):
        s = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, Color.DIAMOND))
        assert list(s) == [
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.DIAMOND),
        ]
        s = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, None))
        assert list(s) == [
            Card.JOKER,
            Card.of(Rank.ACE, Color.HEART),
            Card.of(Rank.ACE, Color.HEART),
        ]

    def test_extend(self):
        s1 = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, Color.DIAMOND))
        c1 = Card.of(Rank.ACE, Color.SPADE)
        s2 = s1.extend(c1)
        assert s2 == Set(Rank.ACE, colors=(Color.HEART, Color.HEART, Color.DIAMOND, Color.SPADE))

        s1 = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, None))
        c1 = Card.of(Rank.ACE, Color.SPADE)
        s2 = s1.extend(c1)
        assert s2 == Set(Rank.ACE, colors=(Color.HEART, Color.HEART, Color.SPADE, None))

        s1 = Set(Rank.ACE, colors=(Color.HEART, Color.HEART, None))
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
        d.take(Card.JOKER)
        d.take(Card.JOKER)
        with pytest.raises(d.InvalidTake):
            d.take(Card.JOKER)
        d.take(Card.of(2, Color.HEART))
        with pytest.raises(d.InvalidTake):
            d.take(Card.of(2, Color.HEART))