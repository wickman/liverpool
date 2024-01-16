import math
from collections import defaultdict
from typing import Dict, Tuple, List, Iterable

from ..common import Deck, Card
from ..game import Listener, Action, Game, Meld


class PlayerView(Listener):
    @classmethod
    def merge(cls, views: Iterable["PlayerView"]) -> Tuple[List[Card], int]:
        known_cards = []
        unknown_cards = 0
        for view in views:
            known_cards.extend(view.known_cards)
            unknown_cards += view.unknown_cards
        return known_cards, unknown_cards

    def __init__(self, pid: int) -> None:
        self.pid = pid
        self.known_cards = []
        self.unknown_cards = 0
        self.meld = None

    def publish_action(self, action: Action, melds: Dict[int, Meld]) -> None:
        if action.init:
            self.known_cards = []
            self.unknown_cards = 0
            self.meld = None
        if self.pid in melds:
            self.meld = melds[self.pid]
        if action.player_id != self.pid:
            return
        if action.move is not None:
            for card in action.move:
                if card in self.known_cards:
                    self.known_cards.remove(card)
                else:
                    self.unknown_cards -= 1
        elif action.purchase is not None:
            self.known_cards.append(action.purchase)
        elif action.draw_discard is not None:
            self.known_cards.append(action.draw_discard)
        elif action.draw_deck:
            self.unknown_cards += 1


class DealerView(Listener):
    def __init__(self) -> None:
        self.deck = None
        self.known_cards = []
        self.discards = []
        self.unknown_cards = 0

    def publish_action(self, action: Action, melds: Dict[int, Meld]) -> None:
        if action.init is not None:
            self.deck = Deck.new(count=Game.PLAYERS_TO_DECKS[action.init.players])
            self.known_cards = []
            self.discards = []
            self.unknown_cards = 0
        if action.move is not None:
            for card in action.move:
                if card in self.known_cards:
                    self.known_cards.remove(card)
                else:
                    self.unknown_cards -= 1
            if action.move.discard:
                self.discards.append(action.move.discard)
        elif action.flip_discard is not None:
            self.discards.append(action.flip_discard)
        elif action.purchase is not None:
            self.known_cards.append(action.purchase)
        elif action.draw_discard is not None:
            self.known_cards.append(action.draw_discard)
            assert self.discards.pop() == action.draw_discard
        elif action.draw_deck:
            self.unknown_cards += 1
        elif action.shuffle_discards:
            self.discards = []


class GameListener(Listener):
    def __init__(self) -> None:
        self.players = {}
        self.dealer = DealerView()
        self.objective = None

    def publish_action(self, action: Action, melds: Dict[int, Meld]) -> None:
        self.dealer.publish_action(action, melds)

        if action.init is not None:
            self.objective = action.init.objective
            self.players = {pid: PlayerView(pid) for pid in range(action.init.players)}

        for player in self.players.values():
            player.publish_action(action, melds)

        self.observe()

    def observe(self):
        pass


class SMECalculator(Listener):
    """Based off simple multiplayer ELO here: http://www.tckerrigan.com/Misc/Multiplayer_Elo/"""

    ELO_SCALE = 400
    K_FACTOR = 32

    def __init__(self, default_elo: int = 1500) -> None:
        self.elos = defaultdict(lambda: default_elo)

    def publish_action(self, action: Action, melds: Dict[int, Meld]) -> None:
        if not action.finalize:
            return

        scores = sorted(action.finalize.scores.items(), key=lambda kv: kv[1])
        # print('elos before: %s' %
        #       ' '.join('%d=%.1f' % (pid, elo) for pid, elo in self.elos.items()))
        # print('scores: %s' %
        #      ' '.join('%d=%d' % (pid, score) for pid, score in scores))

        elo_accumulations = defaultdict(int)

        for (p1, score1), (p2, score2) in zip(scores, scores[1:]):
            p1_elo = self.elos[p1]
            p2_elo = self.elos[p2]

            r1 = math.pow(10, p1_elo / self.ELO_SCALE)
            r2 = math.pow(10, p2_elo / self.ELO_SCALE)
            e1 = r1 / (r1 + r2)
            e2 = r2 / (r1 + r2)
            s1 = 0.5 if score1 == score2 else (1 if score1 < score2 else 0)
            s2 = 0.5 if score2 == score1 else (1 if score2 < score1 else 0)
            new_elo1 = p1_elo + self.K_FACTOR * (s1 - e1)
            new_elo2 = p2_elo + self.K_FACTOR * (s2 - e2)

            # print('%d=%.1f -> %.1f, %d=%.1f -> %.1f' % (
            #    p1, self.elos[p1], new_elo1,
            #    p2, self.elos[p2], new_elo2
            # ))

            elo_accumulations[p1] += new_elo1 - self.elos[p1]
            elo_accumulations[p2] += new_elo2 - self.elos[p2]

        # print('elo accumulations:')
        for pid, acc in elo_accumulations.items():
            # print('  %d += %.1f -> %.1f' % (pid, acc, self.elos[pid] + acc))
            self.elos[pid] += acc

        print(
            "current ELOs: %s" % " ".join("%d=%.1f" % (pid, elo) for pid, elo in self.elos.items())
        )
