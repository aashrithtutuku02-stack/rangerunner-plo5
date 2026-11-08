from types import SimpleNamespace
import numpy as np
import pytest
from game import Action,AgentConfig,Game,make_deal
from research_recency import make


def fresh():
    policy=make('recent-frequency');memory={};policy.new_half(AgentConfig(),memory)
    return policy,memory,SimpleNamespace(**policy.choose_action.__globals__)


def test_fading_counts_preserve_exact_audit_counts_and_duplicate_results_are_idempotent():
    policy,memory,m=fresh();prior=memory['frequency_prior'].copy()
    m.observe_event(memory,(0,3,1,2,.3,1))
    raw=memory['counts'].copy();recent=memory['recent_counts'].copy()
    game=Game(make_deal('recency-callback',0),0);game.apply(Action.FOLD);result=game.hand_result(1)
    policy.on_hand_end(result,memory)
    np.testing.assert_array_equal(memory['counts'],raw)
    np.testing.assert_allclose(memory['recent_counts'],prior+.995*(recent-prior),atol=1e-15)
    before=memory['recent_counts'].copy();policy.on_hand_end(result,memory)
    np.testing.assert_array_equal(memory['recent_counts'],before)


def test_failed_decision_rolls_back_both_frequency_arrays():
    policy,memory,m=fresh();before=memory['counts'].copy();recent=memory['recent_counts'].copy()
    def fail(obs,state):
        m.observe_event(state,(0,1,0,2,0.,1))
        raise RuntimeError('test failure')
    policy.choose_action.__globals__['_decide']=fail
    game=Game(make_deal('recency-rollback',0),0)
    with pytest.raises(RuntimeError):policy.choose_action(game.observation(game.to_act),memory)
    np.testing.assert_array_equal(memory['counts'],before)
    np.testing.assert_array_equal(memory['recent_counts'],recent)


def test_disabling_decay_is_an_exact_negative_control_for_the_frozen_release():
    from research_candidates import make as release
    from adversaries import Opponent
    from stress_benchmark import run
    baseline=run(Opponent('bluffer'),'recent-no-decay',60,release('release-451b'),time_bank_seconds=80.)
    candidate=run(Opponent('bluffer'),'recent-no-decay',60,make('recent-none'),time_bank_seconds=80.)
    assert baseline['paired']==candidate['paired']
