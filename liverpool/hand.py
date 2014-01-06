from __future__ import print_function, unicode_literals

from collections import defaultdict
import contextlib
import gzip
import itertools
import json
import os

from .combinatorics import (
    combinations_with_replacement,
    sort_uniq,
    uniq,
    unique_combinations,
)
from .common import (
    Card,
    Color,
    Meld,
    Objective,
    Rank,
    Run,
    Set,
    unicode
)


class sorted_list(list):
  def __iter__(self):
    return iter(sorted(super(sorted_list, self).__iter__()))


class Setdex(object):
  # Index set count.
  __slots__ = ('value',)

  NUM_BITS = 2 # support 0, 1, 2 decks.  NUM_BITS=3 is 0-7 decks. etc
  SET_MASK = (1 << NUM_BITS) - 1

  @classmethod
  def iter_all(cls):
    for value in range(2**(cls.NUM_BITS * 4)):
      yield cls(value)

  def __init__(self, value=0):
    self.value = value

  def append(self, color):
    self.value += 1 << (self.NUM_BITS * color)

  def remove(self, color):
    self.value -= 1 << (self.NUM_BITS * color)

  def __iter__(self):
    for color in Color.iter():
      count = (self.value & (self.SET_MASK << (self.NUM_BITS * color))) >> (self.NUM_BITS * color)
      for _ in range(count):
        yield color


class Rundex(object):
  pass


class Hand(object):
  class Error(Exception): pass
  class InvalidCard(Error): pass
  class InvalidTake(Error): pass

  __slots__ = ('cards', 'stack', 'setdices', 'rundex', 'jokers')

  SET_CLASS = sorted_list

  @classmethod
  def meld(cls, card_vector, joker_vector):
    """If a card vector and a joker_vector melds into a run, return the start/jokers."""
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

  @classmethod
  def ranks_from_rundex(cls, rundex, jokers=0):
    """Returns (start,joker) arrays for a particular rundex/#jokers."""
    total_jokers = min(2, jokers)  # cap runs at 2 jokers
    runs = []
    ranks = [rank for rank, count in enumerate(rundex) if count]
    for num_jokers in range(total_jokers + 1):
      for rank_selection in range(Run.MIN - num_jokers, len(ranks) + 1):
        for selected_cards in unique_combinations(ranks, rank_selection):
          # this could be improved with some thought
          for joker_vector in unique_combinations(Rank.iter(), num_jokers):
            try:
              start, jokers = cls.meld(selected_cards, joker_vector)
            except ValueError:
              continue
            if len(jokers) < Run.MIN:
              continue
            runs.append((start, tuple(jokers)))
    return sort_uniq(runs)

  @classmethod
  def orderable_colors_with_none(cls, tup):
    return tuple(-1 if val is None else val for val in tup)

  @classmethod
  def sets_from_colors(cls, colors, jokers=0):
    def iterator():
      jokered_colors = [None] * jokers + list(colors)
      for set_size in range(Set.MIN, len(jokered_colors) + 1):
        for combination in unique_combinations(jokered_colors, set_size):
          print('Combination: %s' % (combination,))
          yield combination
    return sort_uniq(iterator(), key=cls.orderable_colors_with_none)

  def __init__(self, cards=None):
    self.rundex = dict((color, [0] * (Rank.MAX + 1)) for color in Color.iter())
    self.setdices = [self.SET_CLASS() for k in range(Rank.MAX + 1)]
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
        raise self.InvalidTake('Hand does not contain jokers!')
      self.jokers -= 1
      self.stack.append(Card.JOKER)
      return Card.JOKER

    self.cards[card] -= 1
    self.rundex[card.color][card.rank] -= 1
    self.setdices[card.rank].remove(card.color)
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
    self.setdices[card.rank].append(card.color)

  def _map_run(self, run, method):
    if not isinstance(run, Run):
      raise TypeError('Expected run to be Run, got %s' % type(run))
    for card in run:
      method(card)

  def _map_set(self, set_, method):
    if not isinstance(set_, Set):
      raise TypeError('Expected set to be Set, got %s' % type(set_))
    for card in set_:
      method(card)

  def put_run(self, run):
    self._map_run(run, self.put_card)

  def put_set(self, set_):
    self._map_set(set_, self.put_card)

  def take_run(self, run):
    self._map_run(run, self.take_card)

  def take_set(self, set_):
    self._map_set(set_, self.take_card)

  @classmethod
  def _orderable_combination(cls, tup):
    return tuple((tup[0], tuple(-1 if val is None else val for val in tup[1])))

  def iter_sets(self):
    for rank, colors in enumerate(self.setdices):
      if rank < 2:
        continue
      for combination in self.sets_from_colors(colors, self.jokers):
        yield Set(rank, combination)

  def iter_runs(self):
    for color, rundex in self.rundex.copy().items():
      for start, jokers in self.ranks_from_rundex(rundex, self.jokers):
        yield Run(Card(start, color), jokers)

  def _take_committed(self, combos, method, commit=False):
    try:
      for combo in combos:
        method(combo)
      if commit:
        self.commit()
      else:
        self.rollback()
      return True
    except self.InvalidTake:
      self.rollback()
      return False

  def iter_melds(self, strategy):
    if strategy.num_runs == 0:
      for sets in uniq(combinations_with_replacement(self.iter_sets(), strategy.num_sets)):
        if self._take_committed(sets, self.take_set, commit=False):
          yield Meld(sets, None)
    elif strategy.num_sets == 0:
      for runs in uniq(combinations_with_replacement(self.iter_runs(), strategy.num_runs)):
        if self._take_committed(runs, self.take_run, commit=False):
          yield Meld(None, runs)
    else:
      for sets in uniq(combinations_with_replacement(self.iter_sets(), strategy.num_sets)):
        if self._take_committed(sets, self.take_set, commit=True):
          for runs in uniq(combinations_with_replacement(self.iter_runs(), strategy.num_runs)):
            if self._take_committed(runs, self.take_run, commit=False):
              yield Meld(sets, runs)
          self.undo()

  def _valid_meld(self, meld):
    try:
      for set_ in meld.sets:
        self.take_set(set_)
      for run in meld.runs:
        self.take_run(run)
    except self.InvalidTake:
      self.rollback()
      return False

    self.rollback()
    return True

  def __unicode__(self):
    cards = []
    for card, count in sorted(self.cards.items()):
      for _ in range(count):
        cards.append(card)
    for _ in range(self.jokers):
      cards.append(Card.JOKER)
    return 'Hand(%s)' % ' '.join('%s' % card for card in cards)

  def __str__(self):
    return unicode(self)


