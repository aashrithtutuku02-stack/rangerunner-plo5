"""Native/fallback equivalence with identical random samples and state."""
import random
import os
import platform
import numpy as np

import equity_engine as reference
import fast_engine as fast
from evaluator import omaha_score


def test_shipped_linux_kernel_loads_on_tournament_architecture():
    if (platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64')
            and os.environ.get('RANGERUNNER_ENGINE')!='numba'):
        assert fast.BACKEND=='portable C'


def test_native_samples_match_numba_bit_for_bit():
    rng = random.Random(9841)
    for _ in range(24):
        cards = rng.sample(range(36), 10)
        hole = np.array(cards[:5], dtype=np.int32)
        board = np.array(cards[5:], dtype=np.int32)
        for n in (0, 3, 4, 5):
            state = np.uint64(rng.randrange(1, 2**64))
            expected = reference.simulate(hole, board[:n], 64, state)
            actual = fast.simulate(hole, board[:n], 64, state)
            for a, b in zip(expected, actual):
                np.testing.assert_array_equal(a, b)


def test_native_score_matches_official_evaluator():
    rng = random.Random(4327)
    for _ in range(1000):
        cards = rng.sample(range(36), 10)
        assert fast.score(cards[:5], cards[5:]) == omaha_score(cards[:5], cards[5:])


def test_preflop_native_lookup_matches_reference():
    rng = random.Random(210)
    for _ in range(500):
        hole = np.array(rng.sample(range(36), 5), dtype=np.int32)
        assert 0 < fast.preflop_equity(hole) < 1
        assert fast.preflop_equity(hole) == reference.preflop_equity(hole)
