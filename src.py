# tiny-chess-01: compact Python chess engine (stdlib only).
# Negamax alpha-beta; 60000-node cap; 8 s hard gate.
# Deterministic, no randomness.

import json
import os
import sys
import urllib.request

A1, H1, A8, H8 = 21, 28, 91, 98
_B = (-11, -9, 9, 11)
_R = (-10, -1, 1, 10)
DIRS = {"N": (-21, -19, -12, -8, 8, 12, 19, 21), "B": _B, "R": _R,
  "Q": _B + _R, "K": _B + _R}
VAL = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 975, "K": 0}

PST = {
 "P": (
0,0,0,0,0,0,0,0,
5,10,10,-20,-20,10,10,5,
5,-5,-10,0,0,-10,-5,5,
0,0,0,20,20,0,0,0,
5,5,10,25,25,10,5,5,
10,10,20,30,30,20,10,10,
50,50,50,50,50,50,50,50,
0,0,0,0,0,0,0,0,
 ),
 "N": (
-50,-40,-30,-30,-30,-30,-40,-50,
-40,-20,0,5,5,0,-20,-40,
-30,5,10,15,15,10,5,-30,
-30,0,15,20,20,15,0,-30,
-30,5,15,20,20,15,5,-30,
-30,0,10,15,15,10,0,-30,
-40,-20,0,0,0,0,-20,-40,
-50,-40,-30,-30,-30,-30,-40,-50,
 ),
 "B": (
-20,-10,-10,-10,-10,-10,-10,-20,
-10,5,0,0,0,0,5,-10,
-10,10,10,10,10,10,10,-10,
-10,0,10,10,10,10,0,-10,
-10,5,5,10,10,5,5,-10,
-10,0,5,10,10,5,0,-10,
-10,0,0,0,0,0,0,-10,
-20,-10,-10,-10,-10,-10,-10,-20,
 ),
 "R": (
0,0,0,5,5,0,0,0,
-5,0,0,0,0,0,0,-5,
-5,0,0,0,0,0,0,-5,
-5,0,0,0,0,0,0,-5,
-5,0,0,0,0,0,0,-5,
-5,0,0,0,0,0,0,-5,
5,10,10,10,10,10,10,5,
0,0,0,0,0,0,0,0,
 ),
 "Q": (0,) * 64,
 "K": (
20,30,10,0,0,10,30,20,
20,20,0,0,0,0,20,20,
-10,-20,-20,-20,-20,-20,-20,-10,
-20,-30,-30,-40,-40,-30,-30,-20,
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
20,30,10,0,0,10,30,20,
 ),
}


