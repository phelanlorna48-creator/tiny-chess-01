# tiny-chess

[![bounty](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/phelanlorna48-creator/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard)
[![reward](https://make.fun/badge/tiny-chess-01/phelanlorna48-creator/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01)

A chess engine in at most 4,096 bytes of Python (an lzma-packed entry;
the readable source is submitted with the entry). Negamax alpha-beta
search with quiescence, a transposition table, MVV-LVA / killer /
history move ordering, null-move pruning and late-move reductions,
under a fixed node budget — no clock, no randomness, fully
deterministic. Built for the make.fun tiny-chess-01 bounty.

Revision note (round 5): the queen now evaluates with a real
piece-square table instead of a flat zero table; everything else is
the locked v4 search (60k-node cap, 8 s wall-clock safety gate).
