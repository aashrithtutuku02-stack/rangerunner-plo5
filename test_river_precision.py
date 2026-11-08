from types import SimpleNamespace
import numpy as np
import pytest

import fast_engine as engine
import river_precision as precision
from game import AgentConfig


def cache_and_memory():
    h=np.array([0,5,10,15,20],dtype=np.int32)
    b=np.array([3,8,13,18,23],dtype=np.int32)
    hands,values,outcomes,_,rng=engine.simulate(h,b,1280,np.uint64(7123))
    cache=dict(hole=h,board=b,hands=hands,values=values,outcomes=outcomes,q=engine.percentiles(values))
    return cache,dict(rng=rng,cpu=0.,config=AgentConfig())


def test_extending_preserves_prefix_and_main_rng_and_matches_auxiliary_draws():
    cache,memory=cache_and_memory()
    old=cache['hands'].copy()
    base_rng=memory['rng']
    base_values=cache['values'].copy();base_outcomes=cache['outcomes'].copy()
    precision.extend(memory,cache)
    expected=engine.simulate(cache['hole'],cache['board'],2816,precision.INITIAL_STATE)
    np.testing.assert_array_equal(cache['hands'][:1280],old)
    for actual,initial,target in zip([cache['hands'],cache['values'],cache['outcomes']],
                                     [old,base_values,base_outcomes],expected[:3]):
        np.testing.assert_array_equal(actual,np.concatenate((initial,target)))
    assert memory['rng']==base_rng and memory['precision_rng']==expected[-1]
    assert cache['q'].shape==(4096,4)


def test_only_close_calls_with_available_budget_are_expanded():
    cache,memory=cache_and_memory()
    cache['outcomes']=np.tile([0.,1.,0.,0.],320)
    weights=np.ones(1280)/1280
    obs=SimpleNamespace(board=cache['board'],to_call=10,my_stack=70,pot=30,hand_index=100)
    assert precision.needs_more(obs,memory,cache,weights)
    obs.pot=90
    assert not precision.needs_more(obs,memory,cache,weights)
    obs.pot=30;obs.to_call=0
    assert not precision.needs_more(obs,memory,cache,weights)
    obs.to_call=10;memory['cpu']=4.5
    assert not precision.needs_more(obs,memory,cache,weights)
    memory['cpu']=.4
    assert not precision.needs_more(obs,memory,cache,weights)


def test_extra_samples_are_not_repeated_and_early_streets_are_excluded():
    cache,memory=cache_and_memory()
    precision.extend(memory,cache)
    rng=memory['precision_rng'];precision.extend(memory,cache)
    assert memory['precision_rng']==rng and len(cache['outcomes'])==4096
    obs=SimpleNamespace(board=cache['board'],to_call=10,my_stack=70,pot=30,hand_index=100)
    assert not precision.needs_more(obs,memory,cache,np.ones(4096)/4096)
    cache['board']=cache['board'][:4];obs.board=cache['board']
    assert not precision.needs_more(obs,memory,cache,np.ones(4096)/4096)
    with pytest.raises(ValueError):precision.extend(memory,cache)


def test_frozen_compiled_release_matches_frozen_vector_policy():
    from research_candidates import make
    from stress_benchmark import run
    result=run(make('release-b15a'),'compiled-policy-mirror',40,make('release-52c5'),time_bank_seconds=80.)
    assert result['paired']==[0.]*40
