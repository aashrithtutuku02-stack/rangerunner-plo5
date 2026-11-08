import numpy as np
import pytest
import range_model as p
from opponents import release_b15a_model as old


@pytest.mark.parametrize('frequencies',[(4.,6.,2.),(1.,2.,9.),(9.,2.,1.),(0.,8.,4.)])
@pytest.mark.parametrize('facing',[False,True])
def test_polarized_margins_integrate_to_observed_frequencies(frequencies,facing):
    q=(np.arange(100000)+.5)/100000
    f,c,r=p.action_prob(q,np.array(frequencies),-16.,facing,.28)
    target=np.array(frequencies)
    if not facing:target[0]=0
    target/=target.sum()
    np.testing.assert_allclose([f.mean(),c.mean(),r.mean()],target,atol=3e-9,rtol=0)
    np.testing.assert_allclose(f+c+r,1.,atol=1e-14)
    assert min(f.min(),c.min(),r.min())>=0


def test_new_positive_models_preserve_the_old_formula():
    q=np.linspace(0,1,101)[None,:];s=np.array([0.,8.,16.])[:,None]
    for actual,expected in zip(p.action_prob(q,[4.,6.,2.],s,True,.33),old.action_prob(q,[4.,6.,2.],s,True,.33)):
        np.testing.assert_allclose(actual,expected,rtol=1e-13,atol=1e-15)


def test_compiled_polarized_likelihoods_match_broadcast_formula():
    rng=np.random.default_rng(177);q=rng.random((73,4))
    counts=rng.uniform(.1,20,(4,3,3));counts[:,0,0]=0
    slopes=np.array([0.,8.,16.,-8.,-16.]);expected=np.ones((5,73))
    events=[(0,0,1,2,.25,1),(2,1,0,1,0.,1),(4,2,2,1,.3,0),(6,3,1,3,.2,1)]
    for _,s,context,action,price,available in events:
        expected*=p.action_prob(q[None,:,s],counts[s,context],slopes[:,None],bool(context),price,bool(available))[min(action,2)]
    np.testing.assert_allclose(p.likelihoods(q,counts,p.event_array(events),slopes),expected,atol=1e-14,rtol=1e-12)


def test_polarized_raise_probability_has_two_tails_without_strong_hand_folds():
    q=np.linspace(0,1,1001)
    f,c,r=p.action_prob(q,[0.,7.,5.],-16.,False,.28)
    assert r[0]>r[500] and r[-1]>r[500]
    assert np.all(f==0)
    f,_,_=p.action_prob(q,[4.,6.,2.],-16.,True,.28)
    assert np.all(np.diff(f)<=0)


@pytest.mark.parametrize('frequencies',[(0.,1.,0.),(0.,0.,1.),(1.,0.,0.),(1e9,1.,1.),(1.,1e9,1.)])
def test_extreme_frequencies_and_endpoint_ranks_remain_valid(frequencies):
    q=np.array([0.,1e-12,.5,1-1e-12,1.])[None,:]
    slopes=np.array([0.,8.,16.,-8.,-16.])[:,None]
    for capped in (False,True):
        probabilities=p.action_prob(q,frequencies,slopes,True,.28,not capped)
        assert all(np.isfinite(x).all() and (x>=0).all() for x in probabilities)
        np.testing.assert_allclose(sum(probabilities),1.,atol=3e-15,rtol=0)
        if capped:assert not probabilities[2].any()


def test_polarized_raise_kernel_integrates_the_same_joint_expectation():
    import bet_ev as polar_bet_ev
    rng=np.random.default_rng(917)
    for capped in (False,True):
        q=rng.random(79);ranges=rng.dirichlet(np.ones(79),5);models=rng.dirichlet(np.ones(5))
        slopes=np.array([0.,8.,16.,-8.,-16.]);frequencies=np.array([4.,6.,2.])
        outcomes=rng.choice([0.,.5,1.],79);weights=models@ranges;equity=float(weights@outcomes)
        targets=np.array([10,20]);raises=3 if capped else 1
        actual=polar_bet_ev.raise_values(q,ranges,models,outcomes,slopes,frequencies,
                                        20,70,70,0,0,raises,4,targets,equity)
        for k,target in enumerate(targets):
            final=20+2*target
            f,c,r=p.action_prob(q[None,:],frequencies,slopes[:,None],True,target/final,not capped)
            joint=models[:,None]*ranges
            expected=float(np.sum(joint*(f*20+(1-f)*(outcomes*final-target))))
            expected-=float(np.sum(joint*r))*min(70-target,final)*max(0.,.68-equity)
            assert actual[k]==pytest.approx(expected,abs=1e-11)


def test_positive_research_kernel_matches_frozen_released_kernel():
    import bet_ev as polar_bet_ev
    from opponents import bet_ev_52c5 as frozen
    rng=np.random.default_rng(41)
    q=rng.random(80);ranges=rng.dirichlet(np.ones(80),3);models=np.array([.1,.3,.6])
    outcomes=rng.choice([0.,.5,1.],80);slopes=np.array([0.,8.,16.])
    args=(q,ranges,models,outcomes,slopes,np.array([4.,6.,2.]),20,70,70,0,0,1,4,np.array([10,20]),.5)
    np.testing.assert_allclose(polar_bet_ev.raise_values(*args),frozen.raise_values(*args),atol=1e-11,rtol=0)


def test_promoted_strategy_matches_the_frozen_research_candidate():
    import agent
    from adversaries import Opponent
    from research_candidates import make
    from stress_benchmark import run
    old=run(Opponent('call'),'caller-promotion-mirror',100,make('margin-passive'),time_bank_seconds=80.)
    current=run(Opponent('call'),'caller-promotion-mirror',100,agent,time_bank_seconds=80.)
    assert old['paired']==current['paired']
