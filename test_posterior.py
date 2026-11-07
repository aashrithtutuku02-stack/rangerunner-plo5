from types import SimpleNamespace
import numpy as np

import strategy
from game import AgentConfig


def test_response_mixture_conditions_model_on_candidate_hand(monkeypatch):
    monkeypatch.setattr(strategy,'SLOPES',np.array([0.,4.,8.,16.]))
    memory={};strategy.initialize(AgentConfig(),memory)
    memory['models']=np.array([.2,.3,.3,.2])
    memory['counts'][3,1]=[3,4,2]
    q=np.array([[.1,.1,.1,.1],[.5,.5,.5,.5],[.9,.9,.9,.9]])
    ranges=np.array([[.8,.1,.1],[.1,.8,.1],[.1,.1,.8],[.05,.15,.8]])
    obs=SimpleNamespace(street=3,to_call=0)
    f,r=strategy.response_prob(obs,memory,{'q':q},1,.28,ranges)
    # Evaluate the conditional joint distribution directly, one hand/model
    # at a time. This is the law of total probability with model-dependent
    # hand likelihoods, not a product of marginal probabilities.
    for hand in range(3):
        denom=sum(memory['models'][m]*ranges[m,hand] for m in range(4))
        expected_f=expected_r=0.0
        for m,slope in enumerate(strategy.SLOPES):
            fp,cp,rp=strategy.action_prob(np.array([q[hand,3]]),memory['counts'][3,1],slope,True,.28)
            posterior=memory['models'][m]*ranges[m,hand]/denom
            expected_f+=posterior*fp[0];expected_r+=posterior*rp[0]
        assert abs(f[hand]-expected_f)<1e-12
        assert abs(r[hand]-expected_r)<1e-12


def test_expensive_bets_induce_more_folds_than_cheap_bets():
    q=np.array([.1,.4,.7,.9])
    counts=np.array([4.,6.,2.])
    cheap=strategy.action_prob(q,counts,4.,True,.05)[0]
    expensive=strategy.action_prob(q,counts,4.,True,.40)[0]
    assert np.all(expensive>cheap)


def test_history_prices_match_replayed_official_game():
    from game import Game,make_deal
    game=Game(make_deal('history-price',0),0)
    # Include raises, calls and street transitions.
    from game import Action
    actions=[Action.RAISE_HALF,Action.CHECK_CALL,Action.CHECK_CALL,
             Action.RAISE_HALF,Action.CHECK_CALL,Action.CHECK_CALL,
             Action.RAISE_HALF,Action.CHECK_CALL]
    for a in actions:
        if game.is_terminal:break
        game.apply(a)
    obs=game.observation(game.to_act)
    replay=Game(game.deal,game.button_seat)
    expected=[]
    for idx,record in enumerate(game.history):
        before=replay.observation(replay.to_act)
        if replay.to_act!=game.to_act:
            expected.append((idx,int(before.street),int(before.to_call>0),int(record.action),
                             before.to_call/max(1,before.pot+before.to_call)))
        replay.apply(record.action)
    assert strategy.history_events(obs)==expected


def test_history_distinguishes_forced_blinds_from_voluntary_reraises():
    from game import Game,make_deal,Action
    game=Game(make_deal('reraise-history',0),0)
    for a in [Action.RAISE_HALF,Action.RAISE_HALF,Action.RAISE_HALF,Action.CHECK_CALL]:
        game.apply(a)
    # Active seat 1 sees opponent seat 0's initial blind-facing raise and
    # subsequent voluntary re-raise in distinct contexts.
    obs=game.observation(1)
    assert [(idx,context) for idx,street,context,action,price in strategy.history_events(obs)]==[(0,1),(2,2)]


def test_response_uses_reraise_bucket_after_opponent_voluntary_bet():
    memory={};strategy.initialize(AgentConfig(),memory)
    memory['counts'][3,1]=[1.,20.,1.]
    memory['counts'][3,2]=[20.,1.,1.]
    cache={'q':np.array([[.5,.5,.5,.5]])}
    first=SimpleNamespace(street=3,to_call=0,raises_this_street=0)
    raised=SimpleNamespace(street=3,to_call=10,raises_this_street=1)
    f1,r1=strategy.response_prob(first,memory,cache,10,.28)
    f2,r2=strategy.response_prob(raised,memory,cache,20,.28)
    assert f2[0]>f1[0]
