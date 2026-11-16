# tiny-chess

A chess engine in at most 4,096 bytes of Python (an lzma-packed entry;
the readable source is submitted with the entry). Negamax alpha-beta
search with quiescence, a transposition table, MVV-LVA / killer /
history move ordering, null-move pruning and late-move reductions,
under a fixed node budget — no clock, no randomness, fully
deterministic. Built for the make.fun tiny-chess-01 bounty.
