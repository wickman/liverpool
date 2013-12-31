class Color(object):
  class Error(Exception): pass
  class InvalidColor(Error): pass

  COLORS = {
    1: 'CLUB',
    2: 'SPADE',
    3: 'HEART',
    4: 'DIAMOND',
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
    return cls.COLORS[cls.validate(color)]


class Rank(object):
  class Error(Exception): pass
  class InvalidRank(Error): pass

  FACES = {
    '11': 'JACK',
    '12': 'QUEEN',
    '13': 'KING',
    '14': 'ACE',
  }
  
  RANK_MIN = 2
  JACK = 11
  QUEEN = 12
  KING = 13
  ACE = RANK_MAX = 14

  @classmethod
  def validate(cls, rank):
    if rank < 2 or rank > 14:
      raise cls.InvalidColor('Rank must be be between [2, 14]')
    return rank

  @classmethod
  def to_str(cls, rank):
    return FACES.get(cls.validate(rank), str(rank))


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

  def hash(self):
    return hash((self.color, self.rank))


class Run(object):
  __slots__ = ('start', 'jokers')
  
  def __init__(self, start, jokers):
    if not isinstance(start, Card):
      raise TypeError('Expected start to be a Card, got %s' % type(start))
    if not isinstance(jokers, (tuple, list)):
      raise TypeError('Expected jokers to be a tuple/list of booleans.')
    self.start = start
    self.jokers = tuple(bool(elt) for elt in jokers)


class Set(object):
  __slots__ = ('rank', 'colors')

  def __init__(self, rank, colors):
    if not isinstance(colors, (tuple, list)):
      raise TypeError('Expected colors to be a tuple/list of colors or Nones.')
    self.colors = tuple(color if color is None else Color.validate(color) for color in colors)
    self.rank = Rank.validate(rank)


class Hand(object):
  pass
