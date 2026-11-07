from types import SimpleNamespace
import numpy as np
import strategy
import range_model
from game import Action,AgentConfig,Game,make_deal


def test_unavailable_raises_become_calls_without_changing_fold_probability():
    q=np.linspace(0,1,101)[None,:];counts=np.array([4.,5.,3.]);slopes=np.array([0.,8.,16.])[:,None]
    f,c,r=range_model.action_prob(q,counts,slopes,True,.3)
    ff,cc,rr=range_model.action_prob(q,counts,slopes,True,.3,False)
    np.testing.assert_allclose(ff,f)
    np.testing.assert_allclose(cc,c+r)
    np.testing.assert_array_equal(rr,0.)
    events=range_model.event_array([(0,0,1,1,.3,0)])
    freq=np.tile(counts,(4,3,1))
    L=range_model.likelihoods(np.tile(q.ravel()[:,None],(1,4)),freq,events,slopes.ravel())
    np.testing.assert_allclose(L,cc,rtol=1e-12,atol=1e-15)


def test_last_allowed_raise_cannot_face_a_further_raise():
    memory={};strategy.initialize(AgentConfig(),memory)
    obs=SimpleNamespace(street=0,to_call=8,raises_this_street=3,
                        my_stack=72,opp_stack=64,my_bet=8,opp_bet=16)
    cache={'q':np.full((8,4),.5)}
    f,r=strategy.response_prob(obs,memory,cache,24,.25)
    np.testing.assert_array_equal(r,0.)
    obs.raises_this_street=2
    f,r=strategy.response_prob(obs,memory,cache,24,.25)
    assert np.all(r>0)


def test_reconstructed_raise_opportunities_match_every_replayed_action():
    game=Game(make_deal('raise-opportunities',0),0)
    for a in [Action.RAISE_HALF]*4+[Action.CHECK_CALL]:game.apply(a)
    obs=game.observation(game.to_act)
    replay=Game(game.deal,game.button_seat)
    expected=[]
    for idx,record in enumerate(game.history):
        if replay.to_act!=game.to_act:
            before=replay.observation(replay.to_act)
            expected.append((idx,int(Action.RAISE_POT in before.legal_actions)))
        replay.apply(record.action)
    actual=[(ev[0],ev[5]) for ev in strategy.history_events(obs)]
    assert actual==expected
    assert any(flag==0 for idx,flag in actual)


def test_a_censored_call_preserves_the_call_raise_preference_ratio():
    memory={};strategy.initialize(AgentConfig(),memory)
    before=memory['counts'][0,2].copy()
    strategy.observe_event(memory,(0,0,2,1,.2,0))
    after=memory['counts'][0,2]
    assert abs(after.sum()-before.sum()-1)<1e-12
    assert abs(after[2]/after[1]-before[2]/before[1])<1e-12
    assert after[0]==before[0]


def test_a_compulsory_free_check_does_not_change_behavior_counts():
    memory={};strategy.initialize(AgentConfig(),memory)
    before=memory['counts'].copy()
    strategy.observe_event(memory,(0,3,0,1,0.,0))
    np.testing.assert_array_equal(memory['counts'],before)
