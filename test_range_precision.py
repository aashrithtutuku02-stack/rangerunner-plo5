from types import SimpleNamespace
import numpy as np
import pytest
import fast_engine as engine
import range_precision as precision
from game import AgentConfig


def inputs():
    h=np.array([0,5,10,15,20],dtype=np.int32);b=np.array([3,8,13,18,23],dtype=np.int32)
    hands,values,outcomes,_,state=engine.simulate(h,b,1280,np.uint64(719))
    cache=dict(hole=h,board=b,hands=hands,values=values,outcomes=outcomes,q=engine.percentiles(values))
    zero=np.flatnonzero(outcomes==0)[:36];one=np.flatnonzero(outcomes==1)[:12]
    assert len(zero)==36 and len(one)==12
    weights=np.zeros(1280);weights[zero]=1/48;weights[one]=1/48
    memory=dict(config=AgentConfig(),cpu=0.,rng=state,cache=cache,precision_rng=precision.INITIAL_STATE,precision_used=0)
    obs=SimpleNamespace(street=3,to_call=10,my_stack=70,pot=30)
    return obs,memory,cache,weights,np.tile(weights,(5,1))


def uniform(obs,memory,cache):
    n=len(cache['outcomes']);return np.ones(n)/n,np.ones((5,n))/n


def test_sparse_range_extension_preserves_samples_and_primary_rng_without_mutating_old_cache():
    obs,memory,cache,weights,models=inputs();before={k:v.copy() for k,v in cache.items() if isinstance(v,np.ndarray)}
    primary=memory['rng'];extra=engine.simulate(cache['hole'],cache['board'],2816,precision.INITIAL_STATE)
    updated,_,_=precision.refine(obs,memory,cache,weights,models,uniform)
    assert updated is not cache and memory['cache'] is updated
    for name,tail in zip(('hands','values','outcomes'),extra[:3]):
        np.testing.assert_array_equal(updated[name],np.concatenate((before[name],tail)))
    for name,values in before.items():np.testing.assert_array_equal(cache[name],values)
    assert memory['rng']==primary and memory['precision_rng']==extra[-1] and memory['precision_used']==1
    assert updated['q'].shape==(4096,4)


def test_failed_range_reweighting_does_not_commit_partial_cache_or_consume_rng():
    obs,memory,cache,weights,models=inputs();state=memory['precision_rng']
    def fail(*args):raise RuntimeError('test failure')
    with pytest.raises(RuntimeError):precision.refine(obs,memory,cache,weights,models,fail)
    assert memory['cache'] is cache and memory['precision_rng']==state and memory['precision_used']==0


@pytest.mark.parametrize('reason',['budget','limit','uniform','clear_call','free_check','early'])
def test_budget_limits_and_unambiguous_or_dense_ranges_do_not_expand(reason):
    obs,memory,cache,weights,models=inputs()
    if reason=='budget':memory['cpu']=4.9
    if reason=='limit':memory['precision_used']=64
    if reason=='uniform':weights=np.ones(1280)/1280
    if reason=='clear_call':weights=(cache['outcomes']==1).astype(float);weights/=weights.sum()
    if reason=='free_check':obs.to_call=0
    if reason=='early':obs.street=0
    result=precision.refine(obs,memory,cache,weights,models,uniform)
    assert result[0] is cache and result[1] is weights and result[2] is models
