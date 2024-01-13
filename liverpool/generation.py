"""Utilities for move generation in liverpool rummy.

Some new concepts:

  * Setdex: A set of colors represented as a bit vector.  For example with 2 decks, it's possible
    to have up to 8 cards of the same rank (not counting jokers.)  Given some combination of 8 colors,
    we precompute all the permutations of those colors to yield a set and store those in a lookup table.
    The Setdex is merely a way to go back and forth from a scalar number to a set of colors.

  * Rundex: A sequence of ranks of a specific color represented as a bit vector.  Given a set number of
    jokers, we can precompute all possible runs for a given Rundex and which positions are materialized
    jokers as (start_rank, joker_indices) tuples.

"""

from collections import defaultdict
import contextlib
import itertools
import gzip
import json
import os
import time

from typing import Iterable, Optional, List, Dict

from .combinatorics import (
    sort_uniq,
    uniq,
    unique_combinations,
)
from .common import (
    Card,
    Color,
    Meld,
    Rank,
    Run,
    Set,
    Add,
    Extend,
    MeldUpdate,
)
from .hand import Hand


__all__ = (
    "iter_adds",
    "iter_extends",
    "iter_melds",
    "iter_runs",
    "iter_sets",
    "iter_runs_lut",
    "iter_sets_lut",
    "iter_updates",
)


# TODO roll up the rest of the set generation logic here
class Setdex:
    """A set's colors represented as a bit vector.

    There are 4 colors for a Card (2 bits = 0, 1, 2, 3 = CLUB, SPADE, HEART, DIAMOND)
    There are NUM_BITS for the number of decks, so for 0, 1, 2 decks we need NUM_BITS = 2,
    for 3-7 decks we need NUM_BITS = 3, etc.
    """

    # Index set count.
    __slots__ = ("value", "count")

    NUM_BITS = 2  # support 0, 1, 2 decks.  NUM_BITS=3 is 0-7 decks. etc
    SET_MASK = (1 << NUM_BITS) - 1

    @classmethod
    def iter_all(cls) -> Iterable["Setdex"]:
        for value in range(2 ** (cls.NUM_BITS * 4)):
            yield cls(value)

    def __init__(self, value: int = 0) -> None:
        self.value = value
        self.count = len(list(self))

    def append(self, color) -> None:
        """Add a color to the set.  NOT BOUNDS CHECKED."""
        self.value += 1 << (self.NUM_BITS * color)
        self.count += 1

    def remove(self, color) -> None:
        """Remove a color from the set.  NOT BOUNDS CHECKED."""
        self.value -= 1 << (self.NUM_BITS * color)
        self.count -= 1

    def __iter__(self) -> Iterable[int]:
        """List the colors in the set."""
        for color in Color.iter():
            count = (self.value & (self.SET_MASK << (self.NUM_BITS * color))) >> (
                self.NUM_BITS * color
            )
            for _ in range(count):
                yield color


# TODO roll up the rest of the methods into here and put run generation logic here
class Rundex:
    @classmethod
    def from_vector(cls, vector) -> "Rundex":
        rd = cls()
        for k in range(Rank.MAX + 1):
            if k < Rank.MIN:
                yield 0
            else:
                if vector & (1 << (k - Rank.MIN)):
                    rd.add(k)
        return rd

    def __init__(self) -> None:
        self._array = bytearray([0] * (Rank.MAX + 1))

    def add(self, rank: int) -> None:
        self._array[rank] += 1

    def remove(self, rank: int) -> None:
        self._array[rank] -= 1
        assert self._array[rank] >= 0

    def __iter__(self) -> Iterable[int]:
        array_copy = bytes(self._array)
        for rank in range(Rank.MAX + 1):
            for _ in range(array_copy[rank]):
                yield rank

    def iter_ranks(self) -> Iterable[int]:
        for rank, count in enumerate(self._array):
            if count:
                yield rank

    def to_vector(self) -> int:
        value = 0
        for rank, count in enumerate(self._array):
            if count:
                value |= 1 << (rank - Rank.MIN)
        return value


