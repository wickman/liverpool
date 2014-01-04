# hand.iter_melds() => Meld(...) => laying down cards.
#
# Table:
#   deck
#   discard
#   players {pid => Player}
#
# Player:
#   hand
#   meld
#
# MeldUpdate:
#   [seq of adds, extends]
#
# Lay:
#   pid
#   meld_update
#
# Add:
#   cards_to_add
#
# Extend:
#   left = [seq]
#   right = [seq]
#
# Move:
#   meld
#   lay  # if meld is None, self.pid cannot be in lays, otherwise it can be.
#   discard
#
#
#
# Generate all moves:
#   if we have not yet melded:
#      generate all melds
#      for each meld:
#        lay the meld down
#        lays = table.iter_valid_lays(self.hand, [all players != us])
#        for each lay:
#          apply lay
#          for each non-playing discard:
#            yield Move(meld, lay, discard)
#          unapply lay
#        unlay meld
#
#   if we have melded:
#     lays = table.iter_valid_lays(self.hand, [all players]) 
#     for each lay:
#       apply lay
#       for each non-playing discard:
#         yield Move(None, lay, discard)
#       unapply lay
#
#
# _is_valid_meld_update_map(map{pid:meld_update}):
#   try:
#     for pid, meld in map.items():
#       table.apply(hand, pid, meld_update)
#     rollback
#     return True
#   except InvalidTake:
#     rollback
#     return False
#
#
# iter_valid_lays(hand, map {pid: meld})
#   lays = {}
#   for pid, meld in map.items():
#      combo_list = []
#      _iter_valid_lays(hand, meld.combos, [], combo_list)
#      lays[pid] = combo_list
#   for combination in itertools.product(lays combinations):
#      if _is_valid_meld_update_map(combination):
#        yield combination
#   
#
# _iter_valid_lays(hand, combos, combo_stack, combo_list)
#   if not combos:
#     combo_list.append(combo_stack[:])
#   combo = combos[0]
#   if combo is set:
#     for add in generate_all_adds(combo, hand) + no-op:
#       combo_stack.append(add)
#       hand.take_add(add)
#       iter_valid_lays(hand, combos[1:], combo_stack, combo_list)
#       hand.put_add(add)
#   if combo is run:
#     for extend in generate_all_extends(combo, hand) + no-op:
#       combo_stack.append(extend)
#       hand.take_extend(extend)
#       iter_valid_lays(hand, combos[1:], combo_stack, combo_list)
#       hand.put_extend(extend)
