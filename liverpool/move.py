# hand.iter_melds() => Meld(...) => laying down cards.
#
# Table:
#   deck [deck]
#   discard pile [deck]
#   players {pid => Player}
#
# Player:
#   hand
#   meld
#
# PlayerView
#   known_hand
#   unknown_count
#   meld
#
# N.B.:
#   there can be a player Player{hand,meld}
#   and there can be a player_view PlayerView{known,hidden_count,meld}
#   each player has {pid:player_view}, which can be used for monte carlo
#
# Meld:
#   combos [ordered seq of Sets,Runs]
#
# Add:
#   cards_to_add [possibly empty]
#
# Extend:
#   left = [seq] [possibly empty]
#   right = [seq] [possibly empty]
#
# MeldUpdate:
#   [seq of adds, extends] (that can be zipped over Meld.combos)
#
# Lay:
#   {pid => meld_update}
#
# Move:
#   meld
#   lay      # if meld is None, self.pid cannot be in lays, otherwise it can be.
#   discard
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
#     lays = table.iter_valid_lays(self.hand, [all players, self included])
#     for each lay:
#       apply lay
#       for each non-playing discard:
#         yield Move(None, lay, discard)
#       unapply lay
#
#
# _is_valid_lay(hand, lay):
#   try:
#     for pid, meld_update in lay.items():
#       table.apply(hand, pid, meld_update)
#     rollback
#     return True
#   except InvalidTake:
#     rollback
#     return False
#
# def lays_from_meld_update_map(meld_update_map):
#   to_product = []
#   for pid, meld_update_list in meld_update_map.items():
#     to_product.append([(pid, meld_update) for meld_update in meld_update_list])
#   for tuples in itertools.product(*to_product):
#     yield Lay(dict(tuples))
#
# iter_valid_lays(hand, melds {pid: meld})
#   meld_update_map = {}
#   for pid, meld in melds.items():
#      update_list = []
#      _iter_valid_lays(hand, meld.combos, [], update_list)
#      meld_update_map[pid] = update_list
#   for lay in lays_from_meld_update_map(meld_update_map):
#      if _is_valid_lay(lay):
#        yield lay
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
