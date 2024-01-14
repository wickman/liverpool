from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import time

from .algorithms import (
    find_useful_cards,
    find_useful_cards_naive,
    least_useful,
    missing_utility,
    existing_utility,
)
from .common import Deck, Card, Objective, Meld, MeldUpdate, Add, Extend
from .hand import Hand
from .generation import (
    iter_sets,
    iter_melds,
    iter_runs,
    iter_runs_lut,
    iter_sets_lut,
    iter_extends,
    iter_adds,
    iter_updates_multi,
    iter_updates_multi_recursive,
)


class Move:
    def __init__(
        self,
        meld: Optional[Meld] = None,
        updates: Dict[int, MeldUpdate] = None,
        discard: Optional[Card] = None,
    ) -> None:
        self.meld = meld
        self.updates = updates or {}
        self.discard = discard

    def __iter__(self):
        if self.meld is not None:
            for combo in self.meld:
                for card in combo:
                    yield card
        if self.updates:
            for update in self.updates.values():
                yield from update
        if self.discard is not None:
            yield self.discard

    def __repr__(self) -> str:
        return "Move(meld=%r, updates=%r, discard=%r)" % (
            self.meld,
            self.updates,
            self.discard,
        )

    def __str__(self):
        return "Meld: %s / Edits: {%s} / Discard: %s" % (
            self.meld,
            ", ".join("%d=%s" % (pid, update) for pid, update in self.updates.items()),
            self.discard,
        )


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


def generate_move(
    pid: int,
    hand: Hand,
    objective: Objective,
    melds: Dict[int, Meld],
    meld_scorer=meld_score,
    update_scorer=edit_score,
) -> List[Move]:
    remaining_cards = Hand(hand)

    my_meld = new_meld = None
    if pid not in melds:
        my_melds = sorted(iter_melds(hand, objective), key=meld_score, reverse=True)
        # XXX you are here
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
        possible_updates = sorted(
            iter_updates_multi_recursive(remaining_cards, melds), key=edit_score
        )
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


@dataclass
class Action:
    player_id: int
    move: Optional[Move] = None
    purchase: Optional[Card] = None
    flip_discard: Optional[Card] = None
    draw_discard: Optional[Card] = None
    draw_deck: bool = False
    shuffle_discards: bool = False

    def __str__(self):
        if self.move is not None:
            return "Player %d moves %s" % (self.player_id, self.move)
        if self.purchase is not None:
            return "Player %d purchases %s" % (self.player_id, self.purchase)
        if self.flip_discard is not None:
            return "Dealer flips %s" % self.flip_discard
        if self.draw_discard is not None:
            return "Player %d draws discard %s" % (self.player_id, self.draw_discard)
        if self.draw_deck:
            return "Player %d draws from deck" % self.player_id
        if self.shuffle_discards:
            return "Dealer shuffles discards"
        return "Unknown action"


class Player(metaclass=ABCMeta):
    def __init__(self, pid: int, hand: Optional[Hand] = None) -> None:
        self.pid = pid
        self.objective = None
        self.hand = hand or Hand()

    def set_objective(self, objective: Objective) -> None:
        self.objective = objective

    @property
    def hand_size(self) -> int:
        return len(self.hand)

    def take(self, card: Card) -> None:
        self.hand.put_card(card)

    def discard(self, card: Card) -> None:
        self.hand.take_card(card.dematerialized())

    def clear(self) -> None:
        self.hand = Hand()

    @abstractmethod
    def publish_action(self, action: Action, melds: Dict[int, Meld]) -> None:
        pass

    @abstractmethod
    def accepts_discard(self, card: Card, melds: Dict[int, Meld]) -> bool:
        pass

    @abstractmethod
    def accepts_purchase(self, card: Card, melds: Dict[int, Meld]) -> bool:
        pass

    @abstractmethod
    def request_move(self, melds: Dict[int, Meld]) -> Move:
        pass


def document_utility(h, objective, useful_missing_cards, useful_existing_cards, indent=4):
    def _p(s):
        print(" " * indent + str(s))

    def _pp(s):
        print(" " * (indent + 4) + str(s))

    _p("----sets-----")
    for s in iter_sets(h):
        _pp(s)

    _p("----runs-----")
    for r in iter_runs(h):
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


