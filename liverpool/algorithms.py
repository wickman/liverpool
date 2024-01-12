from collections import defaultdict

from .common import CardSet, Card, Rank, Objective
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
)

from typing import Dict


def iter_sets_complete(h):
    h = IndexedHand(cards=h)
    for rank, colors in enumerate(h.setdexen):
        if rank < 2: continue
        for combination in sets_from_colors(colors, h.jokers):
          yield from materialized_sets_from_optional_colors(rank, combination)


def missing_utility(kv):
    _, usefulness_dict = kv
    t = sorted(usefulness_dict.items()).pop(0)
    return (t[0], -t[1])


CARD_SCORES = {
           2:  5,
           3:  5,
           4:  5,
           5:  5,
           6:  5,
           7:  5,
           8:  5,
           9:  5,
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


def find_useful_cards(h: Hand, objective: Objective, max_extra_jokers=0):
    useful_missing_cards = defaultdict(lambda: defaultdict(int)) # Card -> Distance -> Count
    useful_existing_cards = {card: 0 for card in h if not card.is_joker}
    useful_card_sets = defaultdict(int)  # CardSet --> int
    h = IndexedHand(cards=h)  # make a copy

    additional_jokers = 0
    jokers_beyond_utility = 0

    set_iterator = iter_sets_complete if objective.num_sets > 0 else iter_sets_lut
    run_iterator = iter_runs_lut

    while (not useful_missing_cards) or (jokers_beyond_utility < max_extra_jokers):
        if useful_missing_cards:
          jokers_beyond_utility += 1
        for meld in iter_melds(h, objective, run_iterator=run_iterator, set_iterator=set_iterator):
            cs = CardSet()
            for combo in meld:
                for card in combo:
                    if card.is_joker:
                        useful_missing_cards[card.as_common()][additional_jokers] += 1
                        cs.append(card.as_common())
                    else:
                        useful_existing_cards[card] += 1
            if cs:
                useful_card_sets[cs] += 1
        h.put_card(Card.joker())
        additional_jokers += 1

    return useful_missing_cards, useful_existing_cards, useful_card_sets


def least_useful(cards: Dict[Card, int]) -> Card:
    return sorted(cards.items(), key=existing_utility, reverse=True).pop(0)[0]