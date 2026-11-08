from dataclasses import replace
from types import SimpleNamespace
import pytest
import bluff_read as b
from game import Action,Game,make_deal


def test_free_checks_and_blind_completions_do_not_teach_bet_folds():
    w=((),())
    assert b.observe(w,(0,0,1,0,.25,1)) is w
    assert b.observe(w,(3,1,0,1,0.,1)) is w
    assert b.observe(w,(4,1,2,0,.3,1)) is w


def test_capped_calls_and_folds_both_inform_fold_frequency():
    w=b.observe(((),()),(2,1,1,1,.25,0))
    w=b.observe(w,(3,1,1,0,.25,0))
    assert w==((),((.25,0),(.25,1)))


def test_expensive_bet_folds_cannot_justify_cheap_bet_bluffs():
    assert b.fold_bound(((.4,1),)*64,.25)==0.
    assert b.fold_bound(((.25,1),)*15,.25)==0.
    assert b.fold_bound(((.25,1),)*64,.25)>.9
    assert b.fold_bound(((.25,0),)*64,.25)<.01


def test_fold_windows_are_separate_bounded_immutable_state():
    before=((),());w=before
    for i in range(200):w=b.observe(w,(i+1,0,1,0,.25,1))
    assert len(w[0])==128 and w[1]==() and before==((),())


def test_private_card_mix_is_stable_for_retries_and_card_order():
    g=Game(make_deal('bluff-coin',0),0);obs=g.observation(g.to_act)
    assert 0<=b.coin(obs)<1
    assert b.coin(obs)==b.coin(replace(obs,hole_cards=tuple(reversed(obs.hole_cards))))


@pytest.mark.parametrize('kind',['caller','facing','value','already_betting'])
def test_no_extra_bluffs_without_a_supported_opening_opportunity(kind):
    g=Game(make_deal('bluff-opportunity',0),0)
    obs=g.observation(g.to_act)
    obs=replace(obs,to_call=1 if kind=='facing' else 0)
    window=((.1,0 if kind=='caller' else 1),)*64
    action=Action.RAISE_HALF if kind=='already_betting' else Action.CHECK_CALL
    eq=.6 if kind=='value' else .1
    assert b.choose(obs,{'fold_windows':(window,window)},eq,eq*obs.pot,action,1.)==action


def test_supported_low_equity_opening_can_bluff():
    g=Game(make_deal('bluff-profit',0),0);g.apply(Action.CHECK_CALL)
    obs=g.observation(g.to_act);assert obs.to_call==0
    w=((.1,1),)*64
    assert b.choose(obs,{'fold_windows':(w,w)},.1,.1*obs.pot,Action.CHECK_CALL,1.) in (Action.RAISE_HALF,Action.RAISE_POT)


def test_failed_decision_restores_fold_evidence(monkeypatch):
    from research_candidates import make
    from game import AgentConfig
    policy=make('bluff-quarter');memory={};policy.new_half(AgentConfig(),memory)
    namespace=policy.choose_action.__globals__
    def fail(obs,state):
        namespace['observe_event'](state,(2,1,1,0,.25,1))
        raise RuntimeError('rollback probe')
    monkeypatch.setitem(namespace,'_decide',fail)
    g=Game(make_deal('bluff-rollback',0),0)
    with pytest.raises(RuntimeError):policy.choose_action(g.observation(g.to_act),memory)
    assert memory['fold_windows']==((),())