class IndexedHand(Hand):
    """A hand of cards annotated by a rundex and setdexen for fast combinatorial move generation."""

    __slots__ = ("setdexen", "rundexen")

    def __init__(self, cards: Optional[List[Card]] = None):
        self.rundexen = dict((color, Rundex()) for color in Color.iter())
        self.setdexen = [Setdex() for k in range(Rank.MAX + 1)]
        super(IndexedHand, self).__init__(cards)

    def iter_color(self, color):
        for rank in self.rundexen[color]:
            yield Card.of(rank, color)

    def take_card(self, card):
        taken_card = super(IndexedHand, self).take_card(card)
        if not taken_card.is_joker:
            self.rundexen[card.color].remove(card.rank)
            self.setdexen[card.rank].remove(card.color)
        return taken_card

    def put_card(self, card):
        super(IndexedHand, self).put_card(card)

        if not card.is_joker:
            self.rundexen[card.color].add(card.rank)
            self.setdexen[card.rank].append(card.color)


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
def ranks_from_rundex(rundex: Rundex, jokers=0):
    """Given a rundex, return all possible runs.

    Runs are a tuple of (start_rank, joker_indices) where joker_indices is a
    tuple of indices into the run that are jokers.  I have no idea how to
    know how long the run is?
    """
    # total_jokers = min(2, jokers)  # cap runs at 2 jokers
    total_jokers = min(3, jokers)
    runs = []
    ranks = [rank for rank in rundex.iter_ranks()]
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


def materialized_sets_from_optional_colors(rank, colors: List[Optional[int]]) -> Iterable[Set]:
    jokers = colors.count(None)
    non_jokers = [color for color in colors if color is not None]
    for joker_colors in itertools.combinations(range(Color.MAX + 1), jokers):
        cards = [Card.of(rank, color, joker=True) for color in joker_colors]
        cards.extend(Card.of(rank, color) for color in non_jokers)
        yield Set(cards)


def take_committed(hand, combos, commit=False):
    try:
        for combo in combos:
            hand.take_combo(combo)
        if commit:
            hand.commit()
        else:
            hand.rollback()
        return True
    except Hand.InvalidTake:
        hand.rollback()
        return False


_RUN_LUT = {}
_RUN_LUT_FILE = os.path.expanduser("~/.liverpool_runs")
_RUN_LUT_MAX_JOKERS = 3


_SET_LUT = {}
_SET_LUT_FILE = os.path.expanduser("~/.liverpool_sets")
_SET_LUT_MAX_JOKERS = 3


def precompute_luts(max_set_jokers=_SET_LUT_MAX_JOKERS, max_run_jokers=_RUN_LUT_MAX_JOKERS):
    print("Precomputing LUTS. This will take a while...")

    for total_jokers in range(max_set_jokers + 1):
        now = time.time()
        print("Precomputing sets with %d jokers" % total_jokers, end="")
        _SET_LUT[total_jokers] = {}
        for setdex in Setdex.iter_all():
            _SET_LUT[total_jokers][setdex.value] = list(sets_from_colors(setdex, total_jokers))
        print("  took %0.2f seconds" % (time.time() - now))

    for total_jokers in range(max_run_jokers + 1):
        now = time.time()
        print("Precomputing runs with %d jokers..." % total_jokers, end="")
        _RUN_LUT[total_jokers] = {}
        for card_vector in range(2 ** (Rank.MAX - Rank.MIN + 1)):
            rundex = Rundex.from_vector(card_vector)
            _RUN_LUT[total_jokers][card_vector] = list(ranks_from_rundex(rundex, total_jokers))
        print("  took %0.2f seconds" % (time.time() - now))


# Consider a more compact representation, e.g. start,len,bitvector
def save_luts():
    with contextlib.closing(gzip.GzipFile(_RUN_LUT_FILE, "w")) as fp:
        fp.write(json.dumps(_RUN_LUT).encode("utf-8"))
    with contextlib.closing(gzip.GzipFile(_SET_LUT_FILE, "w")) as fp:
        fp.write(json.dumps(_SET_LUT).encode("utf-8"))


