from collections import defaultdict

from .common import CardSet, Card, Rank, Objective, Color, Set
from .hand import Hand
from .generation import (
    sets_from_colors,
    materialized_sets_from_optional_colors,
    iter_melds,
    iter_sets,
    iter_sets_lut,
    iter_runs,
    iter_runs_lut,
    IndexedHand,
    _RUN_LUT,
    rundex_to_vector,
)

from typing import Dict


def iter_sets_complete(h):
    h = IndexedHand(cards=h)
    for rank, colors in enumerate(h.setdexen):
        if rank < 2:
            continue
        for combination in sets_from_colors(colors, h.jokers):
            yield from materialized_sets_from_optional_colors(rank, combination)


def missing_utility(kv):
    _, usefulness_dict = kv
    t = sorted(usefulness_dict.items()).pop(0)
    return (t[0], -t[1])


CARD_SCORES = {
    2: 5,
    3: 5,
    4: 5,
    5: 5,
    6: 5,
    7: 5,
    8: 5,
    9: 5,
    10: 10,
    Rank.JACK: 10,
    Rank.QUEEN: 10,
    Rank.KING: 10,
    Rank.ACE: 15,
    None: 15,
}


def existing_utility(kv):
    rank = kv[0].rank
    count = kv[1]
    return (-count, CARD_SCORES[rank])


# A smarter version of this would work directly off the hand's rundexen and setdexen and
# fill in fragments, rather than relying upon iter_melds with jokers to do the work.  For
# example if we had iter_value --> {card: contiguous_count} which represents
# how many contiguous cards are left or right of that card.  This could even be pregenerated
# by a LUT.
#
# For example, if the rundex looked like:
#    x 2 x x 5 x 7 x x x x Q K x
# then the iter_value(1) result would look like
#    0 0 2 2 0 3 0 2 0 0 3 0 0 3
# for which the higher the score, the more we want that card.
#
# iter_value(2) over the following would be:
#    0 0 4 0 0 0 0 3 2 4 0 0 0 0
# or something to that effect.


def find_useful_cards(h: Hand, objective: Objective, max_extra_jokers=0):
    useful_missing_cards = defaultdict(lambda: defaultdict(int))  # Card -> Distance -> Count
    useful_existing_cards = {card: 0 for card in h if not card.is_joker}
    h = IndexedHand(cards=h)  # make a copy

    additional_jokers = 0
    jokers_beyond_utility = 0

    # set_iterator = iter_sets_complete if objective.num_sets > 0 else iter_sets_lut
    set_iterator = iter_sets_lut
    run_iterator = iter_runs_lut

    while (not useful_missing_cards) or (jokers_beyond_utility < max_extra_jokers):
        if useful_missing_cards:
            jokers_beyond_utility += 1
        for meld in iter_melds(h, objective, run_iterator=run_iterator, set_iterator=set_iterator):
            for combo in meld:
                for card in combo:
                    if card.is_joker:
                        useful_missing_cards[card.as_common()][additional_jokers] += 1
                        if isinstance(combo, Set):
                            # since iter_sets only materializes as Color.SPADES, we need to add the other colors
                            # which are useful if we come across them as a discard
                            for color in Color.iter():
                                if color != card.color:
                                    useful_missing_cards[Card.of(card.rank, color)][
                                        additional_jokers
                                    ] += 1
                    else:
                        useful_existing_cards[card] += 1
        h.put_card(Card.joker())
        additional_jokers += 1

    return useful_missing_cards, useful_existing_cards


def find_useful_cards_naive(h: Hand, objective: Objective):
    useful_missing_cards = defaultdict(lambda: defaultdict(int))  # Card -> Distance -> Count
    useful_existing_cards = {card: 0 for card in h if not card.is_joker}
    h = IndexedHand(cards=h)  # make a copy

    # useful_set_cards should be quite easy to compute.  iterate over setdexen, then we say
    #  if setdexen[rank] < 3:
    #    useful_missing_cards[Card.of(rank, *)] = 3 - setdexen[rank]
    #    useful_existing_cards[<every card of rank 'rank' in hand>] = 1
    if objective.num_sets:
        for rank, sd in enumerate(h.setdexen):
            if rank < 2:
                continue
            if sd.count == 0:
                continue
            for color in Color.iter():
                card = Card.of(rank, color)
                if card in h:
                    useful_existing_cards[card] += sd.count
                useful_missing_cards[card][3 - sd.count] += 1
    if objective.num_runs:
        for jokers in range(4):
            for color, rundex in h.rundexen.items():
                for start, joker_vec in _RUN_LUT[jokers][rundex_to_vector(rundex)]:
                    for index, has_joker in enumerate(joker_vec):
                        if has_joker:
                            useful_missing_cards[Card.of(start + index, color)][jokers] += 1
                        else:
                            useful_existing_cards[Card.of(start + index, color)] += 1

    return useful_missing_cards, useful_existing_cards


def least_useful(cards: Dict[Card, int]) -> Card:
    return sorted(cards.items(), key=existing_utility, reverse=True).pop(0)[0]
