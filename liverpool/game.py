from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Optional, List, Dict, Iterable
import time

from .common import Deck, Card, Objective, Meld, MeldUpdate
from .hand import Hand


class Move:
    def __init__(
        self,
        meld: Optional[Meld] = None,
        updates: Optional[Dict[int, MeldUpdate]] = None,
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


"""
Consider a markup language for consuming games and doing statistics.
This could also be a way for agents to consume / participate in games.

# seqno 0
{"pid": 0,     # 0 for game, 1..N for players
 "seq": 0,     # 0
 "objective": {"sets": N, "runs": N} 
 "players": N  # number of players, pids 1..N
 "dealer": 1 } # pid of dealer

# seqno 1
{"pid": 1,
 "seq": 1,
 "action": {
     "type": "draw_deck",
     "receiving_pid": 2,  # receiving pid
 } }

 .....

 # seqno 40
 {"pid": 1,
  "seq": 40,
  "action": {
      "type": "flip_discard",
      "card": {"rank": "KING", "color": "DIAMOND"}
  }

  {"pid": 2,
   "seq": 41,
   "action": {
      "decline": {"rank": "KING", "color": "DIAMOND"}
   }}

   {"pid": 3,
    "seq": 42,
    "action": {
       "purchase": {"rank": "KING", "color": "DIAMOND"}
    }}

   {"pid": 3,
    "seq": 43,
    "action": {
       "draw_deck": true
    }}

    {"pid": 3,
    "seq": 44,
    "action": {
       "draw_deck": true
    }}
 
    {"pid": 2,
    "seq": 45,
    "action": {
       "draw_deck": true
    }}

    {"pid": 2,
    "seq": 46,
    "action": {
        "move": {
            "meld": [
                [{"rank": "KING", "color": "DIAMOND"}],
                [{"rank": "KING", "color": "DIAMOND"}],
                [{"rank": "KING", "color": "DIAMOND"}],
            ],
            "updates": {
                3: {
                    "adds": {
                        0: [{"rank": "KING", "color": "DIAMOND"}],
                        1: [{"rank": "KING", "color": "DIAMOND"}],
                        2: [{"rank": "KING", "color": "DIAMOND"}],
                    },
                    "extends": {
                        0: [{"rank": "KING", "color": "DIAMOND"}],
                        1: [{"rank": "KING", "color": "DIAMOND"}],
                        2: [{"rank": "KING", "color": "DIAMOND"}],
                    },
                }
            },
            "discard": {"rank": "KING", "color": "DIAMOND"},
        }
    }

and so forth.

Then you can build a game from a sequence of actions.  And even do things like
on_action(action) .. { take max of current hands to see who had the biggest hand ever}
or blah blah.  Probably nothing as simple as a query language, but easy enough to
build python functions that do this.

Alternately, rather than JSON, we could do plain text, e.g.

pid:seq:<action>:<params>

0:0 objective:2,3 players:4 dealer:1
0:1 draw_deck:2
0:2 draw_deck:3
0:3 draw_deck:4
0:4 draw_deck:1
...
0:40 flip_discard:Kd
1:41 decline
2:42 purchase
3:43 draw_deck
3:44 draw_deck
2:45 draw_deck
2:46 move meld:KKdKs,89TJs,23?5h updates:1:1:Kd:1:2:3s+9s discard:Ad
3:47 decline
4:48 purchase
4:49 draw_deck
0:50 shuffle_discards
4:51 draw_deck
...


"""


@dataclass
class Trick:
    objective: Objective
    players: int
    dealer: int


@dataclass
class Finalize:
    scores: Dict[int, int]


@dataclass
class Action:
    player_id: int
    init: Optional[Trick] = None
    move: Optional[Move] = None
    purchase: Optional[Card] = None
    decline: Optional[Card] = None
    flip_discard: Optional[Card] = None
    draw_discard: Optional[Card] = None
    draw_deck: bool = False
    shuffle_discards: bool = False
    add_deck: bool = False
    finalize: Optional[Finalize] = None

    """
    @classmethod
    def deserialize(self, s: str) -> "Action":
        pass

    def serialize(self) -> str:
        pass
    """

    def __str__(self):
        if self.init is not None:
            return "Starting trick %d sets / %d runs with %d players and dealer is %d" % (
                self.init.objective.num_sets,
                self.init.objective.num_runs,
                self.init.players,
                self.init.dealer,
            )
        if self.move is not None:
            return "Player %d moves %s" % (self.player_id, self.move)
        if self.purchase is not None:
            return "Player %d purchases %s" % (self.player_id, self.purchase)
        if self.decline is not None:
            return "Player %d declines %s" % (self.player_id, self.decline)
        if self.flip_discard is not None:
            return "Dealer flips %s" % self.flip_discard
        if self.draw_discard is not None:
            return "Player %d draws discard %s" % (self.player_id, self.draw_discard)
        if self.draw_deck:
            return "Player %d draws from deck" % self.player_id
        if self.shuffle_discards:
            return "Dealer shuffles discards"
        if self.add_deck:
            return "Dealer adds a deck"
        if self.finalize is not None:
            return "Final scores: %s" % self.finalize.scores
        return "Unknown action"


class Listener(metaclass=ABCMeta):
    @abstractmethod
    def publish_action(self, action: Action, melds: Dict[int, Meld]) -> None:
        pass


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


class Engine:
    def __init__(
        self,
        objective: Objective,
        card_count: int,
        dealer_pid: int,
        players: Dict[int, Player],
        listeners: Optional[List[Listener]] = None,
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
        self.__listeners = listeners or []
        self.__edits_since_shuffle = self.__melds_since_shuffle = 0

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

    def _process_init(self, action: Action) -> None:
        pass

    def _process_move(self, action: Action) -> None:
        assert action.move is not None
        if action.move.meld:
            self.__melds[action.player_id] = action.move.meld
            self.__melds_since_shuffle += 1
        for pid, update in action.move.updates.items():
            self.__melds[pid] = self.__melds[pid].update(update)
            self.__edits_since_shuffle += 1
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
        self.__edits_since_shuffle = self.__melds_since_shuffle = 0

    def _process_add_deck(self, action: Action) -> None:
        self.__deck = Deck.new(count=1)
        self.__deck.shuffle()

    def _process_finalize(self, action: Action) -> None:
        pass

    def process_action(self, elapsed: float, action: Action) -> None:
        print("  - Processing action: %s (%.1fus)" % (action, 1000000 * elapsed))
        actions = sum(
            [
                action.init is not None,
                action.move is not None,
                action.purchase is not None,
                action.flip_discard is not None,
                action.draw_discard is not None,
                action.shuffle_discards,
                action.draw_deck,
                action.add_deck,
                action.finalize is not None,
            ]
        )
        if actions != 1:
            raise ValueError("Expected one action, got %d" % actions)
        if action.init is not None:
            self._process_init(action)
        elif action.move is not None:
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
        elif action.add_deck:
            self._process_add_deck(action)
        elif action.finalize:
            self._process_finalize(action)
        else:
            raise ValueError("Unknown action %s" % action)
        for player in self.__players.values():
            player.publish_action(action, self.melds)
        for listener in self.__listeners:
            listener.publish_action(action, self.melds)

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
            if self.discard_size > 0:
                if self.__edits_since_shuffle == 0 and self.__melds_since_shuffle == 0:
                    print("Deadlocked")
                    return False
                action = Action(Game.GAME_PID, shuffle_discards=True)
            else:
                action = Action(Game.GAME_PID, add_deck=True)
            self.process_action(0.0, action)
        return True

    def finalize(self):
        scores = self.tabulate()
        self.process_action(0.0, Action(Game.GAME_PID, finalize=Finalize(scores)))
        return scores

    # TODO: need a deadlock detector
    def play(self) -> Dict[int, int]:
        self.process_action(
            0.0,
            Action(
                Game.GAME_PID, init=Trick(self.objective, len(self.__players), self.__dealer_cursor)
            ),
        )
        self.deal()
        running = True
        cursor = self.__dealer_cursor + 1
        edits_since_shuffle = melds_since_shuffle = 0
        while running:
            print("Table melds:")
            for pid, meld in sorted(self.melds.items()):
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
                    action = Action(player.pid, draw_discard=self.current_discard)
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
                                return self.finalize()
                            action = Action(player.pid, draw_deck=True)
                            self.process_action(0.0, action)
                            if not self.refresh_deck_if_necessary():
                                return self.finalize()
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
                        return self.finalize()
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
        return self.finalize()


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

    def __init__(self, players: Dict[int, Player], listeners: Optional[Iterable[Listener]]) -> None:
        self.__dealer_cursor = 0
        self.__players: Dict[int, Player] = players.copy()
        self.__player_scores: Dict[int, int] = {pid: 0 for pid in self.__players}
        self.__trick_stats: Dict[Objective, float] = {}
        self.__listeners = [listener for listener in listeners] if listeners else []

    def run(self) -> Dict[int, int]:
        for objective, card_count in self.TRICKS:
            now = time.time()
            print("========== Starting Trick %s ============" % (objective,))
            trick = Engine(
                objective, card_count, self.__dealer_cursor, self.__players, self.__listeners
            )
            scores = trick.play()
            for pid, score in scores.items():
                self.__player_scores[pid] += score
            print("Current scores:")
            for pid, score in self.__player_scores.items():
                print("  Player %d: %d" % (pid, score))
            self.__dealer_cursor += 1
            self.__dealer_cursor %= len(self.__players)
            self.__trick_stats[objective] = time.time() - now

        print("Gameplay summary:")
        for pid, score in self.__player_scores.items():
            print("   Player %d: %d" % (pid, score))
        print("Timing summary:")
        for objective, elapsed in self.__trick_stats.items():
            print("   Trick %s: %0.2fs" % (objective, elapsed))
        print("Total elapsed: %0.2fs" % sum(self.__trick_stats.values()))
        return self.__player_scores.copy()
