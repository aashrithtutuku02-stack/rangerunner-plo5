"""Compare the one-step expectation with complete referee-played branches."""
from dataclasses import replace
from functools import lru_cache
from unittest.mock import patch
import numpy as np
import pytest
import game
from game import Action,Game,make_deal
import range_model
import reraise_ev
from opponents import reraise_candidate_6 as bet_ev
from opponents import bet_ev_451b as old


def test_reply_sizes_match_every_reachable_numeric_state():
    visited=set();checked=0
    def visit(g):
        nonlocal checked
        key=(g.street,g.to_act,tuple(g.stacks),tuple(g.bets),tuple(g.acted),g.raises_this_street,g.last_increment)
        if key in visited:return
        visited.add(key);obs=g.observation(g.to_act)
        for a in obs.legal_actions:
            child=g.clone();child.apply(a)
            if a in (Action.RAISE_HALF,Action.RAISE_POT) and not child.is_terminal:
                reply=child.observation(child.to_act)
                if Action.RAISE_HALF in reply.legal_actions:
                    actual=reraise_ev.reply_targets(obs.pot,obs.my_stack,obs.opp_stack,obs.my_bet,obs.opp_bet,obs.raise_to[a])
                    assert list(actual)==[reply.raise_to[Action.RAISE_HALF],reply.raise_to[Action.RAISE_POT]]
                    checked+=1
            if not child.is_terminal:visit(child)
    with patch('game.omaha_score',lru_cache(maxsize=None)(game.omaha_score)):
        visit(Game(make_deal('reraise-size-oracle',0),0))
    assert len(visited)==678 and checked>100


def payoff(g,hero,paid):
    while not g.is_terminal:g.apply(Action.CHECK_CALL)
    return g.result().nets[hero]+paid


@pytest.mark.parametrize('raised',[False,True])
def test_one_step_matches_referee_branch_payoffs_and_one_shared_hero_choice(raised):
    rng=np.random.default_rng(791)
    initial=Game(make_deal('reraise-payoff-oracle',int(raised)),0)
    prefix=[]
    if raised:prefix=[Action.RAISE_HALF,Action.CHECK_CALL]
    else:prefix=[Action.CHECK_CALL,Action.CHECK_CALL]
    prefix+= [Action.CHECK_CALL]*4
    if raised:prefix.append(Action.RAISE_HALF)
    for a in prefix:initial.apply(a)
    hero=initial.to_act;obs=initial.observation(hero)
    remaining=[c for c in range(36) if c not in obs.hole_cards+tuple(initial.deal.board)]
    worlds=[];outcomes=[]
    for _ in range(47):
        other=tuple(int(x) for x in rng.choice(remaining,5,replace=False))
        hands=[None,None];hands[hero]=obs.hole_cards;hands[1-hero]=other
        d=replace(initial.deal,hole_cards=tuple(hands));g=Game(d,0)
        for a in prefix:g.apply(a)
        worlds.append(g)
        a=game.omaha_score(obs.hole_cards,d.board);b=game.omaha_score(other,d.board)
        outcomes.append(float(a>b)+.5*(a==b))
    q=rng.random(47);outcomes=np.array(outcomes)
    models=rng.dirichlet(np.ones(5));rows=rng.dirichlet(np.ones(47),5)*np.array([.5,2.,1.,.1,.2])[:,None]
    rows/=float(models@rows.sum(axis=1));joint=models[:,None]*rows
    slopes=np.array([0.,8.,16.,-8.,-16.]);frequencies=np.array([4.,6.,2.])
    targets=np.array([obs.raise_to[a] for a in (Action.RAISE_HALF,Action.RAISE_POT)])
    actual=reraise_ev.raise_values(q,rows,models,outcomes,slopes,frequencies,
        obs.pot,obs.my_stack,obs.opp_stack,obs.my_bet,obs.opp_bet,obs.raises_this_street,4,targets,float(joint.sum(axis=0)@outcomes),1.)
    if raised:
        published=bet_ev.raise_values(q,rows,models,outcomes,slopes,frequencies,
            obs.pot,obs.my_stack,obs.opp_stack,obs.my_bet,obs.opp_bet,obs.raises_this_street,4,targets,float(joint.sum(axis=0)@outcomes),3)
        np.testing.assert_allclose(published,actual,atol=1e-11,rtol=0)
    for k,action in enumerate((Action.RAISE_HALF,Action.RAISE_POT)):
        child=initial.clone();child.apply(action);reply=child.observation(child.to_act)
        f,c,r=range_model.action_prob(q[None,:],frequencies,slopes[:,None],True,reply.to_call/(reply.pot+reply.to_call))
        expected=0.
        for response,probability in [(Action.FOLD,f),(Action.CHECK_CALL,c)]:
            pay=[]
            for world in worlds:
                g=world.clone();g.apply(action);g.apply(response);pay.append(payoff(g,hero,initial.contributed[hero]))
            expected+=float(np.sum(joint*probability*np.array(pay)[None,:]))
        for response,weight in [(Action.RAISE_HALF,.25),(Action.RAISE_POT,.75)]:
            folded=[];called=[]
            for world in worlds:
                g=world.clone();g.apply(action);g.apply(response)
                fold=g.clone();fold.apply(Action.FOLD);folded.append(payoff(fold,hero,initial.contributed[hero]))
                g.apply(Action.CHECK_CALL);called.append(payoff(g,hero,initial.contributed[hero]))
            expected+=weight*max(float(np.sum(joint*r*np.array(folded)[None,:])),float(np.sum(joint*r*np.array(called)[None,:])))
        assert actual[k]==pytest.approx(expected,abs=1e-11)


