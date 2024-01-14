import sys

from liverpool.game import Game
from liverpool.common import Deck
from liverpool.generation import maybe_precompute


def main():
  maybe_precompute()
  if len(sys.argv) > 1:
    print('Seed %s' % sys.argv[1])
    Deck.seed(int(sys.argv[1]))
  g = Game(4)
  _ = g.run()


if __name__ == '__main__':
  main()
