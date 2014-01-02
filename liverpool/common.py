from collections import defaultdict
import itertools


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

  @classmethod
  def iter(cls):
    return iter((cls.CLUB, cls.SPADE, cls.HEART, cls.DIAMOND))


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
      raise cls.InvalidRank('Rank must be be between [2, 14]')
    return rank

  @classmethod
  def to_str(cls, rank):
    return FACES.get(cls.validate(rank), str(rank))

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

  def hash(self):
    return hash((self.color, self.rank))

  def __eq__(self, other):
    if not isinstance(other, Card):
      return False
    return self.color == other.color and self.rank == other.rank


Card.JOKER = Card(None, None)


class Run(object):
  __slots__ = ('start', 'jokers')

  def __init__(self, start, jokers):
    if not isinstance(start, Card):
      raise TypeError('Expected start to be a Card, got %s' % type(start))
    if not isinstance(jokers, (tuple, list)):
      raise TypeError('Expected jokers to be a tuple/list of booleans.')
    self.start = start
    self.jokers = tuple(bool(elt) for elt in jokers)

  def hash(self):
    return hash((self.start, self.jokers))

  def __eq__(self, other):
    if not isinstance(other, Run):
      return False
    return self.start == other.start and self.jokers == other.jokers


class Set(object):
  __slots__ = ('rank', 'colors')

  def __init__(self, rank, colors):
    if not isinstance(colors, (tuple, list)):
      raise TypeError('Expected colors to be a tuple/list of colors or Nones.')
    self.colors = tuple(color if color is None else Color.validate(color) for color in colors)
    self.rank = Rank.validate(rank)

  def hash(self):
    return hash((self.rank, self.colors))

  def __eq__(self, other):
    if not isinstance(other, Set):
      return False
    return self.colors == other.colors and self.rank == other.rank


#
# [heart, heart, spade, None]
#
# choose 2
#   heart heart
#   heart spade
#   heart None
#   spade None
#
# 4c2 =>
#  4! /
#  2!(4-2)!
#  => 4*3*2*1/2/2 => 6
# huh?
#
# [heart, heart, spade, None]
#   => {heart:2, spade:1, None:1}
#
# def take_color(color_iter, color_max):
#   next_color = next(color_iter)
#   for color_rank in range(0, min(color_max, colordex[next_color])):
#     yield (color_rank, take_color(color_iter, color_max - color_rank))
#
#
#


class Hand(object):
  class Error(Exception): pass
  class InvalidCard(Error): pass
  class InvalidTake(Error): pass

  __slots__ = ('cards', 'setdex', 'rundex')

  def __init__(self, cards=None):
    self.rundex = dict((color, [0] * (Rank.RANK_MAX + 1)) for color in Color.iter())
    self.setdex = [[] for k in range(Rank.RANK_MAX + 1)]
    self.cards = defaultdict(int)
    for card in self.cards:
      self.put_card(card)

  def take_card(self, card):
    if not isinstance(card, Card):
      raise TypeError('Expected card to be Card, got %s' % type(card))
    if self.cards[card] < 0:
      if self.cards[Card.JOKER] == 0:
        raise cls.InvalidTake('Hand does not contain a %s or Joker' % card)
      self.cards[Card.JOKER] -= 1
      return Card.JOKER
    self.cards[card] -= 1
    self.rundex[card.color][card.rank] -= 1
    self.setdex[card.rank] -= 1
    return card

  def put_card(self, card):
    if not isinstance(card, Card):
      raise TypeError('Expected card to be Card, got %s' % type(card))
    self.cards[card] += 1

    if card == Card.JOKER:  # jokers are wild!
      return

    self.rundex[card.color][card.rank] += 1
    self.setdex[card.rank] += 1

  def put_run(self, run):
    if not isinstance(run, Run):
      raise TypeError('Expected run to be Run, got %s' % type(run))
    for card, joker in itertools.izip(run.start.iter_rank(), run.jokers):
      self.put_card(Card.JOKER if joker else card)

  def put_set(self, set_):
    if not isinstance(set_, Set):
      raise TypeError('Expected set to be Set, got %s' % type(set_))
    for color in set_.colors:
      self.put_card(Card.JOKER if color is None else Card(set_.rank, color))

  def take_run(self, run):
    pass

  def take_set(self, set_):
    pass

  def iter_sets(self):
    #for rank, dim_max in enumerate(self.setdex):
    #  for dim in range(3, dim_max + 1):
    #    yield Set(rank, dim)
    pass
