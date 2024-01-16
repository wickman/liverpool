from contextlib import contextmanager
from dataclasses import dataclass
import random
import sys

from typing import Iterable, List, Optional, Union, Tuple, Dict


class Serializable:
    def serialize(self) -> str:
        raise NotImplementedError

    @classmethod
    def deserialize(cls, s: str):
        raise NotImplementedError


class Color:
    """Color of a card."""

    class Error(Exception):
        pass

    class InvalidColor(Error):
        pass

    CLUB = MIN = 0
    SPADE = 1
    HEART = 2
    DIAMOND = MAX = 3

    COLORS = {
        CLUB: "CLUB",
        SPADE: "SPADE",
        HEART: "HEART",
        DIAMOND: "DIAMOND",
    }

    POKER_COLORS = {
        CLUB: "c",
        SPADE: "s",
        HEART: "h",
        DIAMOND: "d",
    }

    WHITE_UNICODE_COLORS = {
        CLUB: "\u2663",
        SPADE: "\u2660",
        HEART: "\u2665",
        DIAMOND: "\u2666",
    }

    BLACK_UNICODE_COLORS = {
        CLUB: "\u2667",
        SPADE: "\u2664",
        HEART: "\u2661",
        DIAMOND: "\u2662",
    }

    MIXED_UNICODE_COLORS = {
        CLUB: "\u2667",
        SPADE: "\u2664",
        HEART: "\u2665",
        DIAMOND: "\u2666",
    }

    UNICODE_COLORS = MIXED_UNICODE_COLORS

    @classmethod
    def validate(cls, color: int) -> int:
        if color not in cls.COLORS:
            raise cls.InvalidColor("Unknown color: %s" % color)
        return color

    @classmethod
    def to_str(cls, color: int) -> str:
        return cls.UNICODE_COLORS[cls.validate(color)]

    @classmethod
    def to_repr(cls, color: int) -> str:
        return "%s.%s" % (cls.__name__, cls.COLORS[cls.validate(color)])

    @classmethod
    def iter(cls) -> Iterable[int]:
        return iter((cls.CLUB, cls.SPADE, cls.HEART, cls.DIAMOND))


class Rank:
    """Rank of a card."""

    class Error(Exception):
        pass

    class InvalidRank(Error):
        pass

    FACES = {
        11: "J",
        12: "Q",
        13: "K",
        14: "A",
    }

    FACES_REPR = {
        11: "JACK",
        12: "QUEEN",
        13: "KING",
        14: "ACE",
    }

    MIN = 2
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = MAX = 14

    RANK_TO_POKER = {
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "T",
        JACK: "J",
        QUEEN: "Q",
        KING: "K",
        ACE: "A",
        None: "?",
    }

    POKER_TO_RANK = {v: k for k, v in RANK_TO_POKER.items()}

    @classmethod
    def validate(cls, rank) -> int:
        if rank < cls.MIN or rank > cls.MAX:
            raise cls.InvalidRank(
                "Rank must be be between [%d, %d], got %s" % (cls.MIN, cls.MAX, rank)
            )
        return rank

    @classmethod
    def to_str(cls, rank) -> str:
        return cls.FACES.get(cls.validate(rank), str(rank))

    @classmethod
    def to_repr(cls, rank) -> str:
        if rank in cls.FACES_REPR:
            return "%s.%s" % (cls.__name__, cls.FACES_REPR[rank])
        else:
            return cls.to_str(rank)

    @classmethod
    def iter(cls) -> Iterable[int]:
        return range(cls.MIN, cls.MAX + 1)


# These are optimizations to attempt to avoid card construction in the Combo path.
JOKER_MASK = 1 << 6


def card_color(value: int) -> Optional[int]:
    masked_value = value & ~JOKER_MASK
    return None if masked_value == 0 else masked_value % (Rank.MAX + 1)


def card_rank(value: int) -> Optional[int]:
    masked_value = value & ~JOKER_MASK
    return None if masked_value == 0 else masked_value // (Rank.MAX + 1)


