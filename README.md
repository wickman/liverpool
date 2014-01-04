A contract rummy implementation in Python.


Right now it just has a basic move generator:

```python
>>> from liverpool.common import Card, Color, Objective
>>> from liverpool.hand import Hand
>>> 
>>> h = Hand()
>>> h.put_card(Card(Color.SPADE, 7))
>>> h.put_card(Card(Color.DIAMOND, 7))
>>> h.put_card(Card(Color.HEART, 7))
>>> h.put_card(Card(Color.HEART, 2))
>>> h.put_card(Card(Color.HEART, 3))
>>> h.put_card(Card(Color.CLUB, 3))
>>> h.put_card(Card.JOKER)
>>> h.put_card(Card(Color.HEART, 4))
>>> h.put_card(Card(Color.HEART, 5))
>>> 
>>> print()

>>> print('Sets:')
Sets:
>>> for set_ in h.iter_sets():
...   print(set_)
... 
?? 3♣ 3♥
?? 7♠ 7♥
?? 7♠ 7♦
?? 7♥ 7♦
7♠ 7♥ 7♦
?? 7♠ 7♥ 7♦
>>> print()

>>> print('Runs:')
Runs:
>>> for run in h.iter_runs():
...   print(run)
... 
2♥ 3♥ 4♥ 5♥
2♥ 3♥ 4♥ 5♥ ??
2♥ 3♥ 4♥ 5♥ ?? 7♥
2♥ 3♥ 4♥ ??
2♥ 3♥ ?? 5♥
2♥ ?? 4♥ 5♥
?? 3♥ 4♥ 5♥
3♥ 4♥ 5♥ ??
3♥ 4♥ 5♥ ?? 7♥
4♥ 5♥ ?? 7♥
>>> objective = Objective(1, 1)
>>> 
>>> print()

>>> print('1/1 Lays:')
1/1 Lays:
>>> for lay in h.iter_lays(objective):
...   print(lay)
... 
Lay(?? 7♠ 7♥    2♥ 3♥ 4♥ 5♥)
Lay(?? 7♠ 7♦    2♥ 3♥ 4♥ 5♥)
Lay(?? 7♥ 7♦    2♥ 3♥ 4♥ 5♥)
Lay(7♠ 7♥ 7♦    2♥ 3♥ 4♥ 5♥)
Lay(7♠ 7♥ 7♦    2♥ 3♥ 4♥ 5♥ ??)
Lay(7♠ 7♥ 7♦    2♥ 3♥ 4♥ ??)
Lay(7♠ 7♥ 7♦    2♥ 3♥ ?? 5♥)
Lay(7♠ 7♥ 7♦    2♥ ?? 4♥ 5♥)
Lay(7♠ 7♥ 7♦    ?? 3♥ 4♥ 5♥)
Lay(7♠ 7♥ 7♦    3♥ 4♥ 5♥ ??)
Lay(?? 7♠ 7♥ 7♦    2♥ 3♥ 4♥ 5♥)
```


There is a sample application, test_deck.py that generates the probabilities
of going out off the deal for various objectives:

```console
mba=liverpool=; pypy test_deck.py
sets/runs/dealt 2/0/10 iters/sets/runs/lays/out: 100000/54437/14345/ 9192/    0
sets/runs/dealt 1/1/10 iters/sets/runs/lays/out: 100000/54549/14237/ 2078/    0
sets/runs/dealt 0/2/10 iters/sets/runs/lays/out: 100000/54863/14387/   85/    0
sets/runs/dealt 3/0/10 iters/sets/runs/lays/out: 100000/54547/14247/  164/    8
sets/runs/dealt 2/1/12 iters/sets/runs/lays/out: 100000/70871/24897/  384/    3
sets/runs/dealt 1/2/12 iters/sets/runs/lays/out: 100000/70967/24792/   15/    1
sets/runs/dealt 0/3/12 iters/sets/runs/lays/out: 100000/71085/24728/    0/    0
```
