import itertools


def uniq(sorted_iterable):
  last = None
  for comb in sorted_iterable:
    if comb == last:
      #print('Skipping dupe combination: %s' % (comb,))
      continue
    #print('Yielding new combination: %s (last: %s)' % (comb, last))
    yield comb
    last = comb


def sort_uniq(values):
  return uniq(sorted(values))


def unique_combinations(cards, number):
  return uniq(itertools.combinations(cards, number))


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
