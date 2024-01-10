from contextlib import contextmanager
from dataclasses import dataclass
import random
import sys

from typing import Iterable, List, Optional, Union, Tuple


class Color:
  """Color of a card."""

  class Error(Exception): pass
  class InvalidColor(Error): pass

  CLUB = MIN = 0
  SPADE = 1
  HEART = 2
  DIAMOND = MAX = 3

  COLORS = {
    CLUB: 'CLUB',
    SPADE: 'SPADE',
    HEART: 'HEART',
    DIAMOND: 'DIAMOND',
  }

  WHITE_UNICODE_COLORS = {
    CLUB: u'\u2663',
    SPADE: u'\u2660',
    HEART: u'\u2665',
    DIAMOND: u'\u2666',
  }

  BLACK_UNICODE_COLORS = {
    CLUB: u'\u2667',
    SPADE: u'\u2664',
    HEART: u'\u2661',
    DIAMOND: u'\u2662',
  }

  MIXED_UNICODE_COLORS = {
    CLUB: u'\u2667',
    SPADE: u'\u2664',
    HEART: u'\u2665',
    DIAMOND: u'\u2666',
  }

  UNICODE_COLORS = MIXED_UNICODE_COLORS

  @classmethod
  def validate(cls, color: int) -> int:
    if color not in cls.COLORS:
      raise cls.InvalidColor('Unknown color: %s' % color)
    return color

  @classmethod
  def to_str(cls, color: int) -> str:
    return cls.UNICODE_COLORS[cls.validate(color)]

  @classmethod
  def to_repr(cls, color: int) -> str:
    return '%s.%s' % (cls.__name__, cls.COLORS[cls.validate(color)])

  @classmethod
  def iter(cls) -> Iterable[int]:
    return iter((cls.CLUB, cls.SPADE, cls.HEART, cls.DIAMOND))


class Rank:
  """Rank of a card."""

  class Error(Exception): pass
  class InvalidRank(Error): pass

  FACES = {
    11: 'J',
    12: 'Q',
    13: 'K',
    14: 'A',
  }

  FACES_REPR = {
    11: 'JACK',
    12: 'QUEEN',
    13: 'KING',
    14: 'ACE',
  }

  MIN = 2
  JACK = 11
  QUEEN = 12
  KING = 13
  ACE = MAX = 14

  @classmethod
  def validate(cls, rank) -> int:
    if rank < cls.MIN or rank > cls.MAX:
      raise cls.InvalidRank('Rank must be be between [%d, %d], got %s' % (cls.MIN, cls.MAX, rank))
    return rank

  @classmethod
  def to_str(cls, rank) -> str:
    return cls.FACES.get(cls.validate(rank), str(rank))

  @classmethod
  def to_repr(cls, rank) -> str:
    if rank in cls.FACES_REPR:
      return '%s.%s' % (cls.__name__, cls.FACES_REPR[rank])
    else:
      return cls.to_str(rank)

  @classmethod
  def iter(cls) -> Iterable[int]:
    return range(cls.MIN, cls.MAX + 1)


"""
Right now Card has a single integer as its storage.  It represents a JOKER as 0,
and all other cards as rank + color * (rank.max + 1), where rank is 2..14 and color is
0..3.  This means that valid values are Card.min (2) to Card.max (59), which fits within
5 bits.

We should be able to set the 7th bit (64) to indicate that this is a materialized joker.
That means that it's a Joker but it's been materialized to a specific rank and color.
We need to be more careful this way but it makes a *lot* of things easier, assuming
we minimize the number of places where this logic needs to take place, specifically
around things like move generation and meld editing.

We should have a method on Card that materializes a Joker into a materialized joker, i.e.
Card.materialize(rank, color) -> Card that asserts ValueError if it's not a joker.

This doesn't require any meaningful changes to Hand.
We should reimplement Run so that it is a proper sequence of Cards with materialized jokers.
We should reimplement Set so that it's a Set of Cards with materialized jokers.
"""

