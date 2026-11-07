from dataclasses import replace
import numpy as np
import strategy
from game import Action,AgentConfig,Game,Street,make_deal


def river(first=False):
    game=Game(make_deal('terminal-learning',0),0)
    for _ in range(6):game.apply(Action.CHECK_CALL)
    if not first:game.apply(Action.CHECK_CALL)
    return game


def test_final_call_event_uses_the_price_actually_offered():
    game=river();hero=game.to_act;obs=game.observation(hero)
    game.apply(Action.RAISE_POT);game.apply(Action.CHECK_CALL)
    event=strategy.terminal_event(obs,Action.RAISE_POT,game.hand_result(hero))
    assert event[:4]==(len(obs.action_history)+1,int(Street.RIVER),1,1)
    assert abs(event[4]-1/3)<1e-12


def test_final_fold_requires_matching_winner_pot_and_board():
    game=river();hero=game.to_act;obs=game.observation(hero)
    game.apply(Action.RAISE_POT);game.apply(Action.FOLD)
    result=game.hand_result(hero)
    assert strategy.terminal_event(obs,Action.RAISE_POT,result)[3]==0
    assert strategy.terminal_event(obs,Action.RAISE_POT,replace(result,pot=result.pot+2)) is None
    assert strategy.terminal_event(obs,Action.RAISE_POT,replace(result,winner='opp')) is None


def test_a_later_opponent_reraise_does_not_become_a_fabricated_fold():
    game=river();hero=game.to_act;obs=game.observation(hero)
    game.apply(Action.RAISE_HALF);game.apply(Action.RAISE_POT);game.apply(Action.FOLD)
    assert strategy.terminal_event(obs,Action.RAISE_HALF,game.hand_result(hero)) is None


def test_only_first_actor_can_have_a_missing_final_check():
    game=river(first=True);hero=game.to_act;obs=game.observation(hero)
    game.apply(Action.CHECK_CALL);game.apply(Action.CHECK_CALL)
    assert strategy.terminal_event(obs,Action.CHECK_CALL,game.hand_result(hero))[2:5]==(0,1,0.)
    game=river();hero=game.to_act;obs=game.observation(hero)
    game.apply(Action.CHECK_CALL)
    assert strategy.terminal_event(obs,Action.CHECK_CALL,game.hand_result(hero)) is None


def test_preflop_showdown_learning_includes_the_unseen_final_call(monkeypatch):
    game=Game(make_deal('preflop-terminal',0),0)
    for _ in range(3):game.apply(Action.RAISE_POT)
    hero=game.to_act;obs=game.observation(hero)
    memory={};strategy.initialize(AgentConfig(),memory)
    strategy.learn_actions(obs,memory)
    cache=strategy.cache_samples(obs,memory)
    memory['last']=(obs,Action.RAISE_POT,cache)
    game.apply(Action.RAISE_POT);game.apply(Action.CHECK_CALL)
    calls=[];original=strategy.range_model.likelihoods
    def capture(q,counts,events,slopes):
        calls.append(events.copy());return original(q,counts,events,slopes)
    monkeypatch.setattr(strategy.range_model,'likelihoods',capture)
    strategy.finish(game.hand_result(hero),memory)
    assert len(obs.board)==0 and calls
    assert tuple(calls[0][-1,:4])==(len(obs.action_history)+1,0,2,1)
    assert abs(calls[0][-1,4]-26/160)<1e-12
    assert calls[0][-1,5]==0
    assert memory['last'] is None and memory['cache'] is None
    assert np.all(np.isfinite(memory['models'])) and abs(memory['models'].sum()-1)<1e-12
