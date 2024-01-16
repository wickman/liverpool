import sys

from liverpool.game import Game
from liverpool.common import Deck
from liverpool.generation import maybe_precompute
from liverpool.players import NaivePlayer, AggressiveBuyPlayer
from liverpool.listeners import GameListener, PlayerView, SMECalculator

import click


class PrintingListener(GameListener):
    def observe(self):
        known, unknown = PlayerView.merge(self.players.values())
        print(
            "listener: dealer: known %s / discards %s / unknown %d ;; players: known %s / unknown %d"
            % (
                "".join(map(str, sorted(self.dealer.known_cards))),
                "".join(map(str, self.dealer.discards)),
                self.dealer.unknown_cards,
                "".join(map(str, sorted(known))),
                unknown,
            )
        )
        for pid, player in self.players.items():
            print(
                "  - pid: %d ;; known %s / unknown %d"
                % (pid, "".join(map(str, sorted(player.known_cards))), player.unknown_cards)
            )


def construct_naive(pid, *args):
    if len(args) != 0:
        click.fail("NaivePlayer does not take any arguments")
    return NaivePlayer(pid)


def construct_aggressive(pid, *args):
    if len(args) != 1:
        click.fail(
            "AggressiveBuyPlayer requires exactly one argument: always_buy_if_missing (integer)"
        )
    return AggressiveBuyPlayer(pid, always_buy_if_missing=int(args[0]))


PLAYER_CONVERSIONS = {
    "naive": construct_naive,
    "aggressive": construct_aggressive,
}


class PlayerParam(click.ParamType):
    name = "player"

    def convert(self, value, param, ctx):
        pid, player = value.split("=")
        pid = int(pid)

        try:
            player_type, player_arguments = player.split(":")
        except ValueError:
            player_type, player_arguments = player, []

        if player_type in PLAYER_CONVERSIONS:
            return PLAYER_CONVERSIONS[player_type](pid, *player_arguments)
        else:
            self.fail("%s is not a valid player" % value, param, ctx)


class ListenerParam(click.ParamType):
    name = "listener"

    def convert(self, value, param, ctx):
        try:
            listener_type, listener_arguments = value.split(":")
        except ValueError:
            listener_type, listener_arguments = value, []

        if listener_type == "print":
            return PrintingListener()
        elif listener_type == "elo":
            default_elo = 1500
            if len(listener_arguments) == 1:
                default_elo = int(listener_arguments[0])
            return SMECalculator(default_elo)
        else:
            self.fail("%s is not a valid listener" % value, param, ctx)


@click.group()
@click.option("-s", "--seed", type=int, default=0)
@click.option("-L", "--listener", type=ListenerParam(), multiple=True)
@click.pass_context
def cli(ctx, seed, listener):
    Deck.seed(seed)
    maybe_precompute()
    ctx.ensure_object(dict)
    ctx.obj["listeners"] = listener


@cli.command()
@click.pass_context
@click.argument("games", type=int)
@click.argument("player", type=PlayerParam(), nargs=-1)
def play(ctx, games, player):
    player_dict = {p.pid: p for p in player}

    for _ in range(games):
        g = Game(player_dict, listeners=ctx.obj["listeners"])
        _ = g.run()


if __name__ == "__main__":
    cli()
