from __future__ import print_function, unicode_literals

from collections import defaultdict
import itertools
import pickle

from .combinatorics import (
    combinations_with_replacement,
    unique_combinations,
    sort_uniq,
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
    num_jokers = len([card for card in cards if card.rank is None])
    cards = sorted(card for card in cards if card.rank is not None)
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
    if not all(isinstance(run, Run) for run in self.runs):
      raise TypeError('runs must be instances of Run.')

  def __str__(self):
    return 'Lay(%s)' % '    '.join(map(str, self.sets + self.runs))


class Hand(object):
  class Error(Exception): pass
  class InvalidCard(Error): pass
  class InvalidTake(Error): pass

  __slots__ = ('cards', 'stack', 'setdex', 'rundex', 'jokers')

  RUN_LUT = {}

  @classmethod
  def precompute_runs(cls):
    def vector_to_cards(vector):
      for k in range(13):
        if vector & (1 << k):
          yield k

    def meld(card_vector, joker_vector):
      start = min(card_vector)
      if joker_vector:
        start = min(start, min(joker_vector))
      end = max(card_vector)
      if joker_vector:
        end = max(end, max(joker_vector))
      jokers = []
      for rank in range(start, end + 1):
        if rank in card_vector and rank in joker_vector:
          raise ValueError
        if rank not in card_vector and rank not in joker_vector:
          raise ValueError
        jokers.append(rank not in card_vector)
      return start, jokers

    for total_jokers in range(3):
      cls.RUN_LUT[total_jokers] = defaultdict(list)
      for card_vector in range(2**13):
        running_lut = []
        ranks = list(vector_to_cards(card_vector))
        #print('%2d jok %s : %s' % (
        #      num_jokers, bin(card_vector), ':'.join(Rank.to_str(rank + 2) for rank in ranks)))
        for num_jokers in range(total_jokers + 1):
          for rank_selection in range(Run.MIN - num_jokers, len(ranks) + 1):
            for selected_cards in unique_combinations(ranks, rank_selection):
              for joker_vector in unique_combinations(range(13), num_jokers):
                try:
                  start, jokers = meld(selected_cards, joker_vector)
                except ValueError:
                  continue
                if len(jokers) < Run.MIN:
                  continue
                running_lut.append((start, tuple(jokers)))
        cls.RUN_LUT[total_jokers][card_vector] = list(sort_uniq(running_lut))
        #for start, jokers in sort_uniq(running_lut): # cls.RUN_LUT[num_jokers][card_vector]:
        #  print('  valid: %s' % Run(Card(Color.DIAMOND, start + 2), jokers))

  @classmethod
  def save_lut(cls):
    with open('run.lut', 'wb') as fp:
      pickle.dump(cls.RUN_LUT, fp)

  @classmethod
  def load_lut(cls):
    with open('run.lut', 'rb') as fp:
      cls.RUN_LUT = pickle.load(fp)

  def __init__(self, cards=None):
    self.rundex = dict((color, [0] * (Rank.RANK_MAX + 1)) for color in Color.iter())
    self.setdex = [[] for k in range(Rank.RANK_MAX + 1)]
    self.cards = defaultdict(int)
    self.jokers = 0
    self.stack = [None]   # stack of takes, None represents start of a "transaction"
    for card in self.cards:
      self.put_card(card)
    self.commit()
    self.load_lut()

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
        raise self.InvalidTake('Hand does not contain jokers!')
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
    for card, joker in zip(run.start.iter_rank(), run.jokers):
      method(Card.JOKER if joker else card)

  def _map_set(self, set_, method):
    if not isinstance(set_, Set):
      raise TypeError('Expected set to be Set, got %s' % type(set_))
    for color in set_.colors:
      method(Card.JOKER if color is None else Card(color, set_.rank))

  def put_run(self, run):
    self._map_run(run, self.put_card)

  def put_set(self, set_):
    self._map_set(set_, self.put_card)

  def take_run(self, run):
    #print('Taking run: %s' % run)
    self._map_run(run, self.take_card)

  def take_set(self, set_):
    #print('Taking set: %s' % set_)
    self._map_set(set_, self.take_card)

  def iter_sets(self):
    for rank, colors in enumerate(self.setdex):
      if rank < 2:
        continue
      jokered_colors = [None] * self.jokers + sorted(colors)
      for set_size in range(Set.MIN, len(jokered_colors) + 1):
        for combination in unique_combinations(jokered_colors, set_size):
          yield Set(rank, combination)

  @classmethod
  def rundex_to_vector(cls, rundex):
    value = 0
    for k, count in enumerate(rundex):
      if count:
        value |= (1 << (k - 2))
    return value

  def iter_runs(self):
    for color, rundex in self.rundex.items():
      vector = self.rundex_to_vector(rundex)
      for start, jokers in self.RUN_LUT[self.jokers][vector]:
        yield Run(Card(color, start + 2), jokers)

  def _iter_lays(self, strategy):
    set_combinator = combinations_with_replacement(self.iter_sets(), strategy.num_sets)
    run_combinator = combinations_with_replacement(self.iter_runs(), strategy.num_runs)
    if strategy.num_runs == 0:
      for sets in set_combinator:
        yield Lay(sets, None)
    elif strategy.num_sets == 0:
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

    self.rollback()
    return True

  def iter_lays(self, strategy):
    for lay in self._iter_lays(strategy):
      if self._valid_lay(lay):
        yield lay


"""
from liverpool.common import *

h = Hand()
h.put_card(Card(Color.SPADE, 7))
h.put_card(Card(Color.DIAMOND, 7))
h.put_card(Card(Color.HEART, 7))
h.put_card(Card(Color.HEART, 2))
h.put_card(Card(Color.HEART, 3))
h.put_card(Card(Color.CLUB, 3))
h.put_card(Card.JOKER)
h.put_card(Card(Color.HEART, 4))
h.put_card(Card(Color.HEART, 5))

for set_ in h.iter_sets():
  print(set_)

for run in h.iter_runs():
  print(run)

objective = Objective(1, 1)

for lay in h.iter_lays(objective):
  print(lay)
"""
