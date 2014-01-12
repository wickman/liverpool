from __future__ import print_function, unicode_literals

import array
from collections import defaultdict

from .common import (
    Card,
    fake_unicode,
    Run,
    Set,
    Add,
    Extend,
)


class Hand(object):
  class Error(Exception): pass
  class InvalidCard(Error): pass
  class InvalidTake(Error): pass

  __slots__ = ('cards', 'stack')

  def __init__(self, cards=None):
    self.cards = array.array('B', [0]*(Card.MAX + 1))
    self.stack = [None]   # stack of takes, None represents start of a "transaction"
    for card in cards or []:
      self.put_card(card)
    self.commit()

  @property
  def jokers(self):
    return self.cards[Card.JOKER.value]

  def __iter__(self):
    for card_value, count in enumerate(self.cards):
      for _ in range(count):
        yield Card(card_value)

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

    if self.cards[card.value] <= 0:
      raise self.InvalidTake('You do not have a %s!' % card)

    self.cards[card.value] -= 1
    self.stack.append(card)
    return card

  def put_card(self, card):
    if not isinstance(card, Card):
      raise TypeError('Expected card to be Card, got %s' % type(card))

    self.cards[card.value] += 1

  def put_combo(self, combo):
    for card in combo:
      self.put_card(card)

  def take_combo(self, combo):
    for card in combo:
      self.take_card(card)

  def __unicode__(self):
    return 'Hand(%s)' % ' '.join('%s' % card for card in self)

  def __str__(self):
    return fake_unicode(self)
