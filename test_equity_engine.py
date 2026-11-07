"""Independent rule checks against the supplied tournament evaluator."""
import random
from itertools import combinations

import numpy as np

import equity_engine as e
from evaluator import omaha_score, score_five, cards_from_str


def test_all_five_card_rankings_match_tournament():
    # Exhaustive verification catches wheel, flush, kicker and rank-table bugs.
    for cards in combinations(range(36), 5):
        assert e.five(*cards) == score_five(cards)


def test_omaha_uses_exactly_two_hole_and_three_board_cards():
    rng = random.Random(28)
    for _ in range(500):
        cards = rng.sample(range(36), 10)
        hole = np.array(cards[:5], dtype=np.int32)
        board = np.array(cards[5:], dtype=np.int32)
        assert e.score(hole, board) == omaha_score(hole.tolist(), board.tolist())
        for n in (3, 4):
            expected = max(score_five(h + b) for h in combinations(tuple(hole), 2)
                           for b in combinations(tuple(board[:n]), 3))
            assert e.score(hole, board[:n]) == expected


def test_samples_are_disjoint_and_outcomes_use_supplied_evaluator():
    hole = np.array(cards_from_str('AcAdKhQhJs'), dtype=np.int32)
    board = np.array(cards_from_str('6c7c8c9dTs'), dtype=np.int32)
    for n in (0, 3, 4, 5):
        hands, values, outcomes, future, state = e.simulate(hole, board[:n], 128, np.uint64(7341))
        for h in hands:
            assert len(set(h)) == 5
            assert not set(h).intersection(hole)
            assert not set(h).intersection(board[:n])
        if n == 5:
            mine = omaha_score(hole.tolist(), board.tolist())
            for h, outcome in zip(hands, outcomes):
                theirs = omaha_score(h.tolist(), board.tolist())
                assert outcome == (1 if mine > theirs else .5 if mine == theirs else 0)
        again = e.simulate(hole, board[:n], 128, np.uint64(7341))
        np.testing.assert_array_equal(hands, again[0])
        np.testing.assert_array_equal(outcomes, again[2])


def test_preflop_table_coverage_and_suit_symmetry():
    assert len(e.PREFLOP_KEYS) == 19998, 'Include preflop.npz in the submission'
    keys = set()
    for cards in combinations(range(36), 5):
        masks = [0] * 4
        for c in cards:
            masks[c & 3] |= 1 << (c >> 2)
        masks.sort()
        keys.add(masks[0] | masks[1] << 9 | masks[2] << 18 | masks[3] << 27)
    assert keys == set(e.PREFLOP_KEYS)
    assert np.all((e.PREFLOP_EQUITIES > 0) & (e.PREFLOP_EQUITIES < 1))
    for cards in random.Random(123).sample(list(combinations(range(36), 5)), 50):
        hole = np.array(cards, dtype=np.int32)
        renamed = np.array([(c & ~3) | ((c + 1) & 3) for c in cards], dtype=np.int32)
        assert e.preflop_equity(hole) == e.preflop_equity(renamed)