class Card:
    """A card in the game of Liverpool."""

    SCORES = {
        2: 5,
        3: 5,
        4: 5,
        5: 5,
        6: 5,
        7: 5,
        8: 5,
        9: 5,
        10: 10,
        Rank.JACK: 10,
        Rank.QUEEN: 10,
        Rank.KING: 10,
        Rank.ACE: 15,
    }

    __slots__ = ("value",)

    MIN = Rank.MIN + Color.MIN * (Rank.MAX + 1)
    MAX = Rank.MAX + Color.MAX * (Rank.MAX + 1)
    _JOKER_MASK = 1 << 6
    JOKER_VALUE = _JOKER_MASK

    @classmethod
    def deserialize(cls, s: str) -> "Card":
        pass

    @classmethod
    def joker(cls) -> "Card":
        return cls(cls._JOKER_MASK)

    @classmethod
    def of(cls, rank: int, color: int, joker: bool = False) -> "Card":
        return cls(
            Rank.validate(rank)
            + Color.validate(color) * (Rank.MAX + 1)
            + (cls._JOKER_MASK if joker else 0)
        )

    def __init__(self, value: int):
        self.value = value
        if not isinstance(value, int):
            raise TypeError("Card value must be an integer, got %s" % type(value))
        masked_value = value & ~self._JOKER_MASK
        if masked_value != 0 and (masked_value < self.MIN or masked_value > self.MAX):
            raise ValueError("Invalid card value: %s" % value)

    @property
    def score(self) -> int:
        return 15 if self.is_joker else self.SCORES[self.rank]

    @property
    def is_joker(self) -> bool:
        return (self.value & self._JOKER_MASK) != 0

    @property
    def is_materialized(self) -> bool:
        return (self.value & ~self._JOKER_MASK) != 0

    @property
    def color(self) -> Optional[int]:
        masked_value = self.value & ~self._JOKER_MASK
        return None if masked_value == 0 else masked_value // (Rank.MAX + 1)

    @property
    def rank(self) -> Optional[int]:
        masked_value = self.value & ~self._JOKER_MASK
        return None if masked_value == 0 else masked_value % (Rank.MAX + 1)

    def as_common(self) -> "Card":
        """Return a de-jokerified version of this card.

        If called with an unmaterialized Joker, will return a rank/color validation error.
        """
        return Card.of(self.rank, self.color)

    def materialize(self, rank: int, color: int = 0) -> "Card":
        """Pin a joker to a specific rank and color."""
        if not self.is_joker:
            raise ValueError("Cannot materialize a non-joker card.")
        return Card.of(rank, color, joker=True)

    def dematerialized(self) -> "Card":
        """Return a version of this card without any materialization.

        If called with a materialized Joker, the materialization will be stripped. If
        called with any other card, the card itself will be returned unchanged."""
        if self.is_joker:
            return Card.joker()
        else:
            return self

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        if not isinstance(other, Card):
            raise TypeError
        return self.value < other.value

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.value == other.value

    def __str__(self):
        if self.value == self._JOKER_MASK:
            return "??"
        return "%s%s%s" % (
            Rank.to_str(self.rank),
            Color.to_str(self.color),
            "?" if self.is_joker else "",
        )

    def __repr__(self):
        if self.value == self._JOKER_MASK:
            return "%s.joker()" % self.__class__.__name__
        return "%s.of(%s, %s%s)" % (
            self.__class__.__name__,
            Rank.to_repr(self.rank),
            Color.to_repr(self.color),
            ", joker=True" if self.is_joker else "",
        )


class Extend:
    """A union of two runs that yields the overlapping run and extensions to the left and right."""

    __slots__ = ("left", "right")

    def __init__(
        self,
        left: Optional[List[Card]] = None,
        right: Optional[List[Card]] = None,
    ) -> None:
        self.left: List[Card] = left if left is not None else []
        self.right: List[Card] = right if right is not None else []

    def __len__(self):
        return len(self.left) + len(self.right)

    def __iter__(self):
        return iter(self.left + self.right)

    def __str__(self):
        run_str = "()"
        if self.left:
            run_str = " ".join("%s" % card for card in self.left) + "++" + run_str
        if self.right:
            run_str += "++" + " ".join("%s" % card for card in self.right)
        return run_str

    def __repr__(self):
        # return "Extend(%r, %r)" % (self.left, self.right)
        return str(self)

    def __bool__(self) -> bool:
        return bool(self.left or self.right)


