import numpy as np
import pytest
import agent
from game import AgentConfig,Game,Action,make_deal


@pytest.mark.parametrize('street',[0,1,2,3])
@pytest.mark.parametrize('spent,scale',[(.64,1.),(.67,.5),(.90,0.)])
def test_budget_regimes_choose_legal_actions_with_expected_sample_sizes(street,spent,scale):
    game=Game(make_deal('budget-states',street),0,200)
    while int(game.street)<street:game.apply(Action.CHECK_CALL)
    memory={};agent.new_half(AgentConfig(),memory)
    memory['cpu']=spent
    obs=game.observation(game.to_act)
    assert agent.choose_action(obs,memory) in obs.legal_actions
    base=1280 if street==3 else 768
    expected=int(base*scale) if scale else 192
    assert len(memory['cache']['outcomes'])==expected
    assert np.all(np.isfinite(memory['counts'])) and np.all(np.isfinite(memory['models']))


def test_existing_samples_are_reused_when_the_budget_drops():
    memory={};agent.new_half(AgentConfig(),memory)
    obs=Game(make_deal('cached-budget',0),0,200).observation(0)
    agent.choose_action(obs,memory);cache=memory['cache'];rng=memory['rng']
    memory['cpu']=7.
    assert agent.choose_action(obs,memory) in obs.legal_actions
    assert memory['cache'] is cache and memory['rng']==rng
