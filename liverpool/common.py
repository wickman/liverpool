from __future__ import print_function, unicode_literals

import random
import sys


if sys.version_info[0] == 2:
  def fake_unicode(s):
    return s.__unicode__().encode('utf-8')
else:
  def fake_unicode(s):
    return s.__unicode__()


class Color(object):
  class Error(Exception): pass
  class InvalidColor(Error): pass

  CLUB = 0
  SPADE = 1
  HEART = 2
  DIAMOND = 3
  MAX = 3

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
  def validate(cls, color):
    if color not in cls.COLORS:
      raise cls.InvalidColor('Unknown color: %s' % color)
    return color

  @classmethod
  def to_str(cls, color):
    return cls.UNICODE_COLORS[cls.validate(color)]

  @classmethod
  def to_repr(cls, color):
    return '%s.%s' % (cls.__name__, cls.COLORS[cls.validate(color)])

  @classmethod
  def iter(cls):
    return iter((cls.CLUB, cls.SPADE, cls.HEART, cls.DIAMOND))


class Rank(object):
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
  def validate(cls, rank):
    if rank < 2 or rank > 14:
      raise cls.InvalidRank('Rank must be be between [2, 14], got %s' % rank)
    return rank

  @classmethod
  def to_str(cls, rank):
    return cls.FACES.get(cls.validate(rank), str(rank))

  @classmethod
  def to_repr(cls, rank):
    if rank in cls.FACES_REPR:
      return '%s.%s' % (cls.__name__, cls.FACES_REPR[rank])
    else:
      return cls.to_str(rank)

  @classmethod
  def iter(cls):
    return range(cls.MIN, cls.MAX + 1)


class Card(object):
  # __slots__ = ('color', 'rank')
  __slots__ = ('value',)

  MAX = Rank.MAX + Color.MAX * (Rank.MAX + 1)

  @classmethod
  def of(cls, rank, color):
    return cls(Rank.validate(rank) + Color.validate(color) * (Rank.MAX + 1))

  def __init__(self, value):
    self.value = value

  @property
  def color(self):
    return None if self.value == 0 else self.value // (Rank.MAX + 1)
  
  @property
  def rank(self):
    return None if self.value == 0 else self.value % (Rank.MAX + 1)

  def iter_rank(self):
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

  def __unicode__(self):
    if self.value == 0:
      return '??'
    return '%s%s' % (Rank.to_str(self.rank), Color.to_str(self.color))

  def __str__(self):
    return fake_unicode(self)

  def __repr__(self):
    if self.value == 0:
      return '%s.JOKER' % self.__class__.__name__
    return '%s(%s, %s)' % (
        self.__class__.__name__, Color.to_repr(self.color), Rank.to_repr(self.rank))


Card.JOKER = Card(0)


class Add(list):
  def __unicode__(self):
    return ' '.join('%s' % card for card in self)

  def __str__(self):
    return fake_unicode(self)


class Extend(object):
  __slots__ = ('run', 'left', 'right')

  def __init__(self, run, left=None, right=None):
    self.run = run
    self.left = left if left is not None else []
    self.right = right if right is not None else []

  def __iter__(self):
    return iter(self.left + self.right)

  def __unicode__(self):
    run_str = '(%s)' % self.run
    if self.left:
      run_str = ' '.join('%s' % card for card in self.left) + '++' + run_str
    if self.right:
      run_str += '++' + ' '.join('%s' % card for card in self.right)
    return run_str

  def __str__(self):
    return fake_unicode(self)


