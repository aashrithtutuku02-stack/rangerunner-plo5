"""Retries and delayed events must not reopen hands or rewind learning."""
from dataclasses import replace
import numpy as np
import pytest

import agent
from game import Action,AgentConfig,Game,Street,make_deal


def fresh():
    memory={};agent.new_half(AgentConfig(time_bank_seconds=80.),memory)
    return memory


def forced_call(game,memory,hero):
    if game.to_act==hero:
        obs=game.observation(hero);agent.choose_action(obs,memory)
        memory['last']=(obs,Action.CHECK_CALL,memory['cache'])
    game.apply(Action.CHECK_CALL)


def completed_hand(memory,index=0):
    game=Game(make_deal('replay-events',index),0,index)
    while not game.is_terminal:forced_call(game,memory,0)
    last=memory['last'][0]
    result=game.hand_result(0);agent.on_hand_end(result,memory)
    return last,result


def assert_learning_unchanged(memory,before):
    assert memory.get('response_window')==before.get('response_window')
    np.testing.assert_array_equal(memory['counts'],before['counts'])
    np.testing.assert_array_equal(memory['models'],before['models'])
    assert memory['rng']==before['rng']
    assert memory['last'] is before['last']
    assert memory['cache'] is before['cache']
    assert memory['hands_played']==before['hands_played']


def snapshot(memory):
    result=dict(memory)
    result['counts']=memory['counts'].copy();result['models']=memory['models'].copy()
    return result


def test_duplicate_results_are_idempotent():
    memory=fresh();_,result=completed_hand(memory)
    before=snapshot(memory)
    agent.on_hand_end(result,memory)
    assert_learning_unchanged(memory,before)


def test_old_act_and_duplicate_result_cannot_reopen_a_completed_hand():
    memory=fresh();last,result=completed_hand(memory)
    before=snapshot(memory)
    assert agent.choose_action(last,memory) in last.legal_actions
    agent.on_hand_end(result,memory)
    assert_learning_unchanged(memory,before)


def test_replaying_a_shorter_history_does_not_rewind_or_double_count():
    memory=fresh();game=Game(make_deal('replay-prefix',0),0)
    old=game.observation(0)
    forced_call(game,memory,0);forced_call(game,memory,0);forced_call(game,memory,0)
    current=game.observation(0);agent.choose_action(current,memory)
    before=snapshot(memory)
    assert agent.choose_action(old,memory) in old.legal_actions
    assert_learning_unchanged(memory,before)
    agent.choose_action(current,memory)
    np.testing.assert_array_equal(memory['counts'],before['counts'])


def test_previous_hand_request_does_not_overwrite_a_current_hand():
    memory=fresh();old,result=completed_hand(memory,0)
    game=Game(make_deal('replay-events',1),0,1)
    obs=game.observation(0);agent.choose_action(obs,memory)
    before=snapshot(memory)
    assert agent.choose_action(old,memory) in old.legal_actions
    agent.on_hand_end(result,memory)
    assert_learning_unchanged(memory,before)


def test_new_half_clears_all_values_even_if_the_dictionary_is_reused():
    memory=fresh();completed_hand(memory)
    memory['unrelated_old_cache']='must not survive'
    agent.new_half(AgentConfig(time_bank_seconds=80.),memory)
    expected=fresh()
    assert memory.keys()==expected.keys()
    for k in expected:
        if isinstance(expected[k],np.ndarray):np.testing.assert_array_equal(memory[k],expected[k])
        else:assert memory[k]==expected[k]


def test_callback_without_a_live_observation_does_not_break_direct_startup():
    game=Game(make_deal('startup-callback',0),0)
    game.apply(Action.FOLD)
    memory={};agent.on_hand_end(game.hand_result(0),memory)
    obs=Game(make_deal('startup-callback',1),0,1).observation(0)
    assert agent.choose_action(obs,memory) in obs.legal_actions


def test_equivalent_card_ordering_reuses_the_same_samples():
    memory=fresh();game=Game(make_deal('order-retry',0),0)
    for _ in range(7):forced_call(game,memory,0)
    obs=game.observation(0);agent.choose_action(obs,memory)
    before=memory['rng'];cache=memory['cache']
    reordered=replace(obs,hole_cards=tuple(reversed(obs.hole_cards)),
                      board=tuple(reversed(obs.board[:3]))+obs.board[3:])
    assert agent.choose_action(reordered,memory) in obs.legal_actions
    assert memory['rng']==before and memory['cache'] is cache


def test_failed_new_observation_does_not_partially_change_learning():
    memory=fresh();completed_hand(memory)
    game=Game(make_deal('bad-observation',1),1,1)
    game.apply(Action.RAISE_HALF)
    obs=game.observation(0)
    bad=replace(obs,hole_cards=(obs.hole_cards[0],)*5)
    before=snapshot(memory)
    with pytest.raises(ValueError):agent.choose_action(bad,memory)
    assert_learning_unchanged(memory,before)
    assert agent.choose_action(obs,memory) in obs.legal_actions


def test_failed_result_can_be_retried_without_double_learning():
    memory=fresh();game=Game(make_deal('bad-result',0),0)
    for _ in range(7):forced_call(game,memory,0)
    obs=game.observation(0);agent.choose_action(obs,memory)
    memory['last']=(obs,Action.RAISE_POT,memory['cache'])
    game.apply(Action.RAISE_POT);game.apply(Action.CHECK_CALL)
    result=game.hand_result(0);before=snapshot(memory)
    bad=replace(result,opp_hole=(result.opp_hole[0],)*5)
    with pytest.raises(ValueError):agent.on_hand_end(bad,memory)
    assert_learning_unchanged(memory,before)
    agent.on_hand_end(result,memory)
    assert memory['hands_played']==1
    after=snapshot(memory);agent.on_hand_end(result,memory)
    assert_learning_unchanged(memory,after)


def test_a_conflicting_history_prefix_cannot_change_live_state():
    memory=fresh();game=Game(make_deal('conflicting-prefix',0),0)
    for _ in range(3):forced_call(game,memory,0)
    obs=game.observation(0);agent.choose_action(obs,memory)
    before=snapshot(memory)
    changed=(replace(obs.action_history[0],amount=obs.action_history[0].amount+1),)+obs.action_history[1:]
    bad=replace(obs,action_history=changed)
    assert agent.choose_action(bad,memory) in bad.legal_actions
    assert_learning_unchanged(memory,before)
