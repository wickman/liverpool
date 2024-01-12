from array import array
from collections import defaultdict

from typing import List, Optional, Iterable

from .common import (
    Card,
    Deck,
)


class Hand:
    """A hand of cards.

    Mechanically you construct cards from a deck, e.g. h = Hand.from_deck(deck, 10)

    You can then take cards from the hand, e.g. h.take_card(Card.of(Rank.ACE, Suit.SPADES)).
    You can also take combos, e.g. h.take_combo(run) or h.take_combo(set).

    Takes are transacted, so you can rollback or commit them. Puts are not transacted.
    """

    class Error(Exception):
        pass

    class InvalidCard(Error):
        pass

    class InvalidTake(Error):
        pass

    __slots__ = ("cards", "taken")

    @classmethod
    def from_deck(cls, deck: Deck, count: int) -> "Hand":
        cards = []
        with deck:
            try:
                for _ in range(count):
                    cards.append(deck.pop())
            except deck.EmptyDeck:
                raise cls.Error("Insufficient cards in deck")
        return cls(cards)

    def __init__(self, cards: Iterable[Card] = None) -> None:
        self.cards: array[int] = array("B", [0] * (Card.JOKER_VALUE + 1))
        # stack of takes, None represents start of a "transaction"
        self.taken: List[Optional[Card]] = []
        for card in cards or []:
            self.put_card(card)
        self.commit()

    @property
    def jokers(self) -> int:
        return self.cards[Card.JOKER_VALUE]

    @property
    def empty(self) -> bool:
        return sum(self.cards) == 0

    def __hash__(self) -> int:
        return hash(tuple(self.cards))

    def __len__(self) -> int:
        return sum(self.cards)

    def __iter__(self) -> Iterable[Card]:
        for card_value, count in enumerate(self.cards):
            for _ in range(count):
                yield Card(card_value)

    def commit(self):
        self.taken.append(None)

    def rollback(self):
        while self.taken[-1] is not None:
            self.put_card(self.taken.pop())

    def undo(self):
        assert len(self.taken) > 1
        assert self.taken.pop() is None
        self.rollback()

    def truncate(self):
        self.taken = [None]

    def take_card(self, card) -> Card:
        if not isinstance(card, Card):
            raise TypeError("Expected card to be Card, got %s" % type(card))

        try:
          if self.cards[card.value] <= 0:
              raise self.InvalidTake("You do not have a %s!" % card)
        except IndexError:
            print('card.value %d' % card.value)
            raise

        self.cards[card.value] -= 1
        self.taken.append(card)
        return card

    def put_card(self, card):
        if not isinstance(card, Card):
            raise TypeError("Expected card to be Card, got %s" % type(card))

        self.cards[card.value] += 1

    def put_combo(self, combo: Iterable[Card]):
        for card in combo:
            self.put_card(card.dematerialized())

    def take_combo(self, combo: Iterable[Card]):
        for card in combo:
            self.take_card(card.dematerialized())

    def __str__(self):
        return "Hand(%s)" % " ".join("%s" % card for card in self)
