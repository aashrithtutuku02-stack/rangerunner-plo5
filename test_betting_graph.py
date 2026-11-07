"""Exercise every reachable numeric betting state for a fixed legal deal."""
import numpy as np
import agent
from game import AgentConfig,Game,make_deal,Action,Street


def test_every_reachable_betting_state_produces_a_legal_finite_decision():
    front=[Game(make_deal('betting-graph',0),0)]
    seen=set();streets=set();cap=False;allin=False;same_raise=False;longest=0
    while front:
        game=front.pop()
        if game.is_terminal:continue
        key=(game.street,game.to_act,tuple(game.stacks),tuple(game.bets),
             tuple(game.acted),game.last_increment,game.raises_this_street)
        if key in seen:continue
        seen.add(key)
        obs=game.observation(game.to_act)
        memory={};agent.new_half(AgentConfig(),memory)
        action=agent.choose_action(obs,memory)
        assert action in obs.legal_actions
        assert np.all(np.isfinite(memory['counts']))
        assert np.all(np.isfinite(memory['models']))
        streets.add(obs.street);longest=max(longest,len(obs.action_history))
        cap|=obs.raises_this_street==4
        allin|=obs.opp_stack==0
        same_raise|=(Action.RAISE_HALF in obs.raise_to and
                     obs.raise_to[Action.RAISE_HALF]==obs.raise_to[Action.RAISE_POT])
        for legal in obs.legal_actions:
            child=game.clone();child.apply(legal)
            if not child.is_terminal:front.append(child)
    assert len(seen)==678
    assert streets==set(Street)
    assert cap and allin and same_raise and longest>=12
