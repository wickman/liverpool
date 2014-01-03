from collections import defaultdict
import itertools

from .combinatorics import (
    combinations_with_replacement,
    unique_combinations,
)

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
    if not all(isinstance(run, Run) for run_ in self.runs):
      raise TypeError('runs must be instances of Run.')


class Hand(object):
  class Error(Exception): pass
  class InvalidCard(Error): pass
  class InvalidTake(Error): pass

  __slots__ = ('cards', 'stack', 'setdex', 'rundex', 'jokers')

  def __init__(self, cards=None):
    self.rundex = dict((color, [0] * (Rank.RANK_MAX + 1)) for color in Color.iter())
    self.setdex = [[] for k in range(Rank.RANK_MAX + 1)]
    self.cards = defaultdict(int)
    self.jokers = 0
    self.stack = [None]   # stack of takes, None represents start of a "transaction"
    for card in self.cards:
      self.put_card(card)
    self.commit()

  def commit(self):
    self.stack.append(None)

  def rollback(self):
    while self.stack[-1] is not None:
      self.put_card(self.stack.pop())

  def undo(self):
    assert len(self.stack) > 1
    assert self.stack.pop() is None
    self.rollback()

  def truncate(self):
    self.stack = [None]

  def take_card(self, card):
    if not isinstance(card, Card):
      raise TypeError('Expected card to be Card, got %s' % type(card))

    if card == Card.JOKER or self.cards[card] <= 0:
      if self.jokers == 0:
        raise cls.InvalidTake('Hand does not contain jokers!')
      self.jokers -= 1
      self.stack.append(Card.JOKER)
      return Card.JOKER

    self.cards[card] -= 1
    self.rundex[card.color][card.rank] -= 1
    self.setdex[card.rank].remove(card.color)
    self.stack.append(card)
    return card

  def put_card(self, card):
    if not isinstance(card, Card):
      raise TypeError('Expected card to be Card, got %s' % type(card))

    if card == Card.JOKER:  # jokers are wild!
      self.jokers += 1
      return

    self.cards[card] += 1
    self.rundex[card.color][card.rank] += 1
    self.setdex[card.rank].append(card.color)

  def _map_run(self, run, method):
    if not isinstance(run, Run):
      raise TypeError('Expected run to be Run, got %s' % type(run))
    for card, joker in itertools.izip(run.start.iter_rank(), run.jokers):
      method(Card.JOKER if joker else card)

  def map_set(self, set_, method):
    if not isinstance(set_, Set):
      raise TypeError('Expected set to be Set, got %s' % type(set_))
    for color in set_.colors:
      method(Card.JOKER if color is None else Card(set_.rank, color))

  def put_run(self, run):
    self._map_run(run, self.put_card)

  def put_set(self, set_):
    self._map_set(set_, self.put_card)

  def take_run(self, run):
    self._map_run(run, self.take_card)

  def take_set(self, set_):
    self._map_set(set_, self.take_card)

  def iter_sets(self):
    for rank, colors in enumerate(self.setdex):
      if rank < 2:
        continue
      jokered_colors = colors + [None] * self.jokers
      jokered_colors.sort()
      for set_size in range(3, len(jokered_colors) + 1):
        for combination in unique_combinations(jokered_colors, set_size):
          yield Set(rank, combination)

  def iter_runs(self):
    # iterate over all valid runs.  you may not be able to take_run all of them
    # necessarily, but in isolation they are valid.
    pass

  def _iter_lays(self, strategy):
    set_combinator = combinations_with_replacement(self.iter_sets(), strategy.num_sets)
    run_combinator = combinations_with_replacement(self.iter_runs(), strategy.num_runs)
    if strategy.num_sets == 0:
      for sets in set_combinator:
        yield Lay(sets, None)
    elif strategy.num_runs == 0:
      for runs in run_combinator:
        yield Lay(None, runs)
    else:
      for sets, runs in itertools.product(set_combinator, run_combinator):
        yield Lay(sets, runs)

  def _valid_lay(self, lay):
    try:
      for set_ in lay.sets:
        self.take_set(set_)
      for run in lay.runs:
        self.take_run(run)
    except self.InvalidTake:
      self.rollback()
      return False

    self.undo()
    return True

  def iter_lays(self, strategy):
    for lay in self._iter_lays(strategy):
      if self._valid_lay(lay):
        yield lay
