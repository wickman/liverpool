from __future__ import print_function, unicode_literals

from collections import defaultdict
import itertools
import os
import pickle

from .combinatorics import (
    combinations_with_replacement,
    unique_combinations,
    sort_uniq,
)
from .common import (
    Card,
    Color,
    Lay,
    Objective,
    Rank,
    Run,
    Set,
)


class Hand(object):
  class Error(Exception): pass
  class InvalidCard(Error): pass
  class InvalidTake(Error): pass

  __slots__ = ('cards', 'stack', 'setdex', 'rundex', 'jokers')

  RUN_LUT = {}
  RUN_LUT_FILE = os.path.expanduser('~/.liverpool')
  RUN_LUT_MAX_JOKERS = 2

  @classmethod
  def precompute_runs(cls):
    print('Generating run lookup tables.')

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

    for total_jokers in range(cls.RUN_LUT_MAX_JOKERS + 1):
      cls.RUN_LUT[total_jokers] = defaultdict(list)
      for card_vector in range(2**13):
        running_lut = []
        ranks = list(vector_to_cards(card_vector))
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

  @classmethod
  def save_lut(cls):
    with open(cls.RUN_LUT_FILE, 'wb') as fp:
      pickle.dump(cls.RUN_LUT, fp)

  @classmethod
  def load_lut(cls):
    with open(cls.RUN_LUT_FILE, 'rb') as fp:
      cls.RUN_LUT = pickle.load(fp)

  @classmethod
  def maybe_setup_hand(cls):
    if not cls.RUN_LUT:
      if os.path.exists(cls.RUN_LUT_FILE):
        cls.load_lut()
      else:
        cls.precompute_runs()
        cls.save_lut()

  def __init__(self, cards=None):
    self.maybe_setup_hand()
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
    self._map_run(run, self.take_card)

  def take_set(self, set_):
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
      for start, jokers in self.RUN_LUT[min(self.jokers, self.RUN_LUT_MAX_JOKERS)][vector]:
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

  def __str__(self):
    cards = []
    for card, count in self.cards.items():
      for _ in range(count):
        cards.append(card)
    return 'Hand(%s)' % ' '.join(map(str, cards))