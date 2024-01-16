from collections import defaultdict

from .common import Card, Rank, Objective, Color, Set
from .hand import Hand
from .generation import (
    iter_melds,
    iter_sets_lut,
    iter_runs_lut,
    IndexedHand,
)

from typing import Dict


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


def least_useful(cards: Dict[Card, int]) -> Card:
    return sorted(cards.items(), key=existing_utility, reverse=True).pop(0)[0]


def find_useful_cards(h: Hand, objective: Objective, max_extra_jokers=0):
    useful_missing_cards = defaultdict(lambda: defaultdict(int))  # Card -> Distance -> Count
    useful_existing_cards = {card: 0 for card in h if not card.is_joker}
    h = IndexedHand(cards=h)  # make a copy

    additional_jokers = 0
    jokers_beyond_utility = 0

    while (not useful_missing_cards) or (jokers_beyond_utility < max_extra_jokers):
        if useful_missing_cards:
            jokers_beyond_utility += 1
        for meld in iter_melds(
            h, objective, run_iterator=iter_runs_lut, set_iterator=iter_sets_lut
        ):
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


def document_utility(h, objective, useful_missing_cards, useful_existing_cards, indent=4):
    def _p(s):
        print(" " * indent + str(s))

    def _pp(s):
        print(" " * (indent + 4) + str(s))

    _p("----sets-----")
    for s in iter_sets_lut(h):
        _pp(s)

    _p("----runs-----")
    for r in iter_runs_lut(h):
        _pp(r)

    _p("----melds-----")
    for m in iter_melds(h, objective):
        _pp(m)

    _p("----useful missing cards-----")
    for c, usefulness in sorted(useful_missing_cards.items(), key=missing_utility):
        _pp("%s %s" % (c, dict(usefulness)))

    _p("----useless hand cards-----")
    for c, usefulness in sorted(useful_existing_cards.items(), key=existing_utility, reverse=True):
        _pp("%s %s" % (c, usefulness))
