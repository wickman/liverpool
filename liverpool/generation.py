import contextlib
import gzip
import json
import os

from .combinatorics import (
    combinations_with_replacement,
    sort_uniq,
    uniq,
    unique_combinations,
)
from .common import (
   Add,
   Card,
   Color,
   Extend,
   Meld,
   Rank,
   Run,
   Set,
)
from .hand import Hand


__all__ = (
  'iter_adds',
  'iter_extends',
  'iter_melds',
  'iter_runs',
  'iter_sets',
  'iter_runs_lut',
  'iter_sets_lut',
  'iter_updates',
)


class Setdex(object):
  # Index set count.
  __slots__ = ('value',)

  NUM_BITS = 2  # support 0, 1, 2 decks.  NUM_BITS=3 is 0-7 decks. etc
  SET_MASK = (1 << NUM_BITS) - 1

  @classmethod
  def iter_all(cls):
    for value in range(2 ** (cls.NUM_BITS * 4)):
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


class IndexedHand(Hand):
  __slots__ = ('setdices', 'rundex')

  def __init__(self, cards=None):
    self.rundex = dict((color, [0] * (Rank.MAX + 1)) for color in Color.iter())
    self.setdices = [Setdex() for k in range(Rank.MAX + 1)]
    super(IndexedHand, self).__init__(cards)

  def iter_color(self, color):
    for rank, count in enumerate(self.rundex[color][:]):
      for _ in range(count):
        yield Card(rank, color)

  def take_card(self, card):
    taken_card = super(IndexedHand, self).take_card(card)
    if taken_card != Card.JOKER:
      self.rundex[card.color][card.rank] -= 1
      self.setdices[card.rank].remove(card.color)
    return taken_card

  def put_card(self, card):
    super(IndexedHand, self).put_card(card)

    if card != Card.JOKER:
      self.rundex[card.color][card.rank] += 1
      self.setdices[card.rank].append(card.color)


def interleave(card_vector, joker_vector):
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


# this could be improved with some thought.
#
# for joker_vector in unique_combinations(Rank.iter(), num_jokers):
#   for rank_selection in range(Run.MIN - num_jokers, len(ranks) + 1):
#     for joker_vector in unique_combinations(Rank.iter() - joker_vector, num_jokers):
#       ...
#
# for high joker counts, this will reduce the complexity
def ranks_from_rundex(rundex, jokers=0):
  total_jokers = min(2, jokers)  # cap runs at 2 jokers
  runs = []
  ranks = [rank for rank, count in enumerate(rundex) if count]
  for num_jokers in range(total_jokers + 1):
    for rank_selection in range(Run.MIN - num_jokers, len(ranks) + 1):
      for selected_cards in unique_combinations(ranks, rank_selection):
        for joker_vector in unique_combinations(Rank.iter(), num_jokers):
          try:
            start, jokers = interleave(selected_cards, joker_vector)
          except ValueError:
            continue
          if len(jokers) < Run.MIN:
            continue
          runs.append((start, tuple(jokers)))
  return sort_uniq(runs)


def orderable_colors_with_none(tup):
  return tuple(-1 if val is None else val for val in tup)


def sets_from_colors(colors, jokers=0, min_size=Set.MIN):
  def iterator():
    jokered_colors = [None] * jokers + list(colors)
    for set_size in range(min_size, len(jokered_colors) + 1):
      for combination in unique_combinations(jokered_colors, set_size):
        yield combination
  return sort_uniq(iterator(), key=orderable_colors_with_none)


def iter_sets(hand):
  if not isinstance(hand, IndexedHand):
    hand = IndexedHand(cards=list(hand))
  for rank, colors in enumerate(hand.setdices):
    if rank < 2:
      continue
    for combination in sets_from_colors(colors, hand.jokers):
      yield Set(rank, combination)


def iter_runs(hand):
  if not isinstance(hand, IndexedHand):
    hand = IndexedHand(cards=list(hand))
  for color, rundex in hand.rundex.copy().items():
    for start, jokers in ranks_from_rundex(rundex, hand.jokers):
      yield Run(Card(start, color), jokers)


def take_committed(hand, combos, method, commit=False):
  try:
    for combo in combos:
      method(combo)
    if commit:
      hand.commit()
    else:
      hand.rollback()
    return True
  except Hand.InvalidTake:
    hand.rollback()
    return False


def iter_melds(hand, strategy, set_iterator=iter_sets, run_iterator=iter_runs):
  if not isinstance(hand, IndexedHand):
    hand = IndexedHand(cards=list(hand))
  if strategy.num_runs == 0:
    for sets in uniq(combinations_with_replacement(set_iterator(hand), strategy.num_sets)):
      if take_committed(hand, sets, hand.take_set, commit=False):
        yield Meld(sets, None)
  elif strategy.num_sets == 0:
    for runs in uniq(combinations_with_replacement(run_iterator(hand), strategy.num_runs)):
      if take_committed(hand, runs, hand.take_run, commit=False):
        yield Meld(None, runs)
  else:
    for sets in uniq(combinations_with_replacement(set_iterator(hand), strategy.num_sets)):
      if take_committed(hand, sets, hand.take_set, commit=True):
        for runs in uniq(combinations_with_replacement(run_iterator(hand), strategy.num_runs)):
          if take_committed(hand, runs, hand.take_run, commit=False):
            yield Meld(sets, runs)
        hand.undo()