def load_luts():
    # json dictionary keys can only be strings, so we must coerce
    with contextlib.closing(gzip.GzipFile(_RUN_LUT_FILE, "r")) as fp:
        for num_jokers, lut in json.load(fp).items():
            _RUN_LUT[int(num_jokers)] = {}
            for card_vector, runs in lut.items():
                _RUN_LUT[int(num_jokers)][int(card_vector)] = runs
    with contextlib.closing(gzip.GzipFile(_SET_LUT_FILE, "r")) as fp:
        for num_jokers, lut in json.load(fp).items():
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


def iter_runs(hand):
    if not isinstance(hand, IndexedHand):
        hand = IndexedHand(cards=list(hand))
    for color, rundex in hand.rundexen.copy().items():  # why is this copied?
        for start, jokers in ranks_from_rundex(rundex, hand.jokers):
            # print('run: %s, %s, %s' % (color, start, jokers))
            yield Run.of(color, start, jokers)


def iter_runs_lut(hand):
    maybe_precompute()
    if not isinstance(hand, IndexedHand):
        hand = IndexedHand(cards=list(hand))
    for color, rundex in hand.rundexen.copy().items():  # why is this copied?
        vector = rundex.to_vector()
        for start, jokers in _RUN_LUT[min(hand.jokers, _RUN_LUT_MAX_JOKERS)][vector]:
            # print('run: %s, %s, %s' % (color, start, jokers))
            yield Run.of(color, start, jokers)


def iter_sets(hand):
    if not isinstance(hand, IndexedHand):
        hand = IndexedHand(cards=list(hand))
    for rank, colors in enumerate(hand.setdexen):
        if rank < 2:
            continue
        for combination in sets_from_colors(colors, min(_SET_LUT_MAX_JOKERS, hand.jokers)):
            yield Set.of(rank, combination)


def iter_sets_lut(hand):
    maybe_precompute()
    if not isinstance(hand, IndexedHand):
        hand = IndexedHand(cards=list(hand))
    for rank, colors in enumerate(hand.setdexen):
        if rank < 2:
            continue
        for combination in _SET_LUT[min(_SET_LUT_MAX_JOKERS, hand.jokers)][colors.value]:
            yield Set.of(rank, combination)
            # Change this to the following if we need colorized sets:
            #    yield from materialized_sets_from_optional_colors(rank, combination)
            # Otherwise Set.of will always materialize to spades which is fine unless you're
            # leveraging iter_sets* to search for edits to existing melds.


def iter_melds(hand, strategy, set_iterator=iter_sets, run_iterator=iter_runs):
    if not isinstance(hand, IndexedHand):
        hand = IndexedHand(cards=list(hand))
    if strategy.num_runs == 0:
        for sets in uniq(itertools.combinations(set_iterator(hand), strategy.num_sets)):
            if take_committed(hand, sets, commit=False):
                yield Meld(sets, None)
    elif strategy.num_sets == 0:
        for runs in uniq(itertools.combinations(run_iterator(hand), strategy.num_runs)):
            if take_committed(hand, runs, commit=False):
                yield Meld(None, runs)
    else:
        for sets in uniq(itertools.combinations(set_iterator(hand), strategy.num_sets)):
            if take_committed(hand, sets, commit=True):
                for runs in uniq(itertools.combinations(run_iterator(hand), strategy.num_runs)):
                    if take_committed(hand, runs, commit=False):
                        yield Meld(sets, runs)
                hand.undo()


# TODO Add and Extend should be defined in common and there should be .update methods
# on Set and Run respectively that takes Set.update(Add) -> Set, and Run.update(Extend) -> Run.
# Similarly Meld.Update(MeldUpdate) -> Meld.


def iter_adds(hand, set_):
    if not isinstance(hand, IndexedHand):
        hand = IndexedHand(cards=list(hand))
    yield Add()
    for combination in sets_from_colors(hand.setdexen[set_.rank], jokers=hand.jokers, min_size=1):
        yield Add(
            Card.of(set_.rank, color)
            if color is not None
            else Card.of(set_.rank, Color.SPADE, joker=True)
            for color in combination
        )


