import numpy as np
import pytest

from game import Game,make_deal,Action,Street,AgentConfig
import river_search as river


def test_river_transitions_match_referee_for_every_reachable_numeric_state():
    front=[Game(make_deal('river-transition',0),0)]
    seen=set();checked=0
    while front:
        game=front.pop()
        if game.is_terminal:continue
        key=(game.street,game.to_act,tuple(game.stacks),tuple(game.bets),
             tuple(game.acted),game.last_increment,game.raises_this_street)
        if key in seen:continue
        seen.add(key)
        for action in game.legal_actions():
            child=game.clone();child.apply(action)
            if game.street==Street.RIVER:
                hero=game.to_act;opp=1-hero
                obs=game.observation(hero)
                state=river.state_from_observation(obs,{})
                for a in range(4):assert river.legal(state,a,4)==(a in obs.legal_actions)
                numeric,terminal=river.advance(state,int(action),2)
                assert bool(terminal)==child.is_terminal
                assert (terminal==2)==(action==Action.FOLD)
                assert numeric[0]==child.pot
                assert list(numeric[1:3])==[child.stacks[hero],child.stacks[opp]]
                assert list(numeric[3:5])==[child.bets[hero],child.bets[opp]]
                assert numeric[5]==child.raises_this_street
                assert max(numeric[6],2)==max(child.last_increment,2)
                assert numeric[11]==game.stacks[hero]-child.stacks[hero]
                if not child.is_terminal:
                    assert numeric[7]==int(child.to_act!=hero)
                    assert list(numeric[8:10])==[int(child.acted[hero]),int(child.acted[opp])]
                checked+=1
            if not child.is_terminal:front.append(child)
    assert checked>300


def test_search_chooses_one_action_for_the_entire_information_set():
    # Half the hidden hands win; calling costs 4 into a pot of 12.
    # Correct expectation is .5*16-4=4, not 6 from seeing folded cards.
    state=np.array([12,74,70,0,4,4,4,0,0,1,1,0],dtype=np.int64)
    mass=np.array([[.5,.5]])
    result=river.search(state,mass,np.array([.1,.9]),np.array([1.,0.]),
                        np.ones((3,3)),np.ones((3,2)),np.zeros(1),4,2)
    assert result==pytest.approx(4.)


@pytest.mark.parametrize('winner',[0.,.5,1.])
def test_final_call_value_is_exact_when_raising_is_capped(winner):
    state=np.array([40,70,50,0,20,4,10,0,0,1,1,0],dtype=np.int64)
    mass=np.ones((3,2))/6
    outcomes=np.full(2,winner)
    value=river.search(state,mass,np.array([.2,.8]),outcomes,np.ones((3,3)),
                       np.ones((3,2)),np.array([0.,8.,16.]),4,2,1)
    assert value==pytest.approx(60*winner-20)


def test_nuts_against_a_caller_choose_largest_value_bet():
    state=np.array([20,70,70,0,0,0,2,0,0,1,0,0],dtype=np.int64)
    mass=np.ones((3,2))/6
    counts=np.array([[0.,1.,0.],[0.,1.,0.],[0.,1.,0.]])
    values=[river.search(state,mass,np.array([.2,.8]),np.ones(2),counts,
                         np.ones((3,2)),np.array([0.,8.,16.]),4,2,a) for a in (1,2,3)]
    assert values==pytest.approx([20,30,40])


def test_response_branches_conserve_joint_probability_and_match_model():
    from range_model import action_prob
    rng=np.random.default_rng(7)
    q=rng.random(51);mass=rng.random((3,51));mass/=mass.sum()
    counts=np.array([[0.,7.,5.],[4.,6.,2.],[5.,5.,2.]])
    slopes=np.array([0.,8.,16.])
    state=np.array([30,60,70,10,0,2,10,1,1,0,0,10],dtype=np.int64)
    branches,context=river.response_mass(state,mass,q,counts,slopes,4)
    expected=action_prob(q[None,:],counts[context],slopes[:,None],True,.25)
    np.testing.assert_allclose(branches.sum(axis=0),mass,atol=1e-15)
    for branch,probability in zip(branches,expected):np.testing.assert_allclose(branch,mass*probability,atol=1e-15)


def test_complete_numeric_tree_payoffs_match_actual_referee_for_both_players():
    for hero in (0,1):
        game=Game(make_deal('river-payoffs',hero),button_seat=1-hero)
        while game.street!=Street.RIVER:game.apply(Action.CHECK_CALL)
        obs=game.observation(hero)
        state=river.state_from_observation(obs,{})
        start_contribution=game.contributed[hero]
        # Showdown outcome is used only to check numeric accounting in tests.
        checkdown=game.clone()
        while not checkdown.is_terminal:checkdown.apply(Action.CHECK_CALL)
        winner=checkdown.result().winner_seat
        outcome=.5 if winner is None else float(winner==hero)
        front=[(game,state)];leaves=0
        while front:
            g,x=front.pop()
            for a in range(4):assert river.legal(x,a,4)==(a in g.legal_actions())
            for a in g.legal_actions():
                child=g.clone();child.apply(a)
                y,terminal=river.advance(x,int(a),2)
                assert bool(terminal)==child.is_terminal
                assert y[0]==child.pot
                assert list(y[1:3])==[child.stacks[hero],child.stacks[1-hero]]
                assert list(y[3:5])==[child.bets[hero],child.bets[1-hero]]
                if child.is_terminal:
                    actual=river.terminal_value(y,np.ones((1,1)),np.array([outcome]),terminal==2)
                    assert actual==child.result().nets[hero]+start_contribution
                    leaves+=1
                else:
                    assert y[7]==int(child.to_act!=hero)
                    assert list(y[8:10])==[int(child.acted[hero]),int(child.acted[1-hero])]
                    front.append((child,y))
        assert leaves>50
