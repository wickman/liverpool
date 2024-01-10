import itertools


def uniq(sorted_iterable):
    last = None
    for comb in sorted_iterable:
        if comb == last:
            continue
        yield comb
        last = comb


def sort_uniq(values, **kw):
    return uniq(sorted(values, **kw))


def unique_combinations(cards, number):
    return uniq(itertools.combinations(cards, number))