class Card:
  """A card in the game of Liverpool."""

  __slots__ = ('value',)

  MIN = Rank.MIN + Color.MIN * (Rank.MAX + 1)
  MAX = Rank.MAX + Color.MAX * (Rank.MAX + 1)
  _JOKER_MASK = 1 << 6
  JOKER_VALUE = _JOKER_MASK

  @classmethod
  def joker(cls) -> "Card":
    return cls(cls._JOKER_MASK)

  @classmethod
  def of(cls, rank: int, color: int, joker: bool = False) -> "Card":
    return cls(Rank.validate(rank) + Color.validate(color) * (Rank.MAX + 1) + (cls._JOKER_MASK if joker else 0))

  def __init__(self, value: int):
    self.value = value
    if not isinstance(value, int):
      raise TypeError('Card value must be an integer, got %s' % type(value))
    masked_value = value & ~self._JOKER_MASK
    if masked_value != 0 and (masked_value < self.MIN or masked_value > self.MAX):
      raise ValueError('Invalid card value: %s' % value)

  @property
  def is_joker(self) -> bool:
    return (self.value & self._JOKER_MASK) != 0

  @property
  def is_materialized(self) -> bool:
    return (self.value & ~self._JOKER_MASK) != 0

  @property
  def color(self) -> int:
    masked_value = self.value & ~self._JOKER_MASK
    return None if masked_value == 0 else masked_value // (Rank.MAX + 1)

  @property
  def rank(self) -> int:
    masked_value = self.value & ~self._JOKER_MASK
    return None if masked_value == 0 else masked_value % (Rank.MAX + 1)

  def as_common(self) -> "Card":
    # return the card as a non-joker variant
    return Card.of(self.rank, self.color)

  def materialize(self, rank: int, color: int = 0) -> "Card":
    if not self.is_joker:
      raise ValueError('Cannot materialize a non-joker card.')
    return Card.of(rank, color, joker=True)

  def dematerialized(self) -> "Card":
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
      return '??'
    return '%s%s%s' % (Rank.to_str(self.rank), Color.to_str(self.color), '?' if self.is_joker else '')

  def __repr__(self):
    if self.value == self._JOKER_MASK:
      return '%s.joker()' % self.__class__.__name__
    return '%s.of(%s, %s%s)' % (
        self.__class__.__name__,
        Rank.to_repr(self.rank),
        Color.to_repr(self.color),
        ', joker=True' if self.is_joker else '')




