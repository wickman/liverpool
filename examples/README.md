This directory primarily contains debugging or benchmarking code.

Debugging examples:
* `hand_overflow.py`: Inspecting a regression in a hand getting too many joker
values (the issue was putting materialized (suited/ranked) jokers in the hand instead of
dematerializing them first.)
* `nondeterministic_meld.py`: Meld's hash was nondeterministic for a while
which broke meld caching in gameplay, causing nondeterministic play when
we expected games to be fully consistent from a given seed.
* `update_explosion.py`: Trying to figure out why the earlier implementation
of iter_updates_multi (i.e.  iterating over all possible ways to play cards
from your hand onto opponents' melds) was performing so poorly.  It was
based off itertools.combinations which exploded combinatorially with high
candidate edits.  Changed to a recursive implementation which is still
tractable even when there are dozens of candidate edits.

Benchmarking examples:
* `simulate_deals.py` Simulate / benchmark deals and melding for standard contract rummy
tricks.
* `microbenchmarks.py` Run a bunch of melding calculations and dump out
statistical profiles of them.  Helped find a few random performance
regressions.