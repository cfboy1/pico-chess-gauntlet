"""tiny-chess-01 entry source, packed by the kit's compress command into main.py.

120-square mailbox engine: negamax alpha-beta with a fixed node budget per
move (never a clock), quiescence, killer moves, MVV-LVA ordering and an
incremental piece-square evaluation. The env drives play: POST /game,
POST /move, POST /resign. Every choice derives from the position and move
history only, so a trial replays byte for byte.
"""

import json
import os
import sys
import urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or "http://localhost:8080"

OFF = 7
WP, WN, WB, WR, WQ, WK = 1, 2, 3, 4, 5, 6
MATERIAL = (0, 100, 320, 330, 500, 900, 0)

KNIGHT_D = (-21, -19, -12, -8, 8, 12, 19, 21)
KING_D = (-11, -10, -9, -1, 1, 9, 10, 11)
BISHOP_D = (-11, -9, 9, 11)
ROOK_D = (-10, -1, 1, 10)
A1, H1, A8, H8 = 21, 28, 91, 98

PIECE_CHAR = {"P": WP, "N": WN, "B": WB, "R": WR, "Q": WQ, "K": WK,
              "p": -WP, "n": -WN, "b": -WB, "r": -WR, "q": -WQ, "k": -WK}

MATE = 100000

# PeSTO midgame tables, white's view, first row of each = rank 8 (a8..h8).
PAWN = (
      0,   0,   0,   0,   0,   0,   0,   0,
     98, 134,  61,  95,  68, 126,  34, -11,
     -6,   7,  26,  31,  65,  56,  25, -20,
    -14,  13,  22,  24,  12,  23,   9, -17,
    -13,   0,   7,   6,   1,  33,   4,  -7,
    -36, -12, -14,  -4,  -8, -17,  -3, -35,
     -6,  10,  14,  15,  10,  12,  15,  -8,
      0,   0,   0,   0,   0,   0,   0,   0)
KNIGHT = (
   -167, -89, -34, -49,  61, -97, -15,-107,
    -73, -41,  72,  36,  23,  62,   7, -17,
    -47,  60,  37,  65,  84, 129,  73,  44,
     -9,  17,  83, 134, 151, 118,  69,  16,
    -10,  24,  38,  82, 132, 134,  62,   6,
    -36,   5,  16,  27,  18,  -4, -34, -41,
    -60, -17,  14, -16, -20,  -6, -51, -48,
   -200, -88, -65, -32, -23, -34, -84,-184)
BISHOP = (
    -29,   4,-123, -69, -93, -91,   4, -75,
    -16,  -3,  32,  24,  16,  37,  10, -11,
     -6,   5,  27,  41,  57,  45,  21,  -5,
    -14,  12,  42,  53,  64,  60,  29, -13,
     -7,   8,  32,  55,  64,  53,  25,  -8,
     -6,   6,  19,  34,  27,  15,   1, -13,
     -9,  -5,   2,  15,   7,  -4, -11, -15,
    -14, -21,-111, -40,-121, -61, -27, -25)
ROOK = (
     32,  42,  32,  39,  41,  29,  28,  29,
     -4,  -5,  -3,  -4,  -5,  -5,  -5,  -5,
    -11,  -5,  -4,  -1,   5,  -5,  -7,  -6,
     -5,  -5,  -5,   4,   3,  -6,  -6,  -5,
    -12,  -5,  -5,  -3,  -3,  -5,  -5,  -8,
    -13,  -8,  -6,  -3,  -5,  -7,  -7,  -9,
     -6,   5,  10,  14,  14,  10,   3,  -7,
     28,  34,  36,  36,  38,  37,  36,  25)
QUEEN = (
    -10,  -8,  -6,   2,   2,  -2,  -9, -14,
      3,   5,   2,   1,   0,   4,   8,   1,
      0,   0,   1,   0,   4,   3,   3,   4,
     -4,   0,   4,   7,   9,   6,   0,  -2,
    -11,  -1,   1,   8,  10,   1,  -3, -11,
    -15,   4,  -1,  -3,  -1,  -4,   6,   3,
    -13, -14,  -9,  -3,  -1, -12, -17, -19,
     -8, -11,  -8,  -8,  -8,  -8, -11, -13)
