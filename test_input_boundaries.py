"""Malformed arrays cannot turn Python API errors into native memory errors."""
import numpy as np
import pytest
import fast_engine as e

H=[0,5,10,15,20]
B=[3,8,13,18,23]


@pytest.mark.parametrize('hole,board',[
    (H[:-1],B),(H+[25],B),([-1,5,10,15,20],B),([36,5,10,15,20],B),
    ([2**32,5,10,15,20],B),([0,0,10,15,20],B),(H,[0,8,13,18,23]),
    (H,B[:2]),(H,B+[24]),([[0,5,10,15,20]],B),([.5,5,10,15,20],B),
])
def test_invalid_score_inputs_raise(hole,board):
    with pytest.raises(ValueError):e.score(hole,board)


@pytest.mark.parametrize('count,state',[(0,1),(-1,1),(1.5,1),(65537,1),(1,0),(1,-1),(1,2**64)])
def test_invalid_sample_arguments_raise(count,state):
    with pytest.raises(ValueError):e.simulate(H,[],count,state)


def test_legal_card_id_boundaries_and_empty_board_work():
    hole=[0,1,2,3,35]
    result=e.simulate(hole,[],8,np.uint64(1))
    assert result[0].shape==(8,5)
    assert 0<e.preflop_equity(hole)<1
