from __future__ import print_function, unicode_literals

from collections import defaultdict

from .common import (
    Card,
    fake_unicode,
    Run,
    Set,
)


class Hand(object):
  class Error(Exception): pass
  class InvalidCard(Error): pass
  class InvalidTake(Error): pass

  __slots__ = ('cards', 'jokers', 'stack')

  def __init__(self, cards=None):
    self.cards = defaultdict(int)
    self.jokers = 0
    self.stack = [None]   # stack of takes, None represents start of a "transaction"
    for card in cards or []:
      self.put_card(card)
    self.commit()

  def __iter__(self):
    for card, count in self.cards.items():
      for _ in range(count):
        yield card
    for joker in range(self.jokers):
      yield Card.JOKER

  def commit(self):
    self.stack.append(None)

  def rollback(self):
    while self.stack[-1] is not None:
      self.put_card(self.stack.pop())

  def undo(self):
    assert len(self.stack) > 1
    assert self.stack.pop() is None
    self.rollback()

  def truncate(self):
    self.stack = [None]

  def take_card(self, card):
    if not isinstance(card, Card):
      raise TypeError('Expected card to be Card, got %s' % type(card))

    if card == Card.JOKER or self.cards[card] <= 0:
      if self.jokers == 0:
        raise self.InvalidTake('Not enough jokers to take!')
      self.jokers -= 1
      self.stack.append(Card.JOKER)
      return Card.JOKER

    self.cards[card] -= 1
    self.stack.append(card)
    return card

  def put_card(self, card):
    if not isinstance(card, Card):
      raise TypeError('Expected card to be Card, got %s' % type(card))

    if card == Card.JOKER:  # jokers are wild!
      self.jokers += 1
      return

    self.cards[card] += 1

  def _map_run(self, run, method):
    if not isinstance(run, Run):
      raise TypeError('Expected run to be Run, got %s' % type(run))
    for card in run:
      method(card)

  def _map_set(self, set_, method):
    if not isinstance(set_, Set):
      raise TypeError('Expected set to be Set, got %s' % type(set_))
    for card in set_:
      method(card)

  def put_run(self, run):
    self._map_run(run, self.put_card)

  def put_set(self, set_):
    self._map_set(set_, self.put_card)

  def take_run(self, run):
    self._map_run(run, self.take_card)

  def take_set(self, set_):
    self._map_set(set_, self.take_card)

  def __unicode__(self):
    return 'Hand(%s)' % ' '.join('%s' % card for card in self)

  def __str__(self):
    return fake_unicode(self)