# TODO Runs and Sets are now just bytes() and can inherit a base class
# which would include the following methods:
#   .length, __len__
#   __hash__
#   __lt__ __gt__ __eq__
#   __iter__
#   .score
#   __str__


class Combo:
    """A combo of cards."""

    class Error(Exception):
        pass

    __slots__ = ("cards",)

    def __init__(self, cards: Iterable[Card]) -> None:
        if not isinstance(cards, (tuple, list)):
            raise TypeError("Expected cards to be a tuple/list of cards.")
        # Rely on AttributeError instead here instead of an expensive check.
        # if not all(isinstance(card, Card) for card in cards):
        #    raise TypeError("Expected cards to be a tuple/list of cards.")
        self.cards = bytes(card.value for card in cards)

    @property
    def score(self) -> int:
        return sum(Card(value).score for value in self.cards)

    @property
    def length(self) -> int:
        return len(self.cards)

    def __len__(self) -> int:
        return self.length

    def __hash__(self) -> int:
        return hash(self.cards)

    def __lt__(self, other) -> bool:
        return self.cards < other.cards

    def __eq__(self, other) -> bool:
        return self.cards == other.cards

    def __iter__(self) -> Iterable[Card]:
        """Iterate over the cards in the run."""
        for value in self.cards:
            yield Card(value)

    def __str__(self) -> str:
        return " ".join("%s" % card for card in self)

    def __repr__(self):
        return "%s([%s])" % (
            self.__class__.__name__,
            ", ".join(map(repr, self)),
        )


class Run(Combo):
    """A run of cards of the same color."""

    class InvalidExtend(Combo.Error):
        pass

    MIN = 4

    @classmethod
    def of(cls, color: int, start: int, jokers: List[bool]) -> "Run":
        if not isinstance(color, int):
            raise TypeError("Expected color to be an integer, got %s" % type(color))
        if not isinstance(start, int) or start < Rank.MIN or start > Rank.MAX:
            raise TypeError(
                "Expected start to be an integer between %d and %d, got %s"
                % (Rank.MIN, Rank.MAX, start)
            )
        if len(jokers) < cls.MIN:
            raise TypeError(
                "Expected length to be an integer >= %d, got %s" % (cls.MIN, len(jokers))
            )
        cards = [Card.of(start + offset, color, joker) for offset, joker in enumerate(jokers)]
        return cls(cards)

    def __init__(self, cards: Iterable[Card]) -> None:
        super(Run, self).__init__(cards)
        if self.length < self.MIN:
            raise ValueError("Expected at least %d cards, got %d" % (self.MIN, len(cards)))
        if not all(card.color == self.color for card in cards):
            raise ValueError("Expected all cards to be the same color.")
        for index, card in enumerate(cards):
            if card.rank != cards[0].rank + index:
                raise ValueError("Expected cards to be in ascending order.")

    @property
    def color(self) -> int:
        return Card(self.cards[0]).color

    @property
    def left(self) -> Card:
        return Card(self.cards[0])

    @property
    def next_left(self) -> Optional[Card]:
        return Card.of(self.left.rank - 1, self.left.color) if self.left.rank > Rank.MIN else None

    @property
    def right(self) -> Card:
        return Card(self.cards[-1])

    @property
    def next_right(self) -> Optional[Card]:
        return (
            Card.of(self.right.rank + 1, self.right.color) if self.right.rank < Rank.MAX else None
        )

    def extend(self, card: Card) -> "Run":
        if not isinstance(card, Card):
            raise TypeError("Expected card to be a Card, got %s" % type(card))
        common_card = card.as_common()
        if common_card == self.next_left:
            return Run((card,) + tuple(Card(value) for value in self.cards))
        elif common_card == self.next_right:
            return Run(tuple(Card(value) for value in self.cards) + (card,))
        else:
            raise self.InvalidExtend("Card does not extend the run.")

    def update(self, extend: Extend) -> "Run":
        if not isinstance(extend, Extend):
            raise TypeError("Expected extend to be an Extend, got %s" % type(extend))
        return Run(extend.left + list(self) + extend.right)

    def iter_left(self) -> Iterable[Card]:
        """Iterate, descending, over the cards to the left of the run."""
        if self.next_left:
            for rank in range(self.next_left.rank, Rank.MIN - 1, -1):
                yield Card.of(rank, self.color)

    def iter_right(self) -> Iterable[Card]:
        """Iterate, ascending, over the cards to the right of the run."""
        if self.next_right:
            for rank in range(self.next_right.rank, Rank.MAX + 1):
                yield Card.of(rank, self.color)


