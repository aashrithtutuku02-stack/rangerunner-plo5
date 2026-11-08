from adversaries import Opponent
from research_candidates import make
from stress_benchmark import run


def test_frozen_self_play_is_exactly_zero_when_sampling_budget_is_fixed():
    result=run(Opponent('incumbent'),'frozen-self-play',20,make('incumbent'),time_bank_seconds=80.)
    assert result['paired']==[0.]*20


def test_frozen_b15a_self_play_is_exactly_zero():
    result=run(Opponent('release-b15a'),'b15a-self-play',20,make('release-b15a'),time_bank_seconds=80.)
    assert result['paired']==[0.]*20


def test_frozen_f452_self_play_is_exactly_zero():
    result=run(Opponent('release-f452'),'f452-self-play',20,make('release-f452'),time_bank_seconds=80.)
    assert result['paired']==[0.]*20
