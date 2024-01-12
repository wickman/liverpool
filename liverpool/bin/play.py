import sys

from liverpool.game import Game
from liverpool.common import Deck


def main():
  if len(sys.argv) > 1:
    Deck.seed(sys.argv[1])
  g = Game(4)
  print(g.run())
  

if __name__ == '__main__':
  main()