@pytest.mark.parametrize('facing,raises,street',[(False,1,0),(True,0,0),(True,1,0),(True,2,1),(True,1,3)])
def test_experimental_router_preserves_openings_and_limits_early_high_aggression(facing,raises,street):
    rng=np.random.default_rng(818);q=rng.random(59);rows=rng.dirichlet(np.ones(59),5);models=np.ones(5)/5
    outcomes=rng.choice([0.,.5,1.],59);slopes=np.array([0.,8.,16.,-8.,-16.])
    for freq in (np.array([4.,6.,2.]),np.array([1.,1.,100.])):
        args=(q,rows,models,outcomes,slopes,freq,20,60,56 if facing else 60,0,4 if facing else 0,raises,4,np.array([12,20]),.5)
        actual=bet_ev.raise_values(*args,street)
        if not facing or raises==0 or (street<3 and freq[2]/freq.sum()>.7):expected=old.raise_values(*args)
        else:
            blend=1. if street==3 else min(1.,max(0.,(.70-freq[2]/freq.sum())/.35))
            expected=reraise_ev.raise_values(*args,blend)
        np.testing.assert_allclose(actual,expected,atol=1e-11,rtol=0)


def test_calling_opponent_negative_control_has_no_policy_change():
    import agent
    from adversaries import Opponent
    from research_candidates import make
    from stress_benchmark import run
    old_result=run(Opponent('call'),'reraise-caller-control',60,make('release-451b'),time_bank_seconds=80.)
    new_result=run(Opponent('call'),'reraise-caller-control',60,agent,time_bank_seconds=80.)
    assert old_result['paired']==new_result['paired']


@pytest.mark.parametrize('cap,stack',[(1,70),(4,10)])
def test_unavailable_reraise_preserves_the_released_value(cap,stack):
    rng=np.random.default_rng(33);q=rng.random(53);rows=rng.dirichlet(np.ones(53),5)
    models=np.ones(5)/5;outcomes=rng.choice([0.,.5,1.],53);slopes=np.array([0.,8.,16.,-8.,-16.])
    args=(q,rows,models,outcomes,slopes,np.array([4.,6.,2.]),20,stack,70,0,0,0,cap,np.array([10,10]),.5)
    np.testing.assert_allclose(reraise_ev.raise_values(*args,1.),old.raise_values(*args),atol=1e-11,rtol=0)


def test_zero_blend_is_the_frozen_policy_even_when_reraising_is_available():
    rng=np.random.default_rng(632)
    for _ in range(20):
        q=rng.random(57);rows=rng.dirichlet(np.ones(57),5);models=rng.dirichlet(np.ones(5))
        outcomes=rng.choice([0.,.5,1.],57);slopes=np.array([0.,8.,16.,-8.,-16.])
        args=(q,rows,models,outcomes,slopes,rng.uniform(.1,20,3),20,60,60,0,0,0,4,np.array([10,20]),float((models@rows)@outcomes))
        np.testing.assert_allclose(reraise_ev.raise_values(*args,0.),old.raise_values(*args),atol=1e-11,rtol=0)