class Run:
  """A run of cards of the same color."""

  class Error(Exception): pass
  class InvalidExtend(Exception): pass

  __slots__ = ('cards',)

  MIN = 4

  @classmethod
  def of(cls, color: int, start: int, jokers: List[bool]) -> "Run":
    if not isinstance(color, int):
      raise TypeError('Expected color to be an integer, got %s' % type(color))
    if not isinstance(start, int) or start < Rank.MIN or start > Rank.MAX:
      raise TypeError('Expected start to be an integer between %d and %d, got %s' % (
          Rank.MIN, Rank.MAX, start))
    if len(jokers) < cls.MIN:
      raise TypeError('Expected length to be an integer >= %d, got %s' % (cls.MIN, len(jokers)))
    cards = [Card.of(start + offset, color, joker) for offset, joker in enumerate(jokers)]
    return cls(cards)

  def __init__(self, cards: Iterable[Card]) -> None:
    if not isinstance(cards, (tuple, list)):
      raise TypeError('Expected cards to be a tuple/list of cards.')
    if len(cards) < self.MIN:
      raise ValueError('Expected at least %d cards, got %d' % (self.MIN, len(cards)))
    if not all(isinstance(card, Card) for card in cards):
      raise TypeError('Expected cards to be a tuple/list of cards.')
    if not all(card.color == cards[0].color for card in cards):
      raise ValueError('Expected all cards to be the same color.')
    for index, card in enumerate(cards):
      if card.rank != cards[0].rank + index:
        raise ValueError('Expected cards to be in ascending order.')
    self.cards = tuple(cards)

  @property
  def color(self) -> int:
    return self.cards[0].color

  @property
  def length(self) -> int:
    return len(self.cards)

  @property
  def left(self) -> Card:
    return self.cards[0]

  @property
  def next_left(self) -> Optional[Card]:
    return Card.of(self.left.rank - 1, self.left.color) if self.left.rank > Rank.MIN else None

  @property
  def right(self) -> Card:
    return self.cards[-1]

  @property
  def next_right(self) -> Optional[Card]:
    return Card.of(self.right.rank + 1, self.right.color) if self.right.rank < Rank.MAX else None

  def extend(self, card: Card) -> "Run":
    if not isinstance(card, Card):
      raise TypeError('Expected card to be a Card, got %s' % type(card))
    common_card = card.as_common()
    if common_card == self.next_left:
      return Run((card,) + self.cards)
    elif common_card == self.next_right:
      return Run(self.cards + (card,))
    else:
      raise self.InvalidExtend('Card does not extend the run.')

  def __len__(self):
    return self.length

  def __hash__(self):
    return hash(b'run' + b''.join(card.value.to_bytes(1, 'big') for card in self.cards))

  def __eq__(self, other):
    if not isinstance(other, Run):
      return False
    return self.cards == other.cards

  def __iter__(self) -> Iterable[Card]:
    """Iterate over the cards in the run."""
    for card in self.cards:
      yield card

  def iter_left(self) -> Iterable[Card]:
    """Iterate, descending, over the cards to the left of the run."""
    for rank in range(self.next_left.rank, Rank.MIN - 1, -1):
      yield Card.of(rank, self.color)

  def iter_right(self) -> Iterable[Card]:
    """Iterate, ascending, over the cards to the right of the run."""
    for rank in range(self.next_right.rank, Rank.MAX + 1):
      yield Card.of(rank, self.color)

  def __str__(self):
    return ' '.join('%s' % card for card in self)

  def __repr__(self):
    return '%s.from_cards(%s)' % (self.__class__.__name__, ', '.join(map(repr, self)))


class Set(object):
  __slots__ = ('cards',)

  class Error(Exception): pass
  class InvalidExtend(Exception): pass

  MIN = 3

  @classmethod
  def of(cls, rank: int, colors: Iterable[Optional[int]]) -> "Set":
    if not isinstance(rank, int) or rank < Rank.MIN or rank > Rank.MAX:
      raise TypeError('Expected rank to be an integer between %d and %d, got %s' % (
          Rank.MIN, Rank.MAX, rank))
    if not isinstance(colors, (tuple, list)):
      raise TypeError('Expected colors to be a tuple/list of integers.')
    # it is policy for the sake of sets to materialize jokers as a consistent color every time
    cards = [Card.of(rank, color) if color is not None else Card.of(rank, Color.SPADE, joker=True)
             for color in colors]
    return cls(cards)

  def __init__(self, cards: Iterable[Card]) -> None:
    if not isinstance(cards, (tuple, list)):
      raise TypeError('Expected cards to be a tuple/list of cards.')
    if not all(isinstance(card, Card) for card in cards):
      raise TypeError('Expected cards to be a tuple/list of cards.')
    if len(cards) < self.MIN:
      raise ValueError('Expected at least %d cards, got %d' % (self.MIN, len(cards)))
    if not all(card.rank == cards[0].rank for card in cards):
      raise ValueError('Expected all cards to be the same rank.')
    self.cards = tuple(sorted(cards))

  @property
  def rank(self) -> int:
    return self.cards[0].rank

  def extend(self, card: Card) -> "Set":
    if not isinstance(card, Card):
      raise TypeError('Expected card to be a Card, got %s' % type(card))
    if card.rank != self.rank:
      raise self.InvalidExtend('Card does not match set rank.')
    return Set(self.cards + (card,))

  @property
  def length(self) -> int:
    return len(self.cards)

  def __len__(self):
    return self.length

  def _as_tuple(self):
    return self.cards

  def __hash__(self):
    return hash(b'set' + b''.join(card.value.to_bytes(1, 'big') for card in self.cards))

  def __lt__(self, other):
    if not isinstance(other, Set):
      raise TypeError('Expected other to be a Set, got %s' % type(other))
    return self._as_tuple() < other._as_tuple()

  def __eq__(self, other):
    if not isinstance(other, Set):
      return False
    return self.cards == other.cards

  def __iter__(self):
    for card in self.cards:
      yield card

  def __str__(self):
    return ' '.join('%s' % card for card in self.cards)

  def __repr__(self):
    return '%s((%s))' % (self.__class__.__name__, ', '.join(map(repr, self)))


