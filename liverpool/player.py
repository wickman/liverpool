from .common import (
    Deck,
    Objective,
)


class Game(object):
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


class Trick(object):
    def __init__(self, objective, dealt_cards, num_players=4):
        self.objective = objective
        self.deck = Deck(count=2)
        self.discards = []
        self.players = [Player(k, num_players) for k in range(num_players)]
        self.stack = []
        self.deal(dealt_cards)

    def deal(self, nr_cards):
        for player in self.players:
            for _ in range(nr_cards):
                player.take(self.deck.pop())
                for other_player in self.players:
                    if other_player != player:
                        other_player.apply_take(PlayerTake(player.pid, None, 1))

    def order(self, turn):
        return [self.players[(turn + k) % len(self.players)] for k in range(len(self.players))]

    def negotiate(self, turn):
        takes = []

        first_player = order(self.turn_number)[0]

        if not self.discards:
            first_player.take(self.deck.pop())
            return [PlayerTake(first_player.pid, None, 1)]

        for player in order(self.turn_number):
            if player == first_player:
                if player.wants(self.discards[-1], 0):
                    taken_card = self.discards.pop()
                    player.take(taken_card)
                    return [PlayerTake(player.pid, taken_card, 0)]
            else:
                if player.wants(self.discards[-1], 2):
                    top = self.discards.pop()
                    player.take(top, self.deck.pop(), self.deck.pop())
                    takes.append(PlayerTake(player.pid, top, 2))
                    break

        first_player.take(self.deck.pop())
        takes.append(PlayerTake(first_player.pid, None, 1))
        return takes

    def score_map(self):
        pass

    def play(self):
        turn = 0

        while all(player.live for player in self.players):
            takes = self.negotiate(turn)
            for player in self.players:
                player.apply_takes([take for take in takes if take.pid != player.pid])
            first_player = self.order(turn)[0]
            move = first_player.get_move()
            for player in players:
                player.apply_move(first_player.pid, move)
            turn += 1

        return self.score_map()


class Lay(dict):
    pass


class Move(object):
    def __init__(self, pid, meld=None, lay=None, discard=None):
        self.pid = pid
        self.meld = meld
        self.lay = lay
        self.discard = discard


"""
PlayerView should encapsulate the probability distributions of expected cards from the other player.
For example, when the game starts, the player is dealt N cards.  These come from a known probability distribution
i.e. 2 decks x 54 cards.  We can stochastically generate the sample hands from the probability distribution.
Over time this distribution changes, e.g.:
  player discards card X, so we can change the distribution of unknown cards (e.g. 2 decks x 54 cards - 1)
  player picks up card Y, so we can change the distribution of unknown to known cards

If player picks up card X and discards card X, that doesn't definitely say they don't have card X because it
could be sampled out of the original distribution.  IF player1 discards card Y, this actually reflects the
distribution of other players as well.

So we should have the following:
   * known_cards: set of cards known to be in the player's hand
   * unknown_cards: number of unknown cards -- the distribution is always taken from
        Deck - [your cards] - sum(p.known_cards for p in player_views)
"""


class PlayerView(object):
    def __init__(self, meld=None, visible_cards=None, invisible_cards=0):
        self.meld = meld
        self.visible_cards = visible_cards or []
        self.invisible_cards = invisible_cards

    def apply_take(self, take):
        if take.visible_cards:
            self.visible_cards += take.visible_cards
        self.invisible_cards += take.invisible_cards


class PlayerTake(object):
    def __init__(self, pid, visible_cards=None, invisible_cards=0):
        self.pid = pid
        self.visible_cards = visible_cards or []
        self.invisible_cards = invisible_cards


class Player(object):
    def __init__(self, pid, num_players):
        self.pid = pid
        self.hand = Hand()
        self.unseen_cards = Deck(count=2)
        self.views = dict((pid, PlayerView()) for pid in range(num_players))

    @property
    def live(self):
        return not self.hand.empty

    def take(self, *cards):
        for card in cards:
            self.unseen_cards.take(card)
            self.hand.put_card(card)

    def apply_take(self, player_take):
        self.views[player_take.pid].apply_take(player_take)

    def apply_takes(self, player_takes):
        for take in player_takes:
            self.apply_take(take)

    def apply_move(self, player_move):
        pass

    def wants(self, card, invisible_cards=0):
        pass

    # strategy:
    #   moves = generate all moves
    #   move_map = {}
    #   for move in moves:
    #     outcomes = []
    #     apply move
    #     for _ in range(simulations):
    #       outcomes.append(run_simulation())
    #     move_map[move] = outcomes
    #     unapply move
    #
    #   pick move with highest average [or cull to top 5 and dig deeper]

    def generate_moves_unmelded(self):
        pass

    def generate_moves_melded(self):
        pass

    def generate_moves(self):
        pass

    def get_move(self):
        pass
