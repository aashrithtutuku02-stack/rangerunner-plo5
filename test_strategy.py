import agent
from game import Action, AgentConfig, Deal, Game


def test_extremely_weak_quads_can_fold_even_for_the_small_blind():
    # Four sixes consume four hole cards while Omaha permits only two.
    # The attractive blind price does not justify playing every starting hand.
    deal = Deal(((0, 1, 2, 3, 4), (5, 10, 15, 20, 25)), (6, 11, 16, 21, 26))
    obs = Game(deal, button_seat=0).observation(0)
    memory = {}
    agent.new_half(AgentConfig(), memory)
    assert agent.choose_action(obs, memory) == Action.FOLD
