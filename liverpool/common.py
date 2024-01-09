from contextlib import contextmanager
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


class Card:
  """A card in the game of Liverpool."""

  __slots__ = ('value',)

  JOKER: "Card" = None  # mypy: allow-untyped-defs
  JOKER_VALUE = 0
  MIN = Rank.MIN + Color.MIN * Rank.MIN - 1
  MAX = Rank.MAX + Color.MAX * (Rank.MAX + 1)

  @classmethod
  def of(cls, rank, color) -> "Card":
    return cls(Rank.validate(rank) + Color.validate(color) * (Rank.MAX + 1))

  def __init__(self, value: int):
    self.value = value
    if not isinstance(value, int):
      raise TypeError('Card value must be an integer, got %s' % type(value))
    if self.value != self.JOKER_VALUE and (self.value < self.MIN and self.value > self.MAX):
      raise ValueError('Invalid card value: %s' % value)

  @property
  def color(self):
    return None if self.value == 0 else self.value // (Rank.MAX + 1)

  @property
  def rank(self):
    return None if self.value == 0 else self.value % (Rank.MAX + 1)

  def iter_rank(self) -> Iterable["Card"]:
    # only support rank iteration for non-jokers
    assert self.color is not None
    assert self.rank is not None
    for rank in range(self.rank, Rank.MAX + 1):
      yield Card.of(rank, self.color)

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
    if self.value == 0:
      return '??'
    return '%s%s' % (Rank.to_str(self.rank), Color.to_str(self.color))

  def __repr__(self):
    if self.value == 0:
      return '%s.JOKER' % self.__class__.__name__
    return '%s(%s, %s)' % (
        self.__class__.__name__, Color.to_repr(self.color), Rank.to_repr(self.rank))


Card.JOKER = Card(Card.JOKER_VALUE)


class Add(list):
  """A list of cards that can be added to a hand."""
  def __str__(self):
    return ' '.join('%s' % card for card in self)


class Extend:
  """A union of two runs that yields the overlapping run and extensions to the left and right."""
  __slots__ = ('run', 'left', 'right')

  def __init__(self, run: "Run", left: Optional[List[Card]] = None, right: Optional[List[Card]] = None) -> None:
    self.run: Run = run
    self.left: List[Card] = left if left is not None else []
    self.right: List[Card] = right if right is not None else []

  def __iter__(self):
    return iter(self.left + self.right)

  def __str__(self):
    run_str = '(%s)' % self.run
    if self.left:
      run_str = ' '.join('%s' % card for card in self.left) + '++' + run_str
    if self.right:
      run_str += '++' + ' '.join('%s' % card for card in self.right)
    return run_str


class Run:
  """A run of cards of the same color.

  The run is represented by the first card and a list of booleans indicating Joker positions.
  """

  class Error(Exception): pass
  class InvalidExtend(Exception): pass

  __slots__ = ('start', 'jokers')

  MIN = 4

  # TODO: Reimplement this correctly if we need it
  #@classmethod
  #def from_cards(cls, cards) -> "Run":
  #  if len(cards) < cls.MIN:
  #    raise ValueError('Run is not of minimum length %d' % cls.MIN)
  #  if not all(isinstance(card, Card) for card in cards):
  #    raise TypeError('All cards must be of type Card.')
  #  start_card = cards[0]
  #  jokers = []
  #  for rank_offset, card in enumerate(cards):
  #    if card.color != start_card.color:
  #      raise ValueError('Subsequent cards do not have the correct color.')
  #    if card.rank is not None and start_card.rank + rank_offset != card.rank:
  #      raise ValueError('Not a valid run: %s is out of order.' % card)
  #    jokers.append(card.rank is None)
  #  return cls(start_card, jokers)

  @classmethod
  def of(cls, color: int, start: int, length: int, joker_indices: Optional[List[int]] = None) -> "Run":
    if not isinstance(color, int):
      raise TypeError('Expected color to be an integer, got %s' % type(color))
    if not isinstance(start, int) or start < Rank.MIN or start > Rank.MAX:
      raise TypeError('Expected start to be an integer between %d and %d, got %s' % (
          Rank.MIN, Rank.MAX, start))
    if not isinstance(length, int) or length < cls.MIN:
      raise TypeError('Expected length to be an integer >= %d, got %s' % (cls.MIN, length))
    if joker_indices is not None and not isinstance(joker_indices, (tuple, list)):
      raise TypeError('Expected joker_indices to be a tuple/list of integers.')
    if joker_indices is not None and any(index > length for index in joker_indices):
      raise ValueError('Got joker index out of bounds.')
    jokers = [False] * length
    if joker_indices is not None:
      for joker_index in joker_indices:
        jokers[joker_index] = True
    return cls(Card.of(start, color), jokers)

  def __init__(self, start, jokers):
    if not isinstance(start, Card):
      raise TypeError('Expected start to be a Card, got %s' % type(start))
    if not isinstance(jokers, (tuple, list)):
      raise TypeError('Expected jokers to be a tuple/list of booleans.')
    self.start = start
    self.jokers = tuple(bool(elt) for elt in jokers)

  @property
  def length(self):
    return len(self.jokers)

  def __len__(self):
    return self.length

  def __hash__(self):
    return hash((self.start, self.jokers))

  def __eq__(self, other):
    if not isinstance(other, Run):
      return False
    return self.start == other.start and self.jokers == other.jokers

  def __iter__(self) -> Iterable[Card]:
    """Iterate over the cards in the run."""
    for offset, joker in enumerate(self.jokers):
      yield Card.JOKER if joker else Card.of(self.start.rank + offset, self.start.color)

  def iter_left(self) -> Iterable[Card]:
    """Iterate, descending, over the cards to the left of the run."""
    for rank in range(self.start.rank - 1, Rank.MIN - 1, -1):
      yield Card.of(rank, self.start.color)

  def iter_right(self) -> Iterable[Card]:
    """Iterate, ascending, over the cards to the right of the run."""
    for rank in range(self.start.rank + len(self.jokers), Rank.MAX + 1):
      yield Card.of(rank, self.start.color)

  def extend_from(self, other: "Run") -> Extend:
    if not isinstance(other, Run):
      raise TypeError('Expected other to be a Run, got %s' % type(other))
    if self.start.color != other.start.color:
      raise self.InvalidExtend('Runs must have the same color.')

    my_cards: List[Card] = list(self)
    other_cards: List[Card] = list(other)

    left = []
    while other_cards and other_cards[0] < my_cards[0]:
      left.append(other_cards.pop(0))

    other_cards_overlap, right = other_cards[0:len(my_cards)], other_cards[len(my_cards):]

    if other_cards_overlap != my_cards:
      raise self.InvalidExtend()

    if not left and not right:
      raise self.InvalidExtend('Empty extension.')

    return Extend(self, left, right)

  def __str__(self):
    return ' '.join('%s' % card for card in self)

  def __repr__(self):
    return '%s.from_cards(%s)' % (self.__class__.__name__, ', '.join(map(repr, self)))


class Set(object):
  __slots__ = ('rank', 'jokers', 'colors')

  MIN = 3

  @classmethod
  def partition_colors(cls, colors) -> Tuple[int, Tuple[int, ...]]:
    """return a tuple of # jokers, remaining colors."""
    return (sum(color is None for color in colors),
            tuple(sorted([color for color in colors if color is not None])))

  def __init__(self, rank: int, colors: Iterable[Optional[int]]) -> None:
    if not isinstance(colors, (tuple, list)):
      raise TypeError('Expected colors to be a tuple/list of colors or Nones.')
    if len(colors) < self.MIN:
      raise ValueError('Set not large enough!')
    self.jokers, self.colors = self.partition_colors(
        [color if color is None else Color.validate(color) for color in colors])
    self.rank = Rank.validate(rank)

  @property
  def length(self):
    return self.jokers + len(self.colors)

  def __len__(self):
    return self.length

  def _as_tuple(self):
    return (self.length, self.rank, self.jokers, self.colors)

  def __hash__(self):
    return hash(self._as_tuple())

  def __lt__(self, other):
    if not isinstance(other, Set):
      raise TypeError
    return self._as_tuple() < other._as_tuple()

  def __eq__(self, other):
    if not isinstance(other, Set):
      return False
    return self.rank == other.rank and (
        self.jokers == other.jokers and
        self.colors == other.colors)

  def __iter__(self):
    for _ in range(self.jokers):
      yield Card.JOKER
    for color in self.colors:
      yield Card.of(self.rank, color)

  def __str__(self):
    def render_joker(card):
      if card == Card.JOKER:
        return '%s?' % Rank.to_str(self.rank)
      return card
    return ' '.join('%s' % render_joker(card) for card in self)

  def __repr__(self):
    return '%s.from_cards(%s)' % (self.__class__.__name__, ', '.join(map(repr, self)))


class Objective(object):
  def __init__(self, num_sets, num_runs):
    if not isinstance(num_sets, int) or num_sets < 0:
      raise TypeError('Number of sets must be a non-negative integer.')
    if not isinstance(num_runs, int) or num_runs < 0:
      raise TypeError('Number of runs must be a non-negative integer.')
    self.num_sets = num_sets
    self.num_runs = num_runs


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

  def __eq__(self, other):
    if not isinstance(other, Meld):
      return False
    return self._as_tuple() == other._as_tuple()

  def __len__(self):
    return sum(len(list(s)) for s in self.sets) + sum(len(list(r)) for r in self.runs)

  def __str__(self):
    return 'Meld(%s)' % '   '.join('%s' % combo for combo in (self.sets + self.runs))


class MeldUpdate(list):
  pass


class DeckTransaction:
  def __init__(self, cards: List[Card]) -> None:
    self.cards = cards
    self.saved = False

  def save(self):
    self.saved = True

  def rollback(self):
    self.saved = False



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
        cards.append(Card.JOKER)
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