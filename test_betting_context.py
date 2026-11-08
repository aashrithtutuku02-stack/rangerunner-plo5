from game import Game,make_deal,Street,Action,AgentConfig
from opponents import release_b15a
import betting_context


def river_game():
    game=Game(make_deal('context-test',0),0)
    while game.street!=Street.RIVER:game.apply(Action.CHECK_CALL)
    return game


def test_probe_after_a_check_has_a_distinct_frequency_bucket():
    game=river_game();hero=game.to_act
    game.apply(Action.CHECK_CALL);game.apply(Action.RAISE_HALF)
    obs=game.observation(hero)
    events=betting_context.refine_events(obs,release_b15a.history_events(obs))
    assert events[-1][2]==3


def test_checkraise_is_separate_from_an_ordinary_response_to_a_bet():
    game=river_game();hero=1-game.to_act
    game.apply(Action.CHECK_CALL)
    obs=game.observation(hero)
    assert betting_context.response_context(obs)==4
    game.apply(Action.RAISE_HALF);game.apply(Action.RAISE_HALF)
    obs=game.observation(hero)
    events=betting_context.refine_events(obs,release_b15a.history_events(obs))
    assert [e[2] for e in events if e[1]==3]==[0,4]
    assert betting_context.response_context(obs)==2


def test_checked_turn_does_not_change_the_river_context():
    game=river_game();hero=game.to_act
    obs=game.observation(hero)
    assert betting_context.response_context(obs)==1
    game.apply(Action.RAISE_HALF);game.apply(Action.RAISE_HALF)
    obs=game.observation(hero)
    events=betting_context.refine_events(obs,release_b15a.history_events(obs))
    assert events[-1][2]==1


def test_research_adapter_learns_probes_without_changing_open_counts():
    from research_candidates import make
    import numpy as np
    game=river_game();hero=game.to_act
    game.apply(Action.CHECK_CALL);game.apply(Action.RAISE_HALF)
    obs=game.observation(hero)
    policy=make('context-only')
    memory={};policy.new_half(AgentConfig(),memory)
    before=memory['counts'].copy()
    policy.choose_action(obs,memory)
    np.testing.assert_array_equal(memory['counts'][3,0],before[3,0])
    assert memory['counts'][3,3,2]==before[3,3,2]+1
    assert not np.shares_memory(memory['counts'][3,0],memory['counts'][3,3])


def test_contextual_prior_inherits_global_learning_but_yields_to_local_data():
    from research_candidates import make
    import numpy as np
    memory={};make('context-shrink').new_half(AgentConfig(),memory)
    raw=memory['counts'];raw[3,1,2]+=1000
    predicted=betting_context.shrink_counts(raw)
    np.testing.assert_allclose(predicted[3,4]/predicted[3,4].sum(),raw[3,1]/raw[3,1].sum())
    raw[3,4,1]+=1000
    predicted=betting_context.shrink_counts(raw)
    assert predicted[3,4,1]/predicted[3,4].sum()>.98


def test_research_context_adapter_can_complete_a_river_hand():
    from research_candidates import make
    policy=make('context-shrink');memory={};policy.new_half(AgentConfig(),memory)
    game=river_game();hero=game.to_act
    while not game.is_terminal:
        obs=game.observation(game.to_act)
        a=policy.choose_action(obs,memory) if game.to_act==hero else Action.CHECK_CALL
        assert a in obs.legal_actions
        game.apply(a)
    policy.on_hand_end(game.hand_result(hero),memory)