class NaivePlayer(Player):
    def __init__(self, *args, super_naive=False, **kw) -> None:
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
            self._useful_missing, self._useful_existing = find_useful_cards(self.hand, self.objective)
        return self._useful_missing, self._useful_existing

    def publish_action(self, action: Action, melds: Dict[int, Meld]) -> None:
        # ignore published actions
        pass

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
        #return sorted(iter_melds(self.hand, self.objective, iter_sets_lut, iter_runs_lut), key=meld_score, reverse=True)
    
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
            possible_updates = sorted(
                iter_updates_multi_recursive(remaining_cards, melds), key=edit_score
            )
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


class Trick:
    def __init__(
        self, objective: Objective, card_count: int, dealer_pid: int, players: Dict[int, Player]
    ) -> None:
        self.objective = objective
        self.card_count = card_count
        self.dealer_pid = dealer_pid
        self.__dealer_cursor = dealer_pid
        self.__deck = Deck.new(count=Game.PLAYERS_TO_DECKS[len(players)])
        self.__discards: List[Card] = []
        self.__actions: List[Action] = []
        self.__players = players
        self.__melds: Dict[int, Meld] = {}  # pid -> Meld

    @property
    def last_action(self) -> Optional[Action]:
        return self.__actions[-1] if self.__actions else None

    @property
    def current_discard(self) -> Optional[Card]:
        return self.__discards[-1] if self.__discards else None

    @property
    def deck_size(self) -> int:
        return len(self.__deck)

    @property
    def discard_size(self) -> int:
        return len(self.__discards)

    @property
    def melds(self) -> Dict[int, Meld]:
        return self.__melds.copy()

    def _process_move(self, action: Action) -> None:
        assert action.move is not None
        if action.move.meld:
            self.__melds[action.player_id] = action.move.meld
        for pid, update in action.move.updates.items():
            self.__melds[pid] = self.__melds[pid].update(update)
        for card in action.move:
            self.__players[action.player_id].discard(card)
        if action.move.discard is None:
            assert self.__players[action.player_id].hand_size == 0
        else:
            self.__discards.append(action.move.discard)

    def _process_purchase(self, action: Action) -> None:
        purchase = self.__discards.pop()
        assert purchase == action.purchase
        self.__players[action.player_id].take(action.purchase)

    def _process_flip_discard(self, action: Action) -> None:
        assert action.flip_discard == self.current_discard

    def _process_draw_discard(self, action: Action) -> None:
        self.__players[action.player_id].take(self.current_discard)
        self.__discards.pop()

    def _process_draw_deck(self, action: Action) -> None:
        self.__players[action.player_id].take(self.__deck.pop())

    def _process_shuffle_discards(self, action: Action) -> None:
        self.__deck = Deck(self.__discards)
        self.__deck.shuffle()
        self.__discards = []

    def process_action(self, elapsed: float, action: Action) -> None:
        print("  - Processing action: %s (%.1fus)" % (action, 1000000 * elapsed))
        actions = sum(
            [
                action.move is not None,
                action.purchase is not None,
                action.flip_discard is not None,
                action.draw_discard is not None,
                action.shuffle_discards,
                action.draw_deck,
            ]
        )
        if actions != 1:
            raise ValueError("Expected one action, got %d" % actions)
        if action.move is not None:
            self._process_move(action)
        elif action.purchase is not None:
            self._process_purchase(action)
        elif action.flip_discard is not None:
            self._process_flip_discard(action)
        elif action.draw_discard is not None:
            self._process_draw_discard(action)
        elif action.draw_deck:
            self._process_draw_deck(action)
        elif action.shuffle_discards:
            self._process_shuffle_discards(action)
        else:
            raise ValueError("Unknown action %s" % action)
        for player in self.__players.values():
            player.publish_action(action, self.melds)

    def is_over(self) -> bool:
        return any(player.hand_size == 0 for player in self.__players.values())

    def tabulate(self) -> Dict[int, int]:
        player_scores = {pid: 0 for pid in range(len(self.__players))}
        for pid, player in self.__players.items():
            for card in player.hand:
                player_scores[pid] += card.score
            player.clear()
        return player_scores

    def deal(self):
        cursor = self.__dealer_cursor + 1
        for _ in range(self.card_count):
            for k in range(len(self.__players)):
                player = self.__players[cursor % len(self.__players)]
                action = Action(player.pid, draw_deck=True)
                self.process_action(0.0, action)
                cursor += 1
        self.__discards.append(self.__deck.pop())
        action = Action(self.__dealer_cursor, flip_discard=self.current_discard)
        self.process_action(0.0, action)

    def refresh_deck_if_necessary(self) -> bool:
        if self.deck_size == 0:
            if self.discard_size == 0:
                return False
            action = Action(Game.GAME_PID, shuffle_discards=True)
            self.process_action(0.0, action)
        return True

    def play(self) -> Dict[int, int]:
        self.deal()
        running = True
        cursor = self.__dealer_cursor + 1
        while running:
            print("Table melds:")
            for pid, meld in self.melds.items():
                print("   %d: %s" % (pid, meld))
            for k in range(len(self.__players)):
                print(
                    "Player %d turn [%s]"
                    % (
                        cursor % len(self.__players),
                        self.__players[cursor % len(self.__players)].hand,
                    )
                )
                player = self.__players[cursor % len(self.__players)]
                now = time.time()
                if player.accepts_discard(self.current_discard, self.melds):
                    elapsed = time.time() - now
                    action = Action(player.pid, draw_discard=True)
                    self.process_action(elapsed, action)
                else:
                    for k in range(cursor + 1, cursor + len(self.__players)):
                        player = self.__players[k % len(self.__players)]
                        now = time.time()
                        if player.accepts_purchase(self.current_discard, self.melds):
                            elapsed = time.time() - now
                            action = Action(player.pid, purchase=self.current_discard)
                            self.process_action(elapsed, action)
                            if not self.refresh_deck_if_necessary():
                                return self.tabulate()
                            action = Action(player.pid, draw_deck=True)
                            self.process_action(0.0, action)
                            if not self.refresh_deck_if_necessary():
                                return self.tabulate()
                            action = Action(player.pid, draw_deck=True)
                            self.process_action(0.0, action)
                            break
                        else:
                            elapsed = time.time() - now
                            print(
                                "  - Player %d declines purchase (%.1fus)"
                                % (player.pid, 1000000.0 * elapsed)
                            )
                    if not self.refresh_deck_if_necessary():
                        return self.tabulate()
                    player = self.__players[cursor % len(self.__players)]
                    action = Action(player.pid, draw_deck=True)
                    self.process_action(0.0, action)
                now = time.time()
                move = player.request_move(self.melds)
                elapsed = time.time() - now
                self.process_action(elapsed, Action(player.pid, move=move))
                cursor += 1
                if self.is_over():
                    print("Game over!")
                    running = False
                    break
        return self.tabulate()


class Game:
    # Objective, cards dealt
    TRICKS = (
        (Objective(2, 0), 10),
        (Objective(1, 1), 10),
        (Objective(0, 2), 10),
        (Objective(3, 0), 10),
        (Objective(2, 1), 12),
        (Objective(1, 2), 12),
        (Objective(0, 3), 12),
    )

    PLAYERS_TO_DECKS = {2: 2, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 3}
    GAME_PID = -1

    def __init__(self, num_players: int = 4) -> None:
        self.__dealer_cursor = 0
        self.__players = {k: NaivePlayer(k, super_naive=False) for k in range(num_players)}
        self.__player_scores = {pid: 0 for pid in self.__players}
        self.__trick_stats = {}

    def run(self) -> Dict[int, int]:
        for objective, card_count in self.TRICKS:
            now = time.time()
            for player in self.__players.values():
                player.set_objective(objective)
            print("========== Starting Trick %s ============" % (objective,))
            trick = Trick(objective, card_count, self.__dealer_cursor, self.__players)
            scores = trick.play()
            for pid, score in scores.items():
                self.__player_scores[pid] += score
            print("Current scores:")
            for pid, score in self.__player_scores.items():
                print("  Player %d: %d" % (pid, score))
            self.__dealer_cursor += 1
            self.__dealer_cursor %= len(self.__players)
            self.__trick_stats[objective] = time.time() - now

        for player in self.__players.values():
            # reset objective to report hit rate stats
            player.set_objective(Objective(0, 0))

        print("Gameplay summary:")
        for pid, score in self.__player_scores.items():
            print("   Player %d: %d" % (pid, score))
        print("Timing summary:")
        for objective, elapsed in self.__trick_stats.items():
            print("   Trick %s: %0.2fs" % (objective, elapsed))
        print("Total elapsed: %0.2fs" % sum(self.__trick_stats.values()))
        return self.__player_scores.copy()
