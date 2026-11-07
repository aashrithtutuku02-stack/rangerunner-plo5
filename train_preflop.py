"""Offline, reproducible preflop equity table. Never run during a match.

Usage: python train_preflop.py --samples 8192
All 376,992 starting hands reduce to 19,998 suit-isomorphism classes.
"""
import argparse
from itertools import combinations
from pathlib import Path
import time

import numpy as np
from numba import njit

from equity_engine import next_random, score


@njit
def train_batch(holes, samples, state):
    equities = np.zeros(len(holes), dtype=np.float64)
    deck = np.empty(31, dtype=np.int32)
    opp = np.empty(5, dtype=np.int32)
    board = np.empty(5, dtype=np.int32)
    idxs = np.empty(10, dtype=np.int32)
    for row in range(len(holes)):
        hole = holes[row]
        n = 0
        for c in range(36):
            if c not in hole:
                deck[n] = c
                n += 1
        wins = 0.0
        for trial in range(samples):
            for j in range(10):
                state, r = next_random(state)
                k = j + int(r % np.uint64(31 - j))
                idxs[j] = k
                deck[j], deck[k] = deck[k], deck[j]
                if j < 5:
                    opp[j] = deck[j]
                else:
                    board[j - 5] = deck[j]
            mine = score(hole, board)
            theirs = score(opp, board)
            wins += 1.0 if mine > theirs else (0.5 if mine == theirs else 0.0)
            for j in range(9, -1, -1):
                k = idxs[j]
                deck[j], deck[k] = deck[k], deck[j]
        equities[row] = wins / samples
    return equities, state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=8192)
    parser.add_argument('--output', default='preflop.npz')
    args = parser.parse_args()
    start = time.perf_counter()
    canonical = {}
    multiplicities = {}
    for cards in combinations(range(36), 5):
        masks = [0] * 4
        for c in cards:
            masks[c & 3] |= 1 << (c >> 2)
        masks.sort()
        key = masks[0] | masks[1] << 9 | masks[2] << 18 | masks[3] << 27
        canonical.setdefault(key, cards)
        multiplicities[key] = multiplicities.get(key, 0) + 1
    keys = np.array(sorted(canonical), dtype=np.int64)
    holes = np.array([canonical[k] for k in keys], dtype=np.int32)
    weights = np.array([multiplicities[k] for k in keys], dtype=np.int32)
    equities = np.zeros(len(keys))
    state = np.uint64(0xD1B54A32D192ED03)
    for begin in range(0, len(keys), 500):
        end = min(begin + 500, len(keys))
        equities[begin:end], state = train_batch(holes[begin:end], args.samples, np.uint64(state))
        print(f'{end}/{len(keys)} hands, {time.perf_counter()-start:.1f}s', flush=True)
    # Uniform hands must average exactly 50% against uniform opponents.
    adjustment = 0.5 - np.average(equities, weights=weights)
    equities += adjustment
    np.savez_compressed(args.output, keys=keys, equities=equities.astype(np.float32),
                        multiplicities=weights, samples=args.samples, seed='D1B54A32D192ED03')
    print(f'Saved {args.output}; equity range {equities.min():.4f}..{equities.max():.4f}; '
          f'calibration adjustment {adjustment:.6f}', flush=True)


if __name__ == '__main__':
    main()
