"""Single-threaded short-deck Omaha equity calculations.

Only public cards and the acting player's hand enter this module. Numba
compiles the numeric loops at startup, before the match time bank starts.
"""
from itertools import combinations_with_replacement
from pathlib import Path

import numpy as np
from numba import njit

from evaluator import _score_ranks

POW5 = np.array([5 ** (c >> 2) for c in range(36)], dtype=np.int32)
RANK_TABLE = np.zeros(5 ** 9, dtype=np.int32)
for _r in combinations_with_replacement(range(9), 5):
    if max(_r.count(r) for r in _r) <= 4:
        RANK_TABLE[sum(5 ** r for r in _r)] = _score_ranks(tuple(reversed(_r)), False)

_data_path = Path(__file__).with_name('preflop.npz')
if _data_path.exists():
    with np.load(_data_path, allow_pickle=False) as _data:
        PREFLOP_KEYS = _data['keys']
        PREFLOP_EQUITIES = _data['equities']
else:
    PREFLOP_KEYS = np.empty(0, dtype=np.int64)
    PREFLOP_EQUITIES = np.empty(0, dtype=np.float32)


@njit(inline="always")
def canonical_key(hole):
    a = b = c = d = np.int64(0)
    for card in hole:
        bit = np.int64(1) << (card >> 2)
        suit = card & 3
        if suit == 0:
            a |= bit
        elif suit == 1:
            b |= bit
        elif suit == 2:
            c |= bit
        else:
            d |= bit
    if a > b:
        a, b = b, a
    if c > d:
        c, d = d, c
    if a > c:
        a, c = c, a
    if b > d:
        b, d = d, b
    if b > c:
        b, c = c, b
    return a | b << 9 | c << 18 | d << 27


@njit
def preflop_equity(hole):
    key = canonical_key(hole)
    lo = 0
    hi = len(PREFLOP_KEYS)
    while lo < hi:
        mid = (lo + hi) // 2
        if PREFLOP_KEYS[mid] < key:
            lo = mid + 1
        else:
            hi = mid
    idx = lo
    if idx < len(PREFLOP_KEYS) and PREFLOP_KEYS[idx] == key:
        return float(PREFLOP_EQUITIES[idx])
    return -1.0


@njit(inline="always")
def five(a, b, c, d, e):
    v = RANK_TABLE[POW5[a] + POW5[b] + POW5[c] + POW5[d] + POW5[e]]
    if (a & 3) == (b & 3) == (c & 3) == (d & 3) == (e & 3):
        if v >> 20 == 3:
            v += 5 << 20
        else:
            v += 6 << 20
    return v


@njit
def score(hole, board):
    best = 0
    for i in range(4):
        for j in range(i + 1, 5):
            for a in range(len(board) - 2):
                for b in range(a + 1, len(board) - 1):
                    for c in range(b + 1, len(board)):
                        v = five(hole[i], hole[j], board[a], board[b], board[c])
                        if v > best:
                            best = v
    return best


@njit(inline="always")
def next_random(state):
    # Per-half RNG state is passed by the caller, never global or shared.
    state ^= state >> np.uint64(12)
    state ^= state << np.uint64(25)
    state ^= state >> np.uint64(27)
    return state, state * np.uint64(2685821657736338717)


@njit
def preflop_quality(hole):
    """Ordering proxy for a candidate opponent's preflop range."""
    if len(PREFLOP_KEYS):
        return preflop_equity(hole)
    ranks = np.zeros(9, dtype=np.int32)
    suits = np.zeros(4, dtype=np.int32)
    q = 0.0
    for c in hole:
        r = c >> 2
        ranks[r] += 1
        suits[c & 3] += 1
        q += 0.5 * r
    for r in range(9):
        if ranks[r] >= 2:
            q += 1.8 + 0.55 * r
        if ranks[r] >= 3:
            q -= 5.0
        if ranks[r] == 4:
            q -= 9.0
        for s in range(r + 1, 9):
            if ranks[r] and ranks[s]:
                gap = s - r
                if s == 8 and r < 4:
                    gap = min(gap, r + 1)
                if gap <= 3:
                    q += (4 - gap) * 0.28
    for s in range(4):
        if suits[s] >= 2:
            high = 0
            for c in hole:
                if c & 3 == s and c >> 2 > high:
                    high = c >> 2
            q += 1.3 + 0.18 * high
        if suits[s] >= 3:
            q -= 0.8 * (suits[s] - 2)
    return q


