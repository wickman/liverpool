from __future__ import print_function, unicode_literals


class Color(object):
  class Error(Exception): pass
  class InvalidColor(Error): pass

  COLORS = {
    1: 'CLUB',
    2: 'SPADE',
    3: 'HEART',
    4: 'DIAMOND',
  }

  UNICODE_COLORS = {
    1: u'\u2663',
    2: u'\u2660',
    3: u'\u2665',
    4: u'\u2666',
  }

  CLUB = 1
  SPADE = 2
  HEART = 3
  DIAMOND = 4

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

  RANK_MIN = 2
  JACK = 11
  QUEEN = 12
  KING = 13
  ACE = RANK_MAX = 14

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
    return range(cls.RANK_MIN, cls.RANK_MAX + 1)


class Card(object):
  __slots__ = ('color', 'rank')

  def __init__(self, color, rank):
    self.color = color if color is None else Color.validate(color)
    self.rank = rank if rank is None else Rank.validate(rank)

  def iter_rank(self):
    # only support rank iteration for non-jokers
    assert self.color is not None
    assert self.rank is not None
    for rank in range(self.rank, Rank.RANK_MAX + 1):
      yield Card(self.color, rank)

  def __hash__(self):
    return hash((self.color, self.rank))

  def __eq__(self, other):
    if not isinstance(other, Card):
      return False
    return self.color == other.color and self.rank == other.rank

  def __str__(self):
    if self.color is None and self.rank is None:
      return '??'
    return '%s%s' % (Rank.to_str(self.rank), Color.to_str(self.color))

  def __repr__(self):
    if self.color is None and self.rank is None:
      return '%s.JOKER' % self.__class__.__name__
    return '%s(%s, %s)' % (
        self.__class__.__name__, Color.to_repr(self.color), Rank.to_repr(self.rank))


Card.JOKER = Card(None, None)


class Run(object):
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
      yield Card.JOKER if joker else Card(self.start.color, self.start.rank + offset)

  def __str__(self):
    return ' '.join(map(str, self))

  def __repr__(self):
    return '%s.from_cards(%s)' % (self.__class__.__name__, ', '.join(map(repr, self)))


class Set(object):
  __slots__ = ('rank', 'colors')

  MIN = 3

  def __init__(self, rank, colors):
    if not isinstance(colors, (tuple, list)):
      raise TypeError('Expected colors to be a tuple/list of colors or Nones.')
    self.colors = tuple(color if color is None else Color.validate(color) for color in colors)
    self.rank = Rank.validate(rank)

  def __hash__(self):
    return hash((self.rank, self.colors))

  def __eq__(self, other):
    if not isinstance(other, Set):
      return False
    return self.colors == other.colors and self.rank == other.rank

  def __iter__(self):
    for color in self.colors:
      yield Card.JOKER if color is None else Card(color, self.rank)

  def __str__(self):
    return ' '.join(map(str, self))

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


class Lay(object):
  def __init__(self, sets=None, runs=None):
    self.sets = tuple(sets) or []
    self.runs = tuple(runs) or []
    if not all(isinstance(set_, Set) for set_ in self.sets):
      raise TypeError('sets must be instances of Set.')
    if not all(isinstance(run, Run) for run in self.runs):
      raise TypeError('runs must be instances of Run.')

  def __str__(self):
    return 'Lay(%s)' % '    '.join(map(str, self.sets + self.runs))