def extend_from(run1: Run, run2: Run) -> Extend:
    if run1.color != run2.color:
        raise ValueError("Runs must have the same color.")

    my_cards: List[Card] = list(run1)
    other_cards: List[Card] = list(run2)

    left = []
    while other_cards and other_cards[0] < my_cards[0]:
        left.append(other_cards.pop(0))

    other_cards_overlap, right = (
        other_cards[0 : len(my_cards)],
        other_cards[len(my_cards) :],
    )

    if other_cards_overlap != my_cards:
        raise ValueError("Runs must overlap.")

    if not left and not right:
        raise ValueError("Empty extension.")

    return Extend(left, right)


def iter_extends(hand: Hand, run: Run, run_iterator=iter_runs):
    if not isinstance(hand, IndexedHand):
        hand = IndexedHand(cards=list(hand))

    # get hand containing just the cards that are the same color as the run
    new_hand = IndexedHand(cards=hand.iter_color(run.color))
    # add the run cards to the hand
    for card in run:
        new_hand.put_card(card.dematerialized())
    # add jokers to the hand
    for _ in range(hand.jokers):
        new_hand.put_card(Card.joker())

    # why yield empty run?
    yield Extend()

    # generate all possible runs that can be generated from the hand
    for extended_run in run_iterator(new_hand):
        try:
            # generate Extends from the run and the extended run
            yield extend_from(run, extended_run)
        except ValueError:
            continue


def iter_updates(hand, meld, run_iterator=iter_runs) -> Iterable[MeldUpdate]:
    adds = {}
    extends = {}
    for set_id, set_ in enumerate(meld.sets):
        adds[set_id] = list(iter_adds(hand, set_))
    for run_id, run in enumerate(meld.runs):
        extends[run_id] = list(iter_extends(hand, run, run_iterator))
    mutations = list(adds.items()) + list(extends.items())
    for size in range(len(mutations) + 1):
        for combination in itertools.combinations(mutations, size):
            combos_only = [combo for combo_id, combo in combination]
            if take_committed(hand, combos_only, commit=False):
                yield MeldUpdate(
                    adds={
                        combo_id: combo for combo_id, combo in combination if isinstance(combo, Add)
                    },
                    extends={
                        combo_id: combo
                        for combo_id, combo in combination
                        if isinstance(combo, Extend)
                    },
                )


def iter_updates_multi(
    hand, melds: Dict[int, Meld], run_iterator=iter_runs
) -> Iterable[Dict[int, MeldUpdate]]:
    adds = []
    extends = []
    for pid, meld in melds.items():
        for set_id, set_ in enumerate(meld.sets):
            adds.extend((pid, set_id, add_) for add_ in iter_adds(hand, set_) if len(add_) > 0)
        for run_id, run in enumerate(meld.runs):
            extends.extend(
                (pid, run_id, extend)
                for extend in iter_extends(hand, run, run_iterator)
                if len(extend) > 0
            )

    mutations = adds + extends

    print("mutation candidates (iter_updates_multi):")
    for pid, mid, mutation in mutations:
        print("   - %d -> %d += %s" % (pid, mid, mutation))
    for size in range(len(mutations) + 1):
        for combination in itertools.combinations(mutations, size):
            combos_only = [combo for pid, combo_id, combo in combination]
            if take_committed(hand, combos_only, commit=False):
                updates = defaultdict(dict)
                for pid, combo_id, combo in combination:
                    updates[pid][combo_id] = combo
                yield {
                    pid: MeldUpdate(
                        adds={
                            combo_id: combo
                            for combo_id, combo in combos.items()
                            if isinstance(combo, Add)
                        },
                        extends={
                            combo_id: combo
                            for combo_id, combo in combos.items()
                            if isinstance(combo, Extend)
                        },
                    )
                    for pid, combos in updates.items()
                }
