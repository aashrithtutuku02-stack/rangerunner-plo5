"""A safety margin gates aggression once; raise sizes share the same gate."""
from types import SimpleNamespace
import numpy as np
import pytest
from game import Action,AgentConfig,Game,make_deal
from research_candidates import make


@pytest.mark.parametrize('half,pot,expected',[
    (2.5,2.6,Action.RAISE_POT),(2.6,2.5,Action.RAISE_HALF),
    (2.1,2.15,Action.CHECK_CALL),(2.3,2.3,Action.RAISE_HALF),
    (1.,2.3,Action.RAISE_POT),
])
def test_raise_ranking_uses_one_shared_passive_threshold(monkeypatch,half,pot,expected):
    policy=make('margin-once');memory={};policy.new_half(AgentConfig(),memory)
    g=Game(make_deal('raise-ranking-oracle',0),0)
    while int(g.street)<3:g.apply(Action.CHECK_CALL)
    obs=g.observation(g.to_act)
    assert obs.pot==4 and obs.to_call==0
    cache={'q':np.full((1,4),.5),'outcomes':np.array([.5])}
    namespace=policy.choose_action.__globals__
    monkeypatch.setitem(namespace,'cache_samples',lambda o,m:cache)
    monkeypatch.setitem(namespace,'range_weights',lambda o,m,c:(np.ones(1),np.ones((5,1))))
    monkeypatch.setitem(namespace,'bet_ev',SimpleNamespace(raise_values=lambda *args:np.array([half,pot])))
    assert policy.choose_action(obs,memory)==expected


def test_legacy_hurdle_can_reject_the_better_raise(monkeypatch):
    # The baseline picks half despite pot having the larger modeled return.
    policy=make('release-9efa');memory={};policy.new_half(AgentConfig(),memory)
    g=Game(make_deal('raise-ranking-oracle',0),0)
    while int(g.street)<3:g.apply(Action.CHECK_CALL)
    namespace=policy.choose_action.__globals__
    monkeypatch.setitem(namespace,'cache_samples',lambda o,m:{'q':np.full((1,4),.5),'outcomes':np.array([.5])})
    monkeypatch.setitem(namespace,'range_weights',lambda o,m,c:(np.ones(1),np.ones((5,1))))
    monkeypatch.setitem(namespace,'bet_ev',SimpleNamespace(raise_values=lambda *args:np.array([2.5,2.6])))
    assert policy.choose_action(g.observation(g.to_act),memory)==Action.RAISE_HALF
