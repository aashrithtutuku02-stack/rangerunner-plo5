import numpy as np
import pytest
from game import Action,AgentConfig,Game,make_deal
from research_candidates import make


def preflop_showdown(name):
    policy=make(name);memory={};policy.new_half(AgentConfig(),memory)
    g=Game(make_deal('group-learning-allin',0),0)
    while not g.is_terminal:
        seat=g.to_act
        if seat==0:policy.choose_action(g.observation(seat),memory)
        action=Action.RAISE_POT if Action.RAISE_POT in g.legal_actions() else Action.CHECK_CALL
        if seat==0:
            obs,_,cache=memory['last'];memory['last']=(obs,action,cache)
        g.apply(action)
    assert g.result().went_to_showdown
    return policy,memory,g.hand_result(0)


@pytest.mark.parametrize('name',['street-split','street-shrink','street-mix'])
def test_preflop_showdown_does_not_teach_unobserved_postflop_groups(name):
    policy,memory,result=preflop_showdown(name);before=memory['group_models'].copy()
    policy.on_hand_end(result,memory)
    np.testing.assert_array_equal(memory['group_models'][1:],before[1:])
    assert not np.array_equal(memory['group_models'][0],before[0])
    np.testing.assert_allclose(memory['group_models'].sum(axis=1),1.,atol=1e-14)
    assert (memory['group_models']>0).all()
    after=memory['group_models'].copy();policy.on_hand_end(result,memory)
    np.testing.assert_array_equal(memory['group_models'],after)


def test_group_learning_failure_restores_global_and_local_learning(monkeypatch):
    import street_learning
    policy,memory,result=preflop_showdown('street-mix')
    arrays={n:memory[n].copy() for n in ('counts','models','global_models','group_models')}
    completed=memory['completed_hands'].copy()
    def fail(*args):raise RuntimeError('synthetic inference failure')
    monkeypatch.setattr(street_learning,'revealed_ranks',fail)
    with pytest.raises(RuntimeError):policy.on_hand_end(result,memory)
    for name,array in arrays.items():np.testing.assert_array_equal(memory[name],array)
    assert memory['completed_hands']==completed


def test_independent_group_joint_distribution_is_normalized():
    policy=make('street-mix');memory={};policy.new_half(AgentConfig(),memory)
    g=Game(make_deal('group-joint-normalization',0),0)
    g.apply(Action.RAISE_HALF);g.apply(Action.CHECK_CALL)
    policy.choose_action(g.observation(g.to_act),memory)
    mix,rows=policy.choose_action.__globals__['range_weights'](g.observation(g.to_act),memory,memory['cache'])
    np.testing.assert_allclose(memory['models']@rows,mix,atol=1e-14)
    assert np.isfinite(rows).all() and (rows>=0).all()
    assert abs(mix.sum()-1)<1e-12
