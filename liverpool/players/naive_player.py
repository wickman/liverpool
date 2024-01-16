from typing import Dict, Tuple, List

from ..algorithms import find_useful_cards, least_useful
from ..common import Card, Objective, Meld, MeldUpdate
from ..generation import iter_melds, iter_updates_multi, iter_sets_lut, iter_runs_lut
from ..hand import Hand
from ..game import Player, Action, Move


# Put these scores on the MeldUpdate / Meld classes themselves
def edit_score(updates: Dict[int, MeldUpdate]) -> int:
    score = 0
    for update in updates.values():
        if update.adds is not None:
            score += sum(card.score for add in update.adds.values() for card in add)
        if update.extends is not None:
            score += sum(card.score for extend in update.extends.values() for card in extend)
    return score


def meld_score(meld: Meld) -> Tuple[int, int]:
    meld_cards = [card for combo in meld for card in combo]
    return sum(card.score for card in meld_cards), len(meld_cards)


class NaivePlayer(Player):
    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)
        self._melds = {}
        self._useful_missing, self._useful_existing = None, None

    def set_objective(self, objective: Objective) -> None:
        super().set_objective(objective)
        self._melds = {}
        self._useful_missing, self._useful_existing = None, None

    def take(self, card: Card) -> None:
        super().take(card)
        self._useful_missing, self._useful_existing = None, None

    def discard(self, card: Card) -> None:
        super().discard(card)
        self._useful_missing, self._useful_existing = None, None

    def _find_useful_cards(self):
        if self._useful_missing is None:
            self._useful_missing, self._useful_existing = find_useful_cards(
                self.hand, self.objective
            )
        return self._useful_missing, self._useful_existing

    def publish_action(self, action: Action, melds: Dict[int, Meld]) -> None:
        if action.init:
            self.set_objective(action.init.objective)

    def accepts_discard(self, card: Card, melds: Dict[int, Meld]) -> bool:
        if self.pid in melds:
            return False
        useful_missing, _ = self._find_useful_cards()
        if card in useful_missing:
            return True
        return False

    def accepts_purchase(self, card: Card, melds: Dict[int, Meld]) -> bool:
        if self.pid in melds:
            return False
        useful_missing, _ = self._find_useful_cards()
        if card in useful_missing:
            return True
        return False

    def _iter_melds(self, hand: Hand) -> List[Meld]:
        if hand not in self._melds:
            self._melds[hand] = sorted(
                iter_melds(hand, self.objective, iter_sets_lut, iter_runs_lut),
                key=meld_score,
                reverse=True,
            )
        return self._melds[hand][:]

    def request_move(self, melds: Dict[int, Meld]) -> Move:
        print("Player pid: %d, hand: %s" % (self.pid, self.hand))

        remaining_cards = Hand(self.hand)

        my_meld = new_meld = None
        if self.pid not in melds:
            my_melds = self._iter_melds(remaining_cards)
            if len(my_melds) == 0:
                _, useful_existing = self._find_useful_cards()
                return Move(discard=least_useful(useful_existing))
            else:
                for meld in my_melds:
                    print("  - Considering meld %s (score=%s)" % (meld, meld_score(meld)))
            new_meld = melds[self.pid] = my_melds.pop(0)
            for combo in new_meld:
                for card in combo:
                    remaining_cards.take_card(card.dematerialized())
        else:
            my_meld = melds[self.pid]

        updates = {}
        if my_meld is not None and new_meld is None:
            # iterable of Dict[int, MeldUpdate] (pid -> MeldUpdate)
            possible_updates = sorted(iter_updates_multi(remaining_cards, melds), key=edit_score)
            if possible_updates:
                updates = possible_updates.pop()
                for update in updates.values():
                    for card in update:
                        remaining_cards.take_card(card.dematerialized())

        # need to find the card least likely to be useful for future edits...so not just against our own
        # hand but against all other melds.  leave this as a TODO and just discard the most valuable card
        highest_value_card = None
        if not remaining_cards.empty:
            highest_value_card = max(remaining_cards, key=lambda card: card.score)
        return Move(meld=new_meld, updates=updates, discard=highest_value_card)


class AggressiveBuyPlayer(NaivePlayer):
    def __init__(self, *args, always_buy_if_missing=4, **kw) -> None:
        super().__init__(*args, **kw)
        self._always_buy_if_missing = always_buy_if_missing

    def accepts_purchase(self, card: Card, melds: Dict[int, Meld]) -> bool:
        if self.pid in melds:
            return False
        useful_missing, _ = self._find_useful_cards()
        if card in useful_missing:
            return True
        missing_cards = 100
        for card, missing_count in useful_missing.items():
            missing_cards = min(missing_cards, min(missing_count))
        if missing_cards >= self._always_buy_if_missing:
            return True
        return False
