from itertools import permutations
import random

import agent
import fast_engine as engine
from evaluator import omaha_score
from game import Action,AgentConfig,Game,make_deal
from scenario_sweep import cases


def test_named_card_scenarios_have_the_claimed_rankings():
    c=cases()
    winners={'nut_flush':0,'wheel':0,'quads':0,'split':None,'four_board':None,'four_hole':1,'flush_fullhouse':0}
    for name,winner in winners.items():
        d=c[name];a=omaha_score(d.hole_cards[0],d.board);b=omaha_score(d.hole_cards[1],d.board)
        assert (None if a==b else 0 if a>b else 1)==winner,name
        assert engine.score(d.hole_cards[0],d.board)==a
        assert engine.score(d.hole_cards[1],d.board)==b
    assert engine.score(c['wheel'].hole_cards[0],c['wheel'].board)>>20==3
    assert engine.score(c['four_board'].hole_cards[0],c['four_board'].board)>>20==4
    d=c['flush_fullhouse']
    assert engine.score(d.hole_cards[0],d.board)>>20==6
    assert engine.score(d.hole_cards[1],d.board)>>20==5


def test_card_order_and_all_suit_renamings_preserve_exact_omaha_scores():
    for d in cases().values():
        for h in d.hole_cards:
            expected=engine.score(h,d.board)
            for permuted in permutations(h):assert engine.score(permuted,d.board)==expected
            for flop in permutations(d.board[:3]):assert engine.score(h,flop+d.board[3:])==expected
            for suits in permutations(range(4)):
                rename=lambda cards:tuple((v&~3)|suits[v&3] for v in cards)
                assert engine.score(rename(h),rename(d.board))==expected


def test_unseen_opponent_cards_and_future_board_cannot_change_a_decision():
    # Alter only information absent from the public observation.
    d=make_deal('hidden-information',0);rng=random.Random(881)
    for button in (0,1):
        for street in range(4):
            game=Game(d,button)
            while int(game.street)<street:game.apply(Action.CHECK_CALL)
            if game.to_act!=button:game.apply(Action.CHECK_CALL)
            original=game.observation(button)
            m={};agent.new_half(AgentConfig(time_bank_seconds=80.),m)
            expected=agent.choose_action(original,m)
            for _ in range(24):
                available=[v for v in range(36) if v not in d.hole_cards[button]+original.board]
                other=rng.sample(available,10-len(original.board))
                hands=list(d.hole_cards);hands[1-button]=tuple(other[:5])
                changed=game.clone();changed.deal=type(d)(tuple(hands),original.board+tuple(other[5:]))
                obs=changed.observation(button)
                assert obs.to_dict()==original.to_dict()
                memory={};agent.new_half(AgentConfig(time_bank_seconds=80.),memory)
                assert agent.choose_action(obs,memory)==expected