class Add(list):
    """A list of cards that can be added to a set."""

    def __str__(self):
        return " ".join("%s" % card for card in self)

    def __repr__(self):
        return str(self)


class Set(Combo):
    class InvalidExtend(Combo.Error):
        pass

    MIN = 3
    DEFAULT_JOKER_COLOR = Color.SPADE

    @classmethod
    def of(cls, rank: int, colors: Iterable[Optional[int]]) -> "Set":
        if not isinstance(rank, int) or rank < Rank.MIN or rank > Rank.MAX:
            raise TypeError(
                "Expected rank to be an integer between %d and %d, got %s"
                % (Rank.MIN, Rank.MAX, rank)
            )
        if not isinstance(colors, (tuple, list)):
            raise TypeError("Expected colors to be a tuple/list of integers.")
        # it is policy for the sake of sets to materialize jokers as a consistent color every time
        cards = [
            Card.of(rank, color)
            if color is not None
            else Card.of(rank, cls.DEFAULT_JOKER_COLOR, joker=True)
            for color in colors
        ]
        return cls(cards)

    def __init__(self, cards: Iterable[Card]) -> None:
        super(Set, self).__init__(sorted(cards))
        if len(self.cards) < self.MIN:
            raise ValueError("Expected at least %d cards, got %d" % (self.MIN, len(cards)))
        if not all(card.rank == cards[0].rank for card in cards):
            raise ValueError("Expected all cards to be the same rank.")

    @property
    def rank(self) -> int:
        return Card(self.cards[0]).rank

    def extend(self, card: Card) -> "Set":
        if not isinstance(card, Card):
            raise TypeError("Expected card to be a Card, got %s" % type(card))
        if card.rank != self.rank:
            raise self.InvalidExtend("Card does not match set rank.")
        return Set(tuple(Card(card) for card in self.cards) + (card,))

    def update(self, add: Add) -> "Set":
        if not isinstance(add, Add):
            raise TypeError("Expected add to be an Add, got %s" % type(add))
        if not all(isinstance(card, Card) for card in add):
            raise TypeError("Expected add to be a list of Cards.")
        if not all(card.rank == self.rank for card in add):
            raise ValueError("Expected all cards to be the same rank.")
        return Set(tuple(Card(value) for value in self.cards) + tuple(add))


class CardSet(list):
    def __hash__(self):
        return hash(bytes(card.value for card in self))

    def __str__(self):
        return " ".join(str(card) for card in self)


class Objective(object):
    def __init__(self, num_sets, num_runs):
        if not isinstance(num_sets, int) or num_sets < 0:
            raise TypeError("Number of sets must be a non-negative integer.")
        if not isinstance(num_runs, int) or num_runs < 0:
            raise TypeError("Number of runs must be a non-negative integer.")
        self.num_sets = num_sets
        self.num_runs = num_runs

    def __str__(self):
        return "%d sets / %d runs" % (self.num_sets, self.num_runs)


class MeldUpdate:
    def __init__(
        self, adds: Optional[Dict[int, Add]] = None, extends: Optional[Dict[int, Extend]] = None
    ) -> None:
        self.adds = adds or {}
        self.extends = extends or {}

    def __iter__(self):
        for add in self.adds.values():
            yield from add
        for extend in self.extends.values():
            yield from extend

    def __repr__(self):
        return "MeldUpdate(%s%s%s)" % (
            "adds=%r" % self.adds if self.adds else "",
            ", " if self.adds and self.extends else "",
            "extends=%r" % self.extends if self.extends else "",
        )