KING = (
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -41, -34, -19,  -1,
     -5,   5,  22,  18,   3,  -3,  13, -10,
    -43, -44, -26, -30, -42, -43, -42, -34)
TABS = (PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING)

# PST_W[p][sq120]: contribution of a white piece p (1..6) on 120-square sq.
PST_W = [None] * 7
PST_B = [None] * 7
for _p in range(1, 7):
    _w = [0] * 120
    _b = [0] * 120
    for _f in range(8):
        for _r in range(8):
            _s = 21 + _f + 10 * _r
            _w[_s] = TABS[_p - 1][(7 - _r) * 8 + _f]
            _b[_s] = -TABS[_p - 1][_r * 8 + _f]
    PST_W[_p] = _w
    PST_B[_p] = _b


def contrib(p, sq):
    if p > 0:
        return MATERIAL[p] + PST_W[p][sq]
    return -MATERIAL[-p] + PST_B[-p][sq]


def name_sq(name):
    return 21 + "abcdefgh".index(name[0]) + 10 * (int(name[1]) - 1)


def sq_name(sq):
    return "abcdefgh"[sq % 10 - 1] + str(sq // 10 - 1)


class Position:
    __slots__ = ("b", "white", "castle", "ep", "kw", "kb", "score",
                 "halfmove", "hist")

    def __init__(self, fen):
        self.b = [OFF] * 120
        for r in range(8):
            for f in range(8):
                self.b[21 + f + 10 * r] = 0
        parts = fen.split()
        for ri, row in enumerate(parts[0].split("/")):
            f = 0
            for c in row:
                if c.isdigit():
                    f += int(c)
                else:
                    self.b[21 + f + 10 * (7 - ri)] = PIECE_CHAR[c]
                    f += 1
        self.white = parts[1] == "w"
        c = parts[2]
        self.castle = (("K" in c) << 0) | (("Q" in c) << 1) | (("k" in c) << 2) | (("q" in c) << 3)
        self.ep = name_sq(parts[3]) if parts[3] != "-" else 0
        self.halfmove = int(parts[4])
        self.kw = self.b.index(WK)
        self.kb = self.b.index(-WK)
        s = 0
        for sq in range(21, 99):
            p = self.b[sq]
            if p and p != OFF:
                s += contrib(p, sq)
        self.score = s
        self.hist = []

    def key(self):
        h = 2166136261
        for sq in range(21, 99):
            p = self.b[sq]
            if p and p != OFF:
                h = ((h ^ (p + 40 * sq)) * 16777619) & 0xFFFFFFFF
        return (h ^ (self.castle << 10) ^ ((self.ep or 0) << 4)
                ^ (1 if self.white else 0)) & 0xFFFFFFFF


def attacked(pos, sq, by_white):
    b = pos.b
    if by_white:
        if b[sq - 9] == WP or b[sq - 11] == WP:
            return True
        for d in KNIGHT_D:
            if b[sq + d] == WN:
                return True
        for d in KING_D:
            if b[sq + d] == WK:
                return True
        for d in BISHOP_D:
            t = sq + d
            while b[t] == 0:
                t += d
            p = b[t]
            if p == WB or p == WQ:
                return True
        for d in ROOK_D:
            t = sq + d
            while b[t] == 0:
                t += d
            p = b[t]
            if p == WR or p == WQ:
                return True
    else:
        if b[sq + 9] == -WP or b[sq + 11] == -WP:
            return True
        for d in KNIGHT_D:
            if b[sq + d] == -WN:
                return True
        for d in KING_D:
            if b[sq + d] == -WK:
                return True
        for d in BISHOP_D:
            t = sq + d
            while b[t] == 0:
                t += d
            p = b[t]
            if p == -WB or p == -WQ:
                return True
        for d in ROOK_D:
            t = sq + d
            while b[t] == 0:
                t += d
            p = b[t]
            if p == -WR or p == -WQ:
                return True
    return False


# move = (frm, to, flag); flag: 0 normal, 1 double push, 2 en passant,
# 3..6 promote to N,B,R,Q, 7 O-O, 8 O-O-O. White flag 7 moves rook H1->f1 etc.

def gen_moves(pos, caps_only=False):
    b = pos.b
    white = pos.white
    moves = []
    add = moves.append
    if white:
        own_lo, own_hi = 1, 6
    else:
        own_lo, own_hi = -6, -1
    for frm in ALL_SQ:
        p = b[frm]
        if p == 0 or p == OFF or not (own_lo <= p <= own_hi):
            continue
        ap = p if p > 0 else -p
        if ap == WP:
            fwd = 10 if white else -10
            start = (31 <= frm <= 38) if white else (81 <= frm <= 88)
            t = frm + fwd
            if b[t] == 0:
                if t >= 91 or t <= 28:
                    if not caps_only:
                        add((frm, t, 6)); add((frm, t, 5))
                else:
                    if not caps_only:
                        add((frm, t, 0))
                if not caps_only and start and b[t + fwd] == 0:
                    add((frm, t + fwd, 1))
            for d in (fwd - 1, fwd + 1):
                t = frm + d
                q = b[t]
                if q != OFF and ((q < 0) if white else (q > 0)):
                    if t >= 91 or t <= 28:
                        add((frm, t, 6)); add((frm, t, 5))
                    else:
                        add((frm, t, 0))
                elif t == pos.ep and q == 0:
                    add((frm, t, 2))
        elif ap == WN:
            for d in KNIGHT_D:
                t = frm + d
                q = b[t]
                if q == 0:
                    if not caps_only:
                        add((frm, t, 0))
                elif q != OFF and ((q < 0) == white):
                    add((frm, t, 0))
        elif ap == WK:
            for d in KING_D:
                t = frm + d
                q = b[t]
                if q == 0:
                    if not caps_only:
                        add((frm, t, 0))
                elif q != OFF and ((q < 0) == white):
                    add((frm, t, 0))
            if not caps_only:
                if white and frm == 25:
                    if pos.castle & 1 and b[26] == 0 and b[27] == 0 and b[28] == WR \
                       and not attacked(pos, 25, False) and not attacked(pos, 26, False) \
                       and not attacked(pos, 27, False):
                        add((frm, 27, 7))
                    if pos.castle & 2 and b[24] == 0 and b[23] == 0 and b[22] == 0 \
                       and b[21] == WR and not attacked(pos, 25, False) \
                       and not attacked(pos, 24, False) and not attacked(pos, 23, False):
                        add((frm, 23, 8))
                elif not white and frm == 95:
                    if pos.castle & 4 and b[96] == 0 and b[97] == 0 and b[98] == -WR \
                       and not attacked(pos, 95, True) and not attacked(pos, 96, True) \
                       and not attacked(pos, 97, True):
                        add((frm, 97, 7))
                    if pos.castle & 8 and b[94] == 0 and b[93] == 0 and b[92] == 0 \
                       and b[91] == -WR and not attacked(pos, 95, True) \
                       and not attacked(pos, 94, True) and not attacked(pos, 93, True):
                        add((frm, 93, 8))
        else:
            dirs = BISHOP_D if ap == WB else ROOK_D if ap == WR else KING_D
            for d in dirs:
                t = frm + d
                while True:
                    q = b[t]
                    if q == 0:
                        if not caps_only:
                            add((frm, t, 0))
                    elif q != OFF and ((q < 0) == white):
                        add((frm, t, 0))
                        break
                    else:
                        break
                    t += d
    return moves


ALL_SQ = [21 + f + 10 * r for r in range(8) for f in range(8)]


def make(pos, m):
    frm, to, flag = m
    b = pos.b
    white = pos.white
    p = b[frm]
    cap = b[to]
    csq = cp = 0
    if flag == 2:
        csq = to - 10 if white else to + 10
        cp = b[csq]
    undo_c, undo_ep, undo_hm = pos.castle, pos.ep, pos.halfmove
    d = 0
    if cp:
        d -= contrib(cp, csq)
    elif cap:
        d -= contrib(cap, to)
    d -= contrib(p, frm)
    np = p
    if 3 <= flag <= 6:
        np = (flag - 1) if white else -(flag - 1)
    d += contrib(np, to)
    if flag == 7:
        if white:
            d -= contrib(WR, 28); d += contrib(WR, 26)
        else:
            d -= contrib(-WR, 98); d += contrib(-WR, 96)
    elif flag == 8:
        if white:
            d -= contrib(WR, 21); d += contrib(WR, 24)
        else:
            d -= contrib(-WR, 91); d += contrib(-WR, 94)
    b[frm] = 0
    b[to] = np
    if cp:
        b[csq] = 0
    elif cap:
        pass
    if flag == 7:
        if white:
            b[28] = 0; b[26] = WR
        else:
            b[98] = 0; b[96] = -WR
    elif flag == 8:
        if white:
            b[21] = 0; b[24] = WR
        else:
            b[91] = 0; b[94] = -WR
    pos.ep = (frm + to) >> 1 if flag == 1 else 0
    c = pos.castle
    if p == WK:
        pos.kw = to; c &= ~3
    elif p == -WK:
        pos.kb = to; c &= ~12
    if frm == 21 or to == 21: c &= ~2
    if frm == 28 or to == 28: c &= ~1
    if frm == 91 or to == 91: c &= ~8
    if frm == 98 or to == 98: c &= ~4
    pos.castle = c
    if cap or cp or p == WP or p == -WP:
        pos.halfmove = 0
    else:
        pos.halfmove += 1
    pos.white = not white
    pos.score += d
    pos.hist.append((m, cap, cp, undo_c, undo_ep, undo_hm))


def unmake(pos):
    m, cap, cp, c, ep, hm = pos.hist.pop()
    frm, to, flag = m
    b = pos.b
    pos.white = not pos.white
    white = pos.white
    p = b[to]
    if 3 <= flag <= 6:
        p = WP if white else -WP
    d = 0
    if cp:
        d += contrib(cp, to - 10 if white else to + 10)
    elif cap:
        d += contrib(cap, to)
    d += contrib(p, frm)
    d -= contrib(p, to)
    if flag == 7:
        if white:
            d += contrib(WR, 28); d -= contrib(WR, 26)
        else:
            d += contrib(-WR, 98); d -= contrib(-WR, 96)
    elif flag == 8:
        if white:
            d += contrib(WR, 21); d -= contrib(WR, 24)
        else:
            d += contrib(-WR, 91); d -= contrib(-WR, 94)
    b[frm] = p
    b[to] = cap
    if cp:
        b[to - 10 if white else to + 10] = cp
    if flag == 7:
        if white:
            b[28] = WR; b[26] = 0
        else:
            b[98] = -WR; b[96] = 0
    elif flag == 8:
        if white:
            b[21] = WR; b[24] = 0
        else:
            b[91] = -WR; b[94] = 0
    if p == WK:
        pos.kw = frm
    elif p == -WK:
        pos.kb = frm
    pos.castle = c
    pos.ep = ep
    pos.halfmove = hm
    pos.score += d


def in_check(pos, white):
    return attacked(pos, pos.kw if white else pos.kb, not white)


class Budget(Exception):
    pass


CUR = {"budget": 0, "nodes": 0}


def quiesce(pos, alpha, beta):
    CUR["nodes"] += 1
    if CUR["nodes"] > CUR["budget"]:
        raise Budget
    white = pos.white
    stand = pos.score if white else -pos.score
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    for m in gen_moves(pos, True):
        make(pos, m)
        if in_check(pos, white):
            unmake(pos)
            continue
        s = -quiesce(pos, -beta, -alpha)
        unmake(pos)
        if s >= beta:
            return beta
        if s > alpha:
            alpha = s
    return alpha


def order(pos, moves, killers):
    caps = []
    quiets = []
    b = pos.b
    for m in moves:
        cap = b[m[1]]
        cp = m[2] == 2
        if cap or cp:
            v = 10 * MATERIAL[abs(cap) if cap else WP] - abs(b[m[0]])
            caps.append((-v, m))
        elif m[2] >= 3:
            caps.append((-(5000 + MATERIAL[m[2] - 1]), m))
        else:
            quiets.append((0, m))
    caps.sort(key=lambda t: t[0])
    quiets.sort(key=lambda t: (t[0], t[1]))
    return [m for _, m in caps] + [m for _, m in quiets]


def negamax(pos, depth, alpha, beta, ply):
    CUR["nodes"] += 1
    if CUR["nodes"] > CUR["budget"]:
        raise Budget
    if pos.halfmove >= 100:
        return 0
    white = pos.white
    chk = in_check(pos, white)
    if chk and depth < 24:
        depth += 1
    if depth <= 0:
        return quiesce(pos, alpha, beta)
    best = -2 * MATE
    alpha0 = alpha
    for m in order(pos, gen_moves(pos), ()):
        make(pos, m)
        if in_check(pos, white):
            unmake(pos)
            continue
        s = -negamax(pos, depth - 1, -beta, -alpha, ply + 1)
        unmake(pos)
        if s > best:
            best = s
        if s > alpha:
            alpha = s
        if alpha >= beta:
            break
    if best <= -2 * MATE:
        return (-MATE + ply) if chk else 0
    return best


def to_move(pos, legal):
    """Env UCI strings to (frm, to, flag) tuples, legal on pos."""
    out = []
    b = pos.b
    for u in legal:
        frm = name_sq(u[:2])
        to = name_sq(u[2:4])
        p = abs(b[frm])
        if p == WK and abs(to - frm) == 2:
            flag = 7 if to > frm else 8
        elif p == WP and b[to] == 0 and (to - frm) % 10 != 0:
            flag = 2
        elif len(u) > 4:
            flag = {"n": 3, "b": 4, "r": 5, "q": 6}[u[4]]
        else:
            flag = 0
        out.append((frm, to, flag))
    return out


def root_search(pos, budget, moves_filter):
    CUR["budget"] = budget
    CUR["nodes"] = 0
    white = pos.white
    moves = moves_filter or gen_moves(pos)
    best_m = moves[0]
    try:
        for d in range(1, 32):
            ordered = order(pos, moves, ())
            if best_m in moves and d > 1:
                ordered.remove(best_m)
                ordered.insert(0, best_m)
            cur_best = None
            cur_score = -2 * MATE
            a = -2 * MATE
            for m in ordered:
                make(pos, m)
                if in_check(pos, white):
                    unmake(pos)
                    continue
                s = -negamax(pos, d - 1, -2 * MATE, -a, 1)
                unmake(pos)
                if s > cur_score:
                    cur_score = s
                    cur_best = m
                    if s > a:
                        a = s
            if cur_best is not None:
                best_m = cur_best
            if cur_score >= MATE - 200:
                break
    except Budget:
        pass
    return best_m


# ------------------------------------------------------------- protocol ---

def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path, data=json.dumps(body).encode(),
        headers={"content-type": "application/json"})
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def main():
    game_no = 0
    while True:
        g = post("/game", {})
        if g.get("status") == "done":
            sys.stderr.write(json.dumps({k: g[k] for k in ("games", "wins", "draws", "losses")}) + "\n")
            return
        game_no = g["game"]
        while g.get("status") == "your_move":
            pos = Position(g["fen"])
            legal = g["legal_moves"]
            lmoves = to_move(pos, legal)
            if len(lmoves) == 1:
                m = lmoves[0]
            else:
                m = root_search(pos, 40000, lmoves)
            uci = sq_name(m[0]) + sq_name(m[1]) + {3: "n", 4: "b", 5: "r", 6: "q"}.get(m[2], "")
            if uci not in legal:
                uci = legal[0]
            g = post("/move", {"game": game_no, "move": uci})
            if g.get("status") == "over":
                break


if __name__ == "__main__":
    main()