class FastHand(Hand):
  RUN_LUT = {}
  RUN_LUT_FILE = os.path.expanduser('~/.liverpool_runs')
  RUN_LUT_MAX_JOKERS = 2

  SET_LUT = {}
  SET_LUT_FILE = os.path.expanduser('~/.liverpool_sets')
  SET_LUT_MAX_JOKERS = 3

  SET_CLASS = Setdex
  # SET_CLASS = sorted_list

  @classmethod
  def rundex_to_vector(cls, rundex):
    value = 0
    for k, count in enumerate(rundex):
      if count:
        value |= (1 << (k - Rank.MIN))
    return value

  @classmethod
  def vector_to_rundex(cls, vector):
    for k in range(Rank.MAX + 1):
      if k < Rank.MIN:
        yield 0
      else:
        yield 1 if vector & (1 << (k - Rank.MIN)) else 0

  @classmethod
  def precompute(cls):
    print('Precomputing sets.')
    for total_jokers in range(cls.SET_LUT_MAX_JOKERS + 1):
      cls.SET_LUT[total_jokers] = {}
      for setdex in Setdex.iter_all():
        cls.SET_LUT[total_jokers][setdex.value] = list(
            cls.sets_from_colors(setdex, total_jokers))

    print('Precomputing runs.')
    for total_jokers in range(cls.RUN_LUT_MAX_JOKERS + 1):
      cls.RUN_LUT[total_jokers] = {}
      for card_vector in range(2**(Rank.MAX - Rank.MIN + 1)):
        rundex = list(cls.vector_to_rundex(card_vector))
        cls.RUN_LUT[total_jokers][card_vector] = list(
            cls.ranks_from_rundex(rundex, total_jokers))

  # Consider a more compact representation, e.g. start,len,bitvector
  @classmethod
  def save_luts(cls):
    with contextlib.closing(gzip.GzipFile(cls.RUN_LUT_FILE, 'wb')) as fp:
      fp.write(json.dumps(cls.RUN_LUT))
    with contextlib.closing(gzip.GzipFile(cls.SET_LUT_FILE, 'wb')) as fp:
      fp.write(json.dumps(cls.SET_LUT))

  @classmethod
  def load_luts(cls):
    with contextlib.closing(gzip.GzipFile(cls.RUN_LUT_FILE, 'rb')) as fp:
      # json dictionary keys can only be strings, so we must coerce
      for num_jokers, lut in json.loads(fp.read().decode('utf-8')).items():
        cls.RUN_LUT[int(num_jokers)] = {}
        for card_vector, runs in lut.items():
          cls.RUN_LUT[int(num_jokers)][int(card_vector)] = runs
    with contextlib.closing(gzip.GzipFile(cls.SET_LUT_FILE, 'rb')) as fp:
      # json dictionary keys can only be strings, so we must coerce
      for num_jokers, lut in json.loads(fp.read().decode('utf-8')).items():
        cls.SET_LUT[int(num_jokers)] = {}
        for card_vector, sets in lut.items():
          cls.SET_LUT[int(num_jokers)][int(card_vector)] = sets

  @classmethod
  def maybe_setup_hand(cls):
    if not cls.RUN_LUT:
      if os.path.exists(cls.RUN_LUT_FILE):
        cls.load_luts()
      else:
        cls.precompute()
        cls.save_luts()

  def __init__(self, cards=None):
    self.maybe_setup_hand()
    super(FastHand, self).__init__()

  def iter_runs(self):
    for color, rundex in self.rundex.copy().items():
      vector = self.rundex_to_vector(rundex)
      for start, jokers in self.RUN_LUT[min(self.jokers, self.RUN_LUT_MAX_JOKERS)][vector]:
        yield Run(Card(start, color), jokers)

  def iter_sets(self):
    for rank, colors in enumerate(self.setdices):
      if rank < 2:
        continue
      for combination in self.SET_LUT[min(self.SET_LUT_MAX_JOKERS, self.jokers)][colors.value]:
        yield Set(rank, combination)