class Meld:
    """A collection of sets and runs."""

    @classmethod
    def of(cls, combos: Iterable[Combo]) -> "Meld":
        sets = []
        runs = []
        for combo in combos:
            if isinstance(combo, Set):
                sets.append(combo)
            elif isinstance(combo, Run):
                runs.append(combo)
            else:
                raise TypeError("Expected combo to be a Set or Run, got %s" % type(combo))
        return cls(sorted(sets), sorted(runs))

    def __init__(
        self, sets: Optional[Iterable[Set]] = None, runs: Optional[Iterable[Run]] = None
    ) -> None:
        self.sets = tuple(sets) if sets is not None else ()
        self.runs = tuple(runs) if runs is not None else ()
        self._cards = bytes(b"".join(combo.cards for combo in self))
        if not all(isinstance(set_, Set) for set_ in self.sets):
            raise TypeError("sets must be instances of Set.")
        if not all(isinstance(run, Run) for run in self.runs):
            raise TypeError("runs must be instances of Run.")

    @property
    def score(self) -> int:
        return sum(card.score for combo in self for card in combo)

    def _as_tuple(self):
        return tuple(self.sets + self.runs)

    def __iter__(self):
        return iter(self._as_tuple())

    def enumerate(self):
        return enumerate(self)

    def __eq__(self, other):
        if not isinstance(other, Meld):
            return False
        return self._cards == other._cards

    def __lt__(self, other):
        if not isinstance(other, Meld):
            raise TypeError("Expected other to be a Meld, got %s" % type(other))
        return self._cards < other._cards

    def __len__(self):
        return len(self._cards)

    def __str__(self):
        return "Meld(%s)" % "   ".join("%s" % combo for combo in (self.sets + self.runs))

    def update(self, update: MeldUpdate) -> "Meld":
        meld_sets = list(self.sets)
        meld_runs = list(self.runs)
        for add_id, add in update.adds.items():
            meld_sets[add_id] = meld_sets[add_id].update(add)
        for extend_id, extend in update.extends.items():
            meld_runs[extend_id] = meld_runs[extend_id].update(extend)
        return Meld(meld_sets, meld_runs)


class Deck:
    class Error(Exception):
        pass

    class InvalidTake(Error):
        pass

    class EmptyDeck(Error):
        pass

    _RANDOM = random.Random()

    @classmethod
    def seed(cls, x=None):
        cls._RANDOM.seed(x)

    @classmethod
    def new(cls, count=1) -> "Deck":
        cards = []
        for _ in range(count):
            for rank in Rank.iter():
                for color in Color.iter():
                    cards.append(Card.of(rank, color))
            for _ in range(2):
                cards.append(Card.joker())
        cls._RANDOM.shuffle(cards)
        return cls(cards)

    def __init__(self, cards: List[Card]):
        self.cards: List[Card] = cards
        self.__saved_cards: Optional[List[Card]] = None
        if not all(isinstance(card, Card) for card in self.cards):
            raise TypeError("Expected cards to be a list of Card, got %s" % type(cards))

    def __len__(self):
        return len(self.cards)

    def shuffle(self):
        self._RANDOM.shuffle(self.cards)

    def pop(self):
        try:
            return self.cards.pop()
        except IndexError:
            raise self.EmptyDeck("Deck is empty.")

    def put(self, card):
        self.cards.insert(0, card)

    def take(self, card):
        try:
            self.cards.remove(card)
        except ValueError:
            raise self.InvalidTake("Card not in deck.")

    def __enter__(self):
        assert self.__saved_cards is None, "Already in a transaction."
        self.__saved_cards = self.cards[:]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert self.__saved_cards is not None, "Not in a transaction."
        if exc_type is None:
            self.__saved_cards = None
        else:
            self.cards = self.__saved_cards
            self.__saved_cards = None