@njit
def simulate(hole, board, count, state):
    """Unbiased uniform, collision-free opponent hands and board runouts.

    Outputs include earlier-street scores for Bayesian range conditioning.
    Samples are reused for further decisions on the same visible board.
    """
    available = np.empty(36 - 5 - len(board), dtype=np.int32)
    n = 0
    for c in range(36):
        if c not in hole and c not in board:
            available[n] = c
            n += 1
    hands = np.empty((count, 5), dtype=np.int32)
    values = np.zeros((count, 4), dtype=np.float64)
    outcomes = np.empty(count, dtype=np.float64)
    future = np.empty(count, dtype=np.float64)
    full = np.empty(5, dtype=np.int32)
    for j in range(len(board)):
        full[j] = board[j]
    draw = np.empty(10, dtype=np.int32)
    # On the river every candidate shares the same board. Score each legal
    # pair once instead of rescoring 100 combinations for every sample.
    grids = np.zeros((3, 36, 36), dtype=np.int32)
    fixed_mine = 0
    if len(board) == 5:
        grids[0] = pair_grid(board[:3])
        grids[1] = pair_grid(board[:4])
        grids[2] = pair_grid(board)
        fixed_mine = grid_score(hole, grids[2])
    for i in range(count):
        # Partial Fisher-Yates; undo it after each independent sample.
        idxs = np.empty(10, dtype=np.int32)
        needed = 10 - len(board)
        for j in range(needed):
            state, r = next_random(state)
            k = j + int(r % np.uint64(n - j))
            idxs[j] = k
            available[j], available[k] = available[k], available[j]
            draw[j] = available[j]
        for j in range(5):
            hands[i, j] = draw[j]
        opp = hands[i]
        values[i, 0] = preflop_quality(opp)
        if len(board) == 5:
            for s in range(3):
                values[i, s + 1] = grid_score(opp, grids[s])
            mine = fixed_mine
            theirs = int(values[i, 3])
        else:
            if len(board) >= 3:
                values[i, 1] = score(opp, board[:3])
            if len(board) >= 4:
                values[i, 2] = score(opp, board[:4])
            for j in range(len(board), 5):
                full[j] = draw[5 + j - len(board)]
            mine = score(hole, full)
            theirs = score(opp, full)
        outcomes[i] = 1.0 if mine > theirs else (0.5 if mine == theirs else 0.0)
        future[i] = theirs
        for j in range(needed - 1, -1, -1):
            k = idxs[j]
            available[j], available[k] = available[k], available[j]
    return hands, values, outcomes, future, state


@njit
def pair_grid(board):
    grid = np.zeros((36, 36), dtype=np.int32)
    for i in range(35):
        if i in board:
            continue
        for j in range(i + 1, 36):
            if j in board:
                continue
            best = 0
            for a in range(len(board) - 2):
                for b in range(a + 1, len(board) - 1):
                    for c in range(b + 1, len(board)):
                        v = five(i, j, board[a], board[b], board[c])
                        if v > best:
                            best = v
            grid[i, j] = best
            grid[j, i] = best
    return grid


@njit
def grid_score(hole, grid):
    best = 0
    for i in range(4):
        for j in range(i + 1, 5):
            v = grid[hole[i], hole[j]]
            if v > best:
                best = v
    return best


@njit
def exact_river(hole, board):
    """Enumerate all C(26,5)=65,780 possible opponent hands."""
    deck = np.empty(26, dtype=np.int32)
    k = 0
    for c in range(36):
        if c not in hole and c not in board:
            deck[k] = c
            k += 1
    grids = np.empty((3, 36, 36), dtype=np.int32)
    grids[0] = pair_grid(board[:3])
    grids[1] = pair_grid(board[:4])
    grids[2] = pair_grid(board)
    mine = grid_score(hole, grids[2])
    values = np.empty((65780, 4), dtype=np.float64)
    outcomes = np.empty(65780, dtype=np.float64)
    opp = np.empty(5, dtype=np.int32)
    n = 0
    for a in range(22):
        opp[0] = deck[a]
        for b in range(a + 1, 23):
            opp[1] = deck[b]
            for c in range(b + 1, 24):
                opp[2] = deck[c]
                for d in range(c + 1, 25):
                    opp[3] = deck[d]
                    for e in range(d + 1, 26):
                        opp[4] = deck[e]
                        values[n, 0] = preflop_quality(opp)
                        for s in range(3):
                            values[n, s + 1] = grid_score(opp, grids[s])
                        theirs = values[n, 3]
                        outcomes[n] = 1.0 if mine > theirs else (0.5 if mine == theirs else 0.0)
                        n += 1
    return values, outcomes


def percentiles(values):
    """Midrank percentiles preserve tied hands and split-pot equity."""
    out = np.zeros_like(values)
    for street in range(4):
        col = values[:, street]
        if np.any(col):
            ordered = np.sort(col)
            out[:, street] = (np.searchsorted(ordered, col, side="left")
                              + np.searchsorted(ordered, col, side="right")) / (2.0 * len(col))
    return out


def warm_engine():
    h = np.array([0, 5, 10, 15, 20], dtype=np.int32)
    b = np.array([3, 8, 13, 18, 23], dtype=np.int32)
    for n in (0, 3, 4, 5):
        simulate(h, b[:n], 2, np.uint64(777))
    preflop_equity(h)