def sq_name(i):
 return "abcdefgh"[i % 10 - 1] + str(i // 10 - 1)


def parse_sq(s):
 return (int(s[1]) + 1) * 10 + (ord(s[0]) - 96)


class Pos:
 __slots__ = ("b", "white", "castling", "ep", "kp", "score")

 def __init__(self, b, white, castling, ep):
  self.b = b                # list of 120 chars
  self.white = white        # side to move is white
  self.castling = castling  # bitmask: 1 WK, 2 WQ, 4 BK, 8 BQ
  self.ep = ep              # en passant target square or 0
  self.kp = (b.index("K"), b.index("k"))
  self.score = self.evaluate()

 def evaluate(self):
  b = self.b
  s = 0
  bishops = [0, 0]
  for i in range(21, 99):
   p = b[i]
   if p == "." or p == " ":
    continue
   u = p.upper()
   wi = (9 - i // 10) * 8 + i % 10 - 1  # PST index for a white piece
   if p.isupper():
    s += VAL[u] + PST[u][wi]
    if u == "B":
     bishops[0] += 1
   else:
    s -= VAL[u] + PST[u][63 - wi]
    if u == "B":
     bishops[1] += 1
  if bishops[0] > 1:
   s += 30
  if bishops[1] > 1:
   s -= 30
  return s if self.white else -s

 def gen(self, captures_only=False):
  b = self.b
  white = self.white
  moves = []
  for i in range(21, 99):
   p = b[i]
   if p == "." or p == " " or p.isupper() != white:
    continue
   u = p.upper()
   if u == "P":
    d = 10 if white else -10
    j = i + d
    if not captures_only and b[j] == ".":
     if (j > 90) if white else (j < 30):
      for pr in "qrbn":
       moves.append((i, j, pr))
     else:
      moves.append((i, j, ""))
      if (i // 10 == 3) if white else (i // 10 == 8):
       if b[i + 2 * d] == ".":
        moves.append((i, i + 2 * d, ""))
    for dj in (-1, 1):
     j = i + d + dj
     t = b[j]
     if t != " " and t != "." and t.isupper() != white or j == self.ep:
      if (j > 90) if white else (j < 30):
       for pr in "qrbn":
        moves.append((i, j, pr))
      else:
       moves.append((i, j, ""))
    continue
   for d in DIRS[u]:
    j = i
    while True:
     j += d
     t = b[j]
     if t == " ":
      break
     if t == ".":
      if not captures_only:
       moves.append((i, j, ""))
     else:
      if t.isupper() != white:
       moves.append((i, j, ""))
      break
     if u in "NK":
      break
  if not captures_only:
   moves += self._castling()
  return moves

 def _castling(self):
  b = self.b
  out = []
  if self.white:
   if self.castling & 1 and b[26] == b[27] == "." and b[25] == "K" and b[28] == "R":
    if not self.attacked(25, False) and not self.attacked(26, False) and not self.attacked(27, False):
     out.append((25, 27, ""))
   if self.castling & 2 and b[24] == b[23] == b[22] == "." and b[25] == "K" and b[21] == "R":
    if not self.attacked(25, False) and not self.attacked(24, False) and not self.attacked(23, False):
     out.append((25, 23, ""))
  else:
   if self.castling & 4 and b[96] == b[97] == "." and b[95] == "k" and b[98] == "r":
    if not self.attacked(95, True) and not self.attacked(96, True) and not self.attacked(97, True):
     out.append((95, 97, ""))
   if self.castling & 8 and b[94] == b[93] == b[92] == "." and b[95] == "k" and b[91] == "r":
    if not self.attacked(95, True) and not self.attacked(94, True) and not self.attacked(93, True):
     out.append((95, 93, ""))
  return out

 def attacked(self, sq, by_white):
  b = self.b
  d = -10 if by_white else 10
  for dj in (-1, 1):
   t = b[sq + d + dj]
   if t == ("P" if by_white else "p"):
    return True
  for u, ds in (("N", DIRS["N"]), ("K", DIRS["K"])):
   for d in ds:
    if b[sq + d] == (u if by_white else u.lower()):
     return True
  for ds, us in ((DIRS["B"], "BQ"), (DIRS["R"], "RQ")):
   for d in ds:
    j = sq
    while True:
     j += d
     t = b[j]
     if t == " ":
      break
     if t != ".":
      if t.isupper() == by_white and t.upper() in us:
       return True
      break
  return False

 def in_check(self):
  return self.attacked(self.kp[0] if self.white else self.kp[1], not self.white)

 def move(self, m):
  i, j, pr = m
  b = self.b[:]
  p = b[i]
  white = self.white
  cap = b[j]
  b[i] = "."
  if p.upper() == "P" and j == self.ep and cap == "." and i % 10 != j % 10:
   b[j - 10 if white else j + 10] = "."
  if pr:
   b[j] = pr.upper() if white else pr
  else:
   b[j] = p
  if p.upper() == "K" and abs(j - i) == 2:
   if j > i:
    b[j - 1] = b[j + 1]
    b[j + 1] = "."
   else:
    b[j + 1] = b[j - 2]
    b[j - 2] = "."
  c = self.castling
  if p == "K":
   c &= ~3
  elif p == "k":
   c &= ~12
  if i == 28 or j == 28:
   c &= ~1
  if i == 21 or j == 21:
   c &= ~2
  if i == 98 or j == 98:
   c &= ~4
  if i == 91 or j == 91:
   c &= ~8
  ep = i + (j - i) // 2 if p.upper() == "P" and abs(j - i) == 20 else 0
  return Pos(b, not white, c, ep)

 def key(self):
  return ("".join(self.b), self.white, self.castling, self.ep)


def parse_fen(fen):
 parts = fen.split()
 b = [" "] * 120
 for i in range(21, 99):
  if 1 <= i % 10 <= 8:
   b[i] = "."
 rows = parts[0].split("/")
 for ri, row in enumerate(rows):
  f = 0
  for ch in row:
   if ch.isdigit():
    f += int(ch)
   else:
    b[(9 - ri) * 10 + f + 1] = ch
    f += 1
 castling = 0
 for ch, bit in (("K", 1), ("Q", 2), ("k", 4), ("q", 8)):
  if ch in parts[2]:
   castling |= bit
 ep = parse_sq(parts[3]) if parts[3] != "-" else 0
 return Pos(b, parts[1] == "w", castling, ep)


def move_to_uci(pos, m):
 i, j, pr = m
 return sq_name(i) + sq_name(j) + pr


def uci_to_move(pos, u):
 i, j = parse_sq(u[:2]), parse_sq(u[2:4])
 pr = u[4] if len(u) > 4 else ""
 for m in pos.gen():
  if m == (i, j, pr):
   return m
 return (i, j, pr)


MATE = 100000
INF = 10 ** 9
NODE_CAP = 60000


class Searcher:
 def __init__(self):
  self.tt = {}
  self.nodes = 0
  self.stop = 0
  self.killers = [[None, None] for _ in range(128)]
  self.history = {}
  self.hist_keys = set()

 def order(self, pos, moves, tt_move, ply):
  b = pos.b
  kill = self.killers[ply] if ply < 128 else (None, None)

  def rank(m):
   if m == tt_move:
    return 1 << 30
   i, j, pr = m
   t = b[j]
   if t != "." or pr:
    v = VAL[t.upper()] if t != "." else 100
    return (1 << 24) + v * 32 - VAL[b[i].upper()] // 32 + (VAL[pr.upper()] if pr else 0)
   if m == kill[0]:
    return 1 << 22
   if m == kill[1]:
    return (1 << 22) - 1
   return self.history.get((pos.white, m), 0)

  moves.sort(key=rank, reverse=True)
  return moves

 def qsearch(self, pos, alpha, beta, ply):
  self.nodes += 1
  if self.nodes & 1023 == 0 and os.times()[4] > self.stop:
   self.nodes = NODE_CAP
  if pos.in_check():
   moves = pos.gen()
   self.order(pos, moves, None, ply)
   legal = 0
   for m in moves:
    child = pos.move(m)
    if child.attacked(child.kp[0] if pos.white else child.kp[1], child.white):
     continue
    legal += 1
    s = -self.qsearch(child, -beta, -alpha, ply + 1)
    if s >= beta:
     return beta
    if s > alpha:
     alpha = s
    if self.nodes >= NODE_CAP:
     break
   return alpha if legal else -MATE + ply
  stand = pos.score
  if stand >= beta:
   return beta
  if stand > alpha:
   alpha = stand
  moves = [m for m in pos.gen(True) if pos.b[m[1]] != "." or m[2]]
  self.order(pos, moves, None, ply)
  for m in moves:
   child = pos.move(m)
   if child.attacked(child.kp[0] if pos.white else child.kp[1], child.white):
    continue
   s = -self.qsearch(child, -beta, -alpha, ply + 1)
   if s >= beta:
    return beta
   if s > alpha:
    alpha = s
   if self.nodes >= NODE_CAP:
    break
  return alpha

 def search(self, pos, depth, alpha, beta, ply):
  if self.nodes >= NODE_CAP:
   return pos.score if ply else 0
  if ply > 0:
   if pos.key() in self.hist_keys:
    return 0
   if depth <= 0:
    return self.qsearch(pos, alpha, beta, ply)
  self.nodes += 1
  if self.nodes & 1023 == 0 and os.times()[4] > self.stop:
   self.nodes = NODE_CAP
  key = pos.key()
  ent = self.tt.get(key)
  tt_move = None
  if ent:
   ed, ef, es, tt_move = ent
   if ply > 0 and ed >= depth:
    if ef == 0:
     return es
    if ef == 1:
     alpha = max(alpha, es)
    else:
     beta = min(beta, es)
    if alpha >= beta:
     return es
  check = pos.in_check()
  if depth >= 3 and not check and beta < MATE - 1000 and pos.score >= beta:
   if any(p.upper() in "QRBN" and p.isupper() == pos.white for p in pos.b):
    null = Pos(pos.b[:], not pos.white, pos.castling, 0)
    null.score = -pos.score
    s = -self.search(null, depth - 3, -beta, -beta + 1, ply + 1)
    if s >= beta:
     return beta
  moves = self.order(pos, pos.gen(), tt_move, ply)
  best = -INF
  best_move = None
  flag = 2
  idx = -1
  for m in moves:
   child = pos.move(m)
   if child.attacked(child.kp[0] if pos.white else child.kp[1], child.white):
    continue
   idx += 1
   red = 0
   if depth >= 3 and idx >= 4 and not check and pos.b[m[1]] == "." and not m[2] and not child.in_check():
    red = 1
   if idx == 0:
    s = -self.search(child, depth - 1 - red, -beta, -alpha, ply + 1)
   else:
    s = -self.search(child, depth - 1 - red, -alpha - 1, -alpha, ply + 1)
    if s > alpha and (red or s < beta):
     s = -self.search(child, depth - 1, -beta, -alpha, ply + 1)
   if self.nodes >= NODE_CAP and ply > 0:
    return alpha
   if s > best:
    best = s
    best_move = m
   if s > alpha:
    alpha = s
    flag = 0
   if alpha >= beta:
    flag = 1
    if pos.b[m[1]] == "." and not m[2]:
     k = self.killers[ply]
     if k[0] != m:
      k[1] = k[0]
      k[0] = m
     hk = (pos.white, m)
     self.history[hk] = self.history.get(hk, 0) + depth * depth
    break
  if best_move is None:
   return -MATE + ply if check else 0
  self.tt[key] = (depth, flag, best, best_move)
  return best

 def best_move(self, pos, hist_keys):
  self.nodes = 0
  self.stop = os.times()[4] + 8.0
  self.hist_keys = hist_keys
  moves = pos.gen()
  if len(moves) == 1:
   return moves[0]
  best = moves[0]
  depth = 1
  while self.nodes < NODE_CAP:
   ent = self.tt.get(pos.key())
   tt_move = ent[3] if ent else None
   ordered = self.order(pos, moves[:], tt_move, 0)
   alpha = -INF
   cur = best
   first = True
   for m in ordered:
    child = pos.move(m)
    if child.attacked(child.kp[0] if pos.white else child.kp[1], child.white):
     continue
    if first:
     first = False
     s = -self.search(child, depth - 1, -INF, -alpha, 1)
    else:
     s = -self.search(child, depth - 1, -alpha - 1, -alpha, 1)
     if s > alpha:
      s = -self.search(child, depth - 1, -INF, -alpha, 1)
    if s > alpha:
     alpha = s
     cur = m
    if self.nodes >= NODE_CAP:
     break
   if self.nodes < NODE_CAP:
    best = cur
   depth += 1
   if depth > 64:
    break
  return best


ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")


def post(path, body):
 req = urllib.request.Request(
  ENV_URL + path,
  data=json.dumps(body).encode(),
  headers={"content-type": "application/json"},
 )
 with urllib.request.urlopen(req) as res:
  return json.load(res)


def play():
 searcher = Searcher()
 while True:
  g = post("/game", {})
  if g["status"] == "done":
   print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)
   return
  # replay to current position, tracking keys for draws
  pos = parse_fen(g["start_fen"])
  hist = {pos.key()}
  for u in g["moves"]:
   pos = pos.move(uci_to_move(pos, u))
   hist.add(pos.key())
  while g["status"] == "your_move":
   pos = parse_fen(g["fen"])
   m = searcher.best_move(pos, hist)
   u = move_to_uci(pos, m)
   if u not in g["legal_moves"]:  # never send an illegal move
    u = g["legal_moves"][0]
    m = uci_to_move(pos, u)
   pos = pos.move(m)
   hist.add(pos.key())
   g = post("/move", {"game": g["game"], "move": u})
  print(f"game {g['game']}: {g['outcome']} by {g['reason']}", file=sys.stderr)


if __name__ == "__main__":
 play()
