"""Joint hand/model conditioning checked against an explicit finite prior."""
from types import SimpleNamespace
import numpy as np
from game import Action,AgentConfig,Game,make_deal
from research_joint import make


def test_current_history_updates_both_model_and_hand_without_mutating_prior():
    policy=make('polar-joint')
    module=SimpleNamespace(**policy.choose_action.__globals__)
    memory={};policy.new_half(AgentConfig(),memory)
    prior=memory['models'].copy()
    game=Game(make_deal('joint-prior-test',0),0)
    game.apply(Action.RAISE_HALF)
    obs=game.observation(game.to_act)
    q=np.array([[.1,.2,.3,.4],[.3,.4,.5,.6],[.7,.6,.5,.4],[.9,.8,.7,.6]])
    events=module.history_events(obs,memory['config'].raise_cap)
    likelihood=module.range_model.likelihoods(q,memory['counts'],module.range_model.event_array(events),module.SLOPES)
    expected=prior[:,None]*likelihood/len(q)
    expected/=expected.sum()
    marginal,scaled=module.range_weights(obs,memory,{'q':q})
    np.testing.assert_allclose(prior[:,None]*scaled,expected,rtol=1e-14,atol=1e-16)
    np.testing.assert_allclose(marginal,expected.sum(axis=0),rtol=1e-14,atol=1e-16)
    np.testing.assert_array_equal(memory['models'],prior)
    assert abs(marginal.sum()-1)<1e-14


def test_no_history_leaves_the_joint_prior_uniform_over_hands():
    policy=make('polar-joint')
    module=SimpleNamespace(**policy.choose_action.__globals__)
    memory={};policy.new_half(AgentConfig(),memory)
    game=Game(make_deal('joint-empty-test',0),0)
    q=np.random.default_rng(5).random((17,4))
    marginal,scaled=module.range_weights(game.observation(game.to_act),memory,{'q':q})
    np.testing.assert_allclose(marginal,np.ones(17)/17,atol=1e-16)
    np.testing.assert_allclose(scaled,np.ones((5,17))/17,atol=1e-16)
