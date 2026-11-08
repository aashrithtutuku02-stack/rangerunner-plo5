"""An aggression gate must preserve probability mass and the conservative limit."""
from types import SimpleNamespace
import numpy as np
import pytest
from game import Action,AgentConfig,Game,make_deal
from research_gated import make


def inputs(name):
    policy=make(name);module=SimpleNamespace(**policy.choose_action.__globals__)
    memory={};policy.new_half(AgentConfig(),memory)
    game=Game(make_deal('gate-probabilities',0),0);game.apply(Action.RAISE_HALF)
    cache={'q':np.random.default_rng(17).random((31,4))}
    return module,memory,game.observation(game.to_act),cache


def test_conservative_limit_removes_bluff_models_and_preserves_original_value_mixture():
    m,memory,obs,cache=inputs('polar-gated')
    memory['counts'][1,0,1]+=100
    marginal,scaled=m.range_weights(obs,memory,cache)
    L=m.range_model.likelihoods(cache['q'],memory['counts'],m.range_model.event_array(m.history_events(obs)),m.SLOPES)
    L/=L.sum(axis=1)[:,None]
    expected=np.array([.1,.3,.6])@L[:3]
    np.testing.assert_allclose(marginal,expected,rtol=1e-14,atol=1e-16)
    assert not scaled[3:].any()


@pytest.mark.parametrize('name',['polar-gated','polar-gated-joint'])
def test_aggressive_limit_matches_the_corresponding_ungated_joint_distribution(name):
    m,memory,obs,cache=inputs(name)
    memory['counts'][1,0,2]+=200
    prior=memory['models'].copy();counts=memory['counts'].copy()
    marginal,scaled=m.range_weights(obs,memory,cache)
    L=m.range_model.likelihoods(cache['q'],memory['counts'],m.range_model.event_array(m.history_events(obs)),m.SLOPES)
    if name=='polar-gated':L/=L.sum(axis=1)[:,None]
    expected=prior[:,None]*L;expected/=expected.sum()
    np.testing.assert_allclose(prior[:,None]*scaled,expected,rtol=1e-14,atol=1e-16)
    np.testing.assert_allclose(marginal,expected.sum(axis=0),rtol=1e-14,atol=1e-16)
    np.testing.assert_array_equal(memory['models'],prior)
    np.testing.assert_array_equal(memory['counts'],counts)


def test_unrelated_context_counts_do_not_inflate_the_aggression_gate():
    m,memory,obs,cache=inputs('polar-gated')
    _,before=m.range_weights(obs,memory,cache)
    memory['counts'][0,0,2]+=1000
    memory['counts'][1:,1:,2]+=1000
    _,after=m.range_weights(obs,memory,cache)
    # Row masses isolate mixture weights from the hand likelihood curves.
    np.testing.assert_allclose(before.sum(axis=1),after.sum(axis=1),atol=1e-14)