_RUN_LUT = {}
_RUN_LUT_FILE = os.path.expanduser('~/.liverpool_runs')
_RUN_LUT_MAX_JOKERS = 2


_SET_LUT = {}
_SET_LUT_FILE = os.path.expanduser('~/.liverpool_sets')
_SET_LUT_MAX_JOKERS = 3


def rundex_to_vector(rundex):
  value = 0
  for k, count in enumerate(rundex):
    if count:
      value |= (1 << (k - Rank.MIN))
  return value


def vector_to_rundex(vector):
  for k in range(Rank.MAX + 1):
    if k < Rank.MIN:
      yield 0
    else:
      yield 1 if vector & (1 << (k - Rank.MIN)) else 0


def precompute_luts():
  for total_jokers in range(_SET_LUT_MAX_JOKERS + 1):
    _SET_LUT[total_jokers] = {}
    for setdex in Setdex.iter_all():
      _SET_LUT[total_jokers][setdex.value] = list(sets_from_colors(setdex, total_jokers))

  for total_jokers in range(_RUN_LUT_MAX_JOKERS + 1):
    _RUN_LUT[total_jokers] = {}
    for card_vector in range(2 ** (Rank.MAX - Rank.MIN + 1)):
      rundex = list(vector_to_rundex(card_vector))
      _RUN_LUT[total_jokers][card_vector] = list(ranks_from_rundex(rundex, total_jokers))


# Consider a more compact representation, e.g. start,len,bitvector
def save_luts():
  with contextlib.closing(gzip.GzipFile(_RUN_LUT_FILE, 'wb')) as fp:
    fp.write(json.dumps(_RUN_LUT))
  with contextlib.closing(gzip.GzipFile(_SET_LUT_FILE, 'wb')) as fp:
    fp.write(json.dumps(_SET_LUT))


def load_luts():
  # json dictionary keys can only be strings, so we must coerce
  with contextlib.closing(gzip.GzipFile(_RUN_LUT_FILE, 'rb')) as fp:
    for num_jokers, lut in json.loads(fp.read().decode('utf-8')).items():
      _RUN_LUT[int(num_jokers)] = {}
      for card_vector, runs in lut.items():
        _RUN_LUT[int(num_jokers)][int(card_vector)] = runs
  with contextlib.closing(gzip.GzipFile(_SET_LUT_FILE, 'rb')) as fp:
    for num_jokers, lut in json.loads(fp.read().decode('utf-8')).items():
      _SET_LUT[int(num_jokers)] = {}
      for card_vector, sets in lut.items():
        _SET_LUT[int(num_jokers)][int(card_vector)] = sets


def maybe_precompute():
  if not _RUN_LUT or not _SET_LUT:
    if os.path.exists(_RUN_LUT_FILE):
      load_luts()
    else:
      precompute_luts()
      save_luts()


def iter_runs_lut(hand):
  maybe_precompute()
  if not isinstance(hand, IndexedHand):
    hand = IndexedHand(cards=list(hand))
  for color, rundex in hand.rundex.copy().items():
    vector = rundex_to_vector(rundex)
    for start, jokers in _RUN_LUT[min(hand.jokers, _RUN_LUT_MAX_JOKERS)][vector]:
      yield Run(Card(start, color), jokers)


def iter_sets_lut(hand):
  maybe_precompute()
  if not isinstance(hand, IndexedHand):
    hand = IndexedHand(cards=list(hand))
  for rank, colors in enumerate(hand.setdices):
    if rank < 2:
      continue
    for combination in _SET_LUT[min(_SET_LUT_MAX_JOKERS, hand.jokers)][colors.value]:
      yield Set(rank, combination)


def iter_adds(hand, set_):
  if not isinstance(hand, IndexedHand):
    hand = IndexedHand(cards=list(hand))
  for combination in sets_from_colors(hand.setdices[set_.rank], jokers=hand.jokers, min_size=1):
    yield Add(combination)


def iter_extends(hand, run, run_iterator=iter_runs):
  if not isinstance(hand, IndexedHand):
    hand = IndexedHand(cards=list(hand))

  new_hand = IndexedHand(cards=hand.iter_color(run.start.color))
  for card in run:
    new_hand.put_card(card)
  for _ in range(hand.jokers):
    new_hand.put_card(Card.JOKER)

  for extended_run in run_iterator(new_hand):
    try:
      yield run.extend_from(extended_run)
    except Run.InvalidExtend:
      continue


def iter_updates(hand, meld):
  pass


"""
new_h = Hand(cards=[Card(7, Color.HEART)])
new_h.put_card(Card.JOKER)
meld = list(iter_melds(h, Objective(1,1)))[-1]
from liverpool.generation import iter_adds, iter_extends
for extend in iter_extends(new_h, meld.runs[0]):
  print(extend)

"""