class Objective(object):
  def __init__(self, num_sets, num_runs):
    if not isinstance(num_sets, int) or num_sets < 0:
      raise TypeError('Number of sets must be a non-negative integer.')
    if not isinstance(num_runs, int) or num_runs < 0:
      raise TypeError('Number of runs must be a non-negative integer.')
    self.num_sets = num_sets
    self.num_runs = num_runs


@dataclass
class MeldEdit:
  """An edit to a meld.

  Runs can be edited by adding or removing cards from the left or right.
  Sets can be edited by adding or removing cards of the same Rank.

  Run.extend(card, as_joker=False)
  Set.extend(card)
  """
  run_edits: List[Tuple[int, List[Card]]]
  set_edits: List[Tuple[int, List[Card]]]


class Meld:
  """A collection of sets and runs."""

  def __init__(self, sets: Optional[Iterable[Set]] = None, runs: Optional[Iterable[Run]] = None) -> None:
    self.sets = tuple(sets) if sets is not None else ()
    self.runs = tuple(runs) if runs is not None else ()
    if not all(isinstance(set_, Set) for set_ in self.sets):
      raise TypeError('sets must be instances of Set.')
    if not all(isinstance(run, Run) for run in self.runs):
      raise TypeError('runs must be instances of Run.')

  def _as_tuple(self):
    return tuple(self.sets + self.runs)

  def __iter__(self):
    return iter(self._as_tuple())

  def enumerate(self):
    return enumerate(self)

  """
  def extend(self, edit: MeldEdit) -> "Meld":
    sets = self.sets[:]
    runs = self.runs[:]
    for index, cards in edit.set_edits:
      for card in cards:
        sets[index] = sets[index].extend(card)
    for index, cards in edit.run_edits:
  """

  def __eq__(self, other):
    if not isinstance(other, Meld):
      return False
    return self._as_tuple() == other._as_tuple()

  def __len__(self):
    return sum(len(list(s)) for s in self.sets) + sum(len(list(r)) for r in self.runs)

  def __str__(self):
    return 'Meld(%s)' % '   '.join('%s' % combo for combo in (self.sets + self.runs))


class Deck:
  class Error(Exception): pass
  class InvalidTake(Error): pass
  class EmptyDeck(Error): pass

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
      raise TypeError('Expected cards to be a list of Card, got %s' % type(cards))

  def __len__(self):
    return len(self.cards)

  def shuffle(self):
    self._RANDOM.shuffle(self.cards)

  def pop(self):
    try:
      return self.cards.pop()
    except IndexError:
      raise self.EmptyDeck('Deck is empty.')

  def put(self, card):
    self.cards.insert(0, card)

  def take(self, card):
    try:
      self.cards.remove(card)
    except ValueError:
      raise self.InvalidTake('Card not in deck.')

  def __enter__(self):
    assert self.__saved_cards is None, 'Already in a transaction.'
    self.__saved_cards = self.cards[:]
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    assert self.__saved_cards is not None, 'Not in a transaction.'
    if exc_type is None:
      self.__saved_cards = None
    else:
      self.cards = self.__saved_cards
      self.__saved_cards = None