class Run(object):
  class Error(Exception): pass
  class InvalidExtend(Exception): pass

  __slots__ = ('start', 'jokers')

  MIN = 4

  @classmethod
  def from_cards(cls, cards):
    if len(cards) < cls.MIN:
      raise ValueError('Run is not of minimum length %d' % cls.MIN)
    if not all(isinstance(card, Card) for card in cards):
      raise TypeError('All cards must be of type Card.')
    start_card = cards[0]
    jokers = []
    for rank_offset, card in enumerate(cards):
      if card.color != start_card.color:
        raise ValueError('Subsequent cards do not have the correct color.')
      if card.rank is not None and start_card.rank + rank_offset != card.rank:
        raise ValueError('Not a valid run: %s is out of order.' % card)
      jokers.append(card.rank is None)
    return cls(start_card, jokers)

  def __init__(self, start, jokers):
    if not isinstance(start, Card):
      raise TypeError('Expected start to be a Card, got %s' % type(start))
    if not isinstance(jokers, (tuple, list)):
      raise TypeError('Expected jokers to be a tuple/list of booleans.')
    self.start = start
    self.jokers = tuple(bool(elt) for elt in jokers)

  def __hash__(self):
    return hash((self.start, self.jokers))

  def __eq__(self, other):
    if not isinstance(other, Run):
      return False
    return self.start == other.start and self.jokers == other.jokers

  def __iter__(self):
    for offset, joker in enumerate(self.jokers):
      yield Card.JOKER if joker else Card.of(self.start.rank + offset, self.start.color)

  def iter_left(self):
    for rank in range(self.start.rank, Rank.MIN - 1, -1):
      yield Card.of(rank, self.start.color)

  def iter_right(self):
    for rank in range(self.start.rank + len(self.jokers), Rank.MAX + 1):
      yield Card.of(rank, self.start.color)

  def extend_from(self, other):
    if not isinstance(other, Run):
      return False
    if self.start.color != other.start.color:
      return False

    my_cards = list(self)
    other_cards = list(other)

    left = []
    while other_cards and other_cards[0] < my_cards[0]:
      left.append(other_cards.pop(0))

    other_cards_overlap, right = other_cards[0:len(my_cards)], other_cards[len(my_cards):]

    if other_cards_overlap != my_cards:
      raise self.InvalidExtend()

    if not left and not right:
      raise self.InvalidExtend('Empty extension.')

    return Extend(self, left, right)

  def __unicode__(self):
    return ' '.join('%s' % card for card in self)

  def __str__(self):
    return fake_unicode(self)

  def __repr__(self):
    return '%s.from_cards(%s)' % (self.__class__.__name__, ', '.join(map(repr, self)))


class Set(object):
  __slots__ = ('rank', 'jokers', 'colors')

  MIN = 3

  @classmethod
  def partition_colors(cls, colors):
    """return a tuple of # jokers, remaining colors."""
    return (sum(color is None for color in colors),
            tuple(sorted([color for color in colors if color is not None])))

  def __init__(self, rank, colors):
    if not isinstance(colors, (tuple, list)):
      raise TypeError('Expected colors to be a tuple/list of colors or Nones.')
    if len(colors) < self.MIN:
      raise ValueError('Set not large enough!')
    self.jokers, self.colors = self.partition_colors(
        [color if color is None else Color.validate(color) for color in colors])
    self.rank = Rank.validate(rank)

  def _as_tuple(self):
    return (self.jokers + len(self.colors), self.rank, self.jokers, self.colors)

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

  def __unicode__(self):
    def render_joker(card):
      if card == Card.JOKER:
        return '%s?' % Rank.to_str(self.rank)
      return card
    return ' '.join('%s' % render_joker(card) for card in self)

  def __str__(self):
    return fake_unicode(self)

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


class Meld(object):
  def __init__(self, sets=None, runs=None):
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

  def __unicode__(self):
    return 'Meld(%s)' % '   '.join('%s' % combo for combo in (self.sets + self.runs))

  def __str__(self):
    return fake_unicode(self)


class MeldUpdate(list):
  pass


class Deck(object):
  def __init__(self, count=1):
    self.cards = []
    for _ in range(count):
      for rank in Rank.iter():
        for color in Color.iter():
          self.cards.append(Card.of(rank, color))
      for _ in range(2):
        self.cards.append(Card.JOKER)
    self.shuffle()

  def shuffle(self):
    random.shuffle(self.cards)

  def take(self):
    return self.cards.pop()

  def put(self, card):
    self.cards.insert(0, card)
