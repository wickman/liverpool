from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, List

from .common import Hand, Deck, Card, Objective, Meld
from .generation import (
    iter_melds,
    iter_extends,
    iter_adds,
    Extend,
    Add,
)


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


@dataclass
class Edit:
    pid: int
    add: Optional[Add]
    extend: Optional[Extend]


class Move:
    def __init__(
        self, meld: Optional[Meld], edit: Optional[List[Edit]], discard: Optional[Card]
    ) -> None:
        self.meld = meld
        self.edit = edit or []
        self.discard = discard


@dataclass
class Action:
    player_id: int
    move: Optional[Move] = None
    purchase: Optional[Card] = None
    draw_discard: Optional[Card] = None
    draw_deck: bool = False


class GameState:
    def __init__(self, num_players: int = 4) -> None:
        self.__deck = Deck.new(count=Game.PLAYERS_TO_DECKS[num_players])
        self.__discards = []
        self.__actions: List[Action] = []

    @property
    def last_action(self) -> Optional[Action]:
        return self.__actions[-1] if self.__actions else None


class Player(metaclass=ABC):
    def __init__(self, hand: Hand) -> None:
        self.hand = hand

    def take(self, card: Card) -> None:
        self.hand.put_card(card)

    def discard(self, card: Card) -> None:
        self.hand.take_card(card)

    @abstractmethod
    def publish_action(self, action: Action) -> None:
        pass

    @abstractmethod
    def accepts_discard(self, card: Card) -> bool:
        pass

    @abstractmethod
    def accepts_purchase(self, card: Card) -> bool:
        pass

    @abstractmethod
    def action(self) -> Move:
        pass


class Trick:
    def __init__(
        self, objective: Objective, dealt_cards: int, num_players: int = 4
    ) -> None:
        self.objective = objective
        self.deck = Deck.new(count=Game.PLAYERS_TO_DECKS[num_players])
        self.discards = []
        self.players = [Player(k, num_players) for k in range(num_players)]
        self.cursor = 1  # 0 is the dealer, 1 is the first to play
        self.deal(dealt_cards)

    @property
    def dealer(self):
        return self.players[0]

    @property
    def active_player(self):
        return self.players[self.cursor]

    def deal(self, nr_cards: int) -> None:
        for _ in range(nr_cards):
            for player in self.players:
                player.take(self.deck.pop())
        self.discards.append(self.deck.pop())

    def play(self):
        # step 1: determine if the active player wants the discard
        if self.active_player.accepts_discard(self.discards[-1]):
            self.active_player.take(self.discards.pop())
        else:
            for player in self.players[self.cursor :] + self.players[0 : self.cursor]:
                if player.accepts_purchase(self.discards[-1]):
                    player.take(self.discards.pop())
                    # TODO 1: encode policy as to whether this is one card or two cards
                    # TODO 2: implement error handling for insufficient cards in deck
                    player.take(self.deck.pop())
                    player.take(self.deck.pop())
                    break
            self.active_player.take(self.deck.pop())

        # step 4: active player either discards or melds
        move = self.active_player.action()

        # repeat until active player has no cards
