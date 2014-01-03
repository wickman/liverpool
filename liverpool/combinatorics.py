import itertools


def unique_combinations(cards, number):
  last = None
  for comb in itertools.combinations(cards, number):
    if comb == last:
      continue
    yield comb
    last = comb


# part of the standard library as of 3.1.x, sigh.
def combinations_with_replacement(cards, number):
  pool = tuple(cards)
  n = len(pool)
  if not n and number:
    return
  indices = [0] * number
  yield tuple(pool[i] for i in indices)
  while True:
    for i in reversed(range(number)):
      if indices[i] != n - 1:
        break
    else:
      return
    indices[i:] = [indices[i] + 1] * (number - i)
    yield tuple(pool[i] for i in indices)
