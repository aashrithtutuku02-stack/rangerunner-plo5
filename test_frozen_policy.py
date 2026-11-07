from adversaries import Opponent
from research_candidates import make
from stress_benchmark import run


def test_frozen_self_play_is_exactly_zero_when_sampling_budget_is_fixed():
    result=run(Opponent('incumbent'),'frozen-self-play',20,make('incumbent'),time_bank_seconds=80.)
    assert result['paired']==[0.]*20
