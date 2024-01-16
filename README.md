A contract rummy implementation in Python.

```python
>>>> from liverpool.common import Card, Color, Rank, Objective
>>>> from liverpool.hand import Hand
>>>> from liverpool.generation import iter_sets, iter_runs, iter_melds
>>>>
>>>> h = Hand([
....     Card.of(7, Color.SPADE),
....     Card.of(7, Color.DIAMOND),
....     Card.of(7, Color.HEART),
....     Card.of(10, Color.HEART),
....     Card.of(Rank.JACK, Color.HEART),
....     Card.of(Rank.QUEEN, Color.HEART),
....     Card.of(Rank.KING, Color.HEART),
....     Card.of(2, Color.CLUB),
....     Card.of(5, Color.CLUB),
....     Card.joker()
.... ])
>>>> for s in iter_sets(h):
....   print(s)
....
7♤ 7♥ 7♤?
7♤ 7♥ 7♦ 7♤?
7♤ 7♦ 7♤?
7♥ 7♦ 7♤?
7♤ 7♥ 7♦
>>>> for r in iter_runs(h):
....   print(r)
....
9♥? 10♥ J♥ Q♥
9♥? 10♥ J♥ Q♥ K♥
10♥ J♥ Q♥ K♥
10♥ J♥ Q♥ K♥ A♥?
10♥ J♥ Q♥ K♥?
10♥ J♥ Q♥? K♥
10♥ J♥? Q♥ K♥
10♥? J♥ Q♥ K♥
J♥ Q♥ K♥ A♥?
>>>> for m in iter_melds(h, Objective(1, 1)):
....   print(m)
....
Meld(7♤ 7♥ 7♦   10♥ J♥ Q♥ K♥)
Meld(7♤ 7♥ 7♦   10♥ J♥ Q♥ K♥ A♥?)
Meld(7♤ 7♥ 7♦   10♥ J♥ Q♥ K♥?)
Meld(7♤ 7♥ 7♦   10♥ J♥ Q♥? K♥)
Meld(7♤ 7♥ 7♦   10♥ J♥? Q♥ K♥)
Meld(7♤ 7♥ 7♦   J♥ Q♥ K♥ A♥?)
Meld(7♤ 7♥ 7♦ 7♤?   10♥ J♥ Q♥ K♥)
Meld(7♤ 7♥ 7♦   9♥? 10♥ J♥ Q♥)
Meld(7♤ 7♥ 7♦   9♥? 10♥ J♥ Q♥ K♥)
Meld(7♤ 7♥ 7♦   10♥? J♥ Q♥ K♥)
Meld(7♤ 7♥ 7♤?   10♥ J♥ Q♥ K♥)
Meld(7♤ 7♦ 7♤?   10♥ J♥ Q♥ K♥)
Meld(7♥ 7♦ 7♤?   10♥ J♥ Q♥ K♥)
```


There is a sample application, simulate_deals.py that generates the probabilities
of going out off the deal for various objectives:

```console
=; pypy examples/simulate_deals.py
Without LUTS
sets/runs/dealt 2/0/10 iters/sets/runs/melds/out: 100000/54636/14307/ 9259/    0 [60.9us/iter]
sets/runs/dealt 1/1/10 iters/sets/runs/melds/out: 100000/54468/14176/ 2126/    2 [54.1us/iter]
sets/runs/dealt 0/2/10 iters/sets/runs/melds/out: 100000/54604/14262/   80/    1 [62.7us/iter]
sets/runs/dealt 3/0/10 iters/sets/runs/melds/out: 100000/54788/14444/  145/    6 [54.5us/iter]
sets/runs/dealt 2/1/12 iters/sets/runs/melds/out: 100000/70720/24543/  409/    0 [105.4us/iter]
sets/runs/dealt 1/2/12 iters/sets/runs/melds/out: 100000/70666/24786/   16/    0 [107.4us/iter]
sets/runs/dealt 0/3/12 iters/sets/runs/melds/out: 100000/70847/24884/    0/    0 [124.7us/iter]
With LUTS
sets/runs/dealt 2/0/10 iters/sets/runs/melds/out: 1000000/546496/143301/93787/    3 [14.6us/iter]
sets/runs/dealt 1/1/10 iters/sets/runs/melds/out: 1000000/546384/142799/20320/    3 [15.7us/iter]
sets/runs/dealt 0/2/10 iters/sets/runs/melds/out: 1000000/546780/142352/  813/    1 [12.7us/iter]
sets/runs/dealt 3/0/10 iters/sets/runs/melds/out: 1000000/546749/142806/ 1525/   79 [14.0us/iter]
sets/runs/dealt 2/1/12 iters/sets/runs/melds/out: 1000000/708952/248009/ 3924/   18 [23.9us/iter]
sets/runs/dealt 1/2/12 iters/sets/runs/melds/out: 1000000/708430/248576/  170/    8 [22.9us/iter]
sets/runs/dealt 0/3/12 iters/sets/runs/melds/out: 1000000/709170/248412/    1/    1 [16.4us/iter]
```


There are a couple different naive player implementations as well as a basic
game engine and multiplayer ELO calculator.  The cli is not optimized for
readability but you can test basic head-to-head play:

```console
# Play 100 games between a naive but decent player, vs a naive player that
# aggressively buys everything.  The naive but conservative player
# consistently wins.
=; pypy liverpool/bin/play.py -L elo play 100 0=naive 1=aggressive:1 | grep ELOs | tail -1
current ELOs: 0=1804.6 1=1195.4

# Play 100 games between two equally matched naive players, where we expect
# ELO to break even to the average ~1500:
=; pypy liverpool/bin/play.py -L elo play 100 0=naive 1=naive | grep -i ELOs | tail -1
current ELOs: 1=1495.5 0=1504.5
```

The `examples` directory has a few examples for the purposes of benchmarking
and debugging.