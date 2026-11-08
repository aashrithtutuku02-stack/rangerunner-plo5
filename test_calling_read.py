from types import SimpleNamespace
import numpy as np
import pytest
import calling_read as read
from game import Action,AgentConfig,Game,make_deal
from research_candidates import make


@pytest.mark.parametrize('event',[(0,1,0,1,0.,1),(0,1,1,1,.3,0),(0,1,2,1,.3,0)])
def test_free_checks_and_unavailable_raises_add_no_calling_evidence(event):
    window=(1,2,1)
    assert read.add_response(window,event) is window


def test_read_requires_evidence_and_recent_aggression_invalidates_it():
    assert not read.confident_caller((1,)*23)
    assert read.confident_caller((1,)*24)
    assert not read.confident_caller((1,)*16+(0,)*8)
    window=(1,)*64
    for i in range(7):window=read.add_response(window,(i,2,1,3,.3,1))
    assert len(window)==64 and not read.confident_caller(window)


def test_fold_is_negative_evidence_even_if_raising_was_unavailable():
    window=(1,)*24
    updated=read.add_response(window,(0,3,2,0,.4,0))
    assert updated==window+(0,)


@pytest.mark.parametrize('calls,equity,expected',[(23,.51,Action.CHECK_CALL),
    (24,.51,Action.RAISE_POT),(24,.49,Action.CHECK_CALL)])
@pytest.mark.parametrize('name',['margin-passive','release'])
def test_margin_changes_only_for_confident_value_bets(monkeypatch,calls,equity,expected,name):
    policy=make(name);memory={};policy.new_half(AgentConfig(),memory)
    memory['response_window']=(1,)*calls
    g=Game(make_deal('calling-value-oracle',0),0)
    while int(g.street)<3:g.apply(Action.CHECK_CALL)
    obs=g.observation(g.to_act)
    memory.update(seen_hand=obs.hand_index,seen_count=len(obs.action_history),seen_history=tuple(obs.action_history))
    namespace=policy.choose_action.__globals__
    monkeypatch.setitem(namespace,'cache_samples',lambda o,m:{'q':np.full((1,4),.5),'outcomes':np.array([equity])})
    monkeypatch.setitem(namespace,'range_weights',lambda o,m,c:(np.ones(1),np.ones((5,1))))
    monkeypatch.setitem(namespace,'bet_ev',SimpleNamespace(raise_values=lambda *args:np.array([2.05,2.10])))
    assert policy.choose_action(obs,memory)==expected


def test_decision_failure_restores_response_window_and_half_reset_clears_it(monkeypatch):
    policy=make('margin-passive');memory={};policy.new_half(AgentConfig(),memory)
    counts=memory['counts'].copy();namespace=policy.choose_action.__globals__
    def fail(obs,state):
        namespace['observe_event'](state,(0,0,1,1,.25,1))
        raise RuntimeError('inference failure')
    monkeypatch.setitem(namespace,'_decide',fail)
    g=Game(make_deal('calling-read-rollback',0),0)
    with pytest.raises(RuntimeError):policy.choose_action(g.observation(g.to_act),memory)
    assert memory['response_window']==()
    np.testing.assert_array_equal(memory['counts'],counts)
    memory['response_window']=(1,)*64;policy.new_half(AgentConfig(),memory)
    assert memory['response_window']==()


def test_always_raising_opponent_is_an_exact_policy_negative_control():
    from adversaries import Opponent
    from stress_benchmark import run
    baseline=run(Opponent('pot'),'calling-read-negative',60,make('release-9efa'),time_bank_seconds=80.)
    candidate=run(Opponent('pot'),'calling-read-negative',60,make('margin-passive'),time_bank_seconds=80.)
    assert baseline['paired']==candidate['paired']
