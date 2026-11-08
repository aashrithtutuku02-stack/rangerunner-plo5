"""Enumerate every legal betting history for fixed cards and the supplied rules.

The public referee is the transition oracle. Distinct histories are never merged.
Only its pure terminal card evaluator is memoized, keyed by exact input cards.
"""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import time
from unittest.mock import patch

import numpy as np
import agent
import strategy
from evaluator import cards_from_str,omaha_score
from game import Action,AgentConfig,Deal,Game,make_deal


def cases():
    named={
        'nut_flush':('AhKhTcTdJs','AcAdKcKdQc','6h9hQh7c8d'),
        'wheel':('Ah6d6h6sKc','AsAcKdKhKs','7c8d9hTdQd'),
        'quads':('AhAsKhQhJh','KcKdQdJdTd','AcAd6h7s8c'),
        'split':('AhAdKhKdQs','AcAsKcKsQd','6c7d8h9sTc'),
        'four_board':('AhKhQhJhTh','AdKdQdJdTd','6c6d6h6sAc'),
        'four_hole':('6c6d6h6s7c','AhAdKhKdQh','8c9dThJsQc'),
        'flush_fullhouse':('KhQhJdTc6c','Ac9c9dKd6d','AhAd9h8h7c'),
    }
    result={'random':make_deal('scenario-cards',0)}
    for name,(h0,h1,board) in named.items():
        result[name]=Deal((tuple(cards_from_str(h0)),tuple(cards_from_str(h1))),tuple(cards_from_str(board)))
    for d in result.values():
        cards=d.hole_cards[0]+d.hole_cards[1]+d.board
        assert len(cards)==15 and len(set(cards))==15
    return result


def clone_memory(memory):
    copied=dict(memory)
    copied['counts']=memory['counts'].copy();copied['models']=memory['models'].copy()
    copied['completed_hands']=memory['completed_hands'].copy()
    return copied


def expected_counts(prior,events):
    """Interpret independently recorded referee opportunities, in event order."""
    expected=prior.copy()
    for _,street,context,action,_,available in events:
        cell=expected[street,context]
        if available or action==Action.FOLD:cell[min(action,2)]+=1
        elif action==Action.CHECK_CALL and context:
            # A forced call observes the union of call and raise preferences.
            proportions=cell[1:]/cell[1:].sum()
            cell[1:]+=proportions
    return expected


def sweep(name,deal,button,full_policy=True):
    started=time.perf_counter();config=AgentConfig(num_hands=1,time_bank_seconds=80.)
    sources=['agent.py','strategy.py','range_model.py','bet_ev.py','reraise_ev.py','fast_engine.py','equity_engine.py',
             'game.py','evaluator.py','preflop.npz','native/plo5_fast_linux_x86_64.so','scenario_sweep.py']
    root=Path(__file__).parent
    fingerprints={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in sources}
    memories=[{},{}]
    for memory in memories:agent.new_half(config,memory)
    prior=memories[0]['counts'].copy()
    totals=Counter();streets=Counter();endings=Counter();samples=Counter()
    numeric=set();trace=hashlib.sha256();max_decision=0.

    def checked_counts(memory,events):
        np.testing.assert_allclose(memory['counts'],expected_counts(prior,events),atol=1e-10,rtol=0)
        assert np.all(np.isfinite(memory['models'])) and abs(memory['models'].sum()-1)<1e-12
        assert memory['rng']!=0
        totals['learning_checks']+=1

    def visit(game,memories,events,raised,path):
        nonlocal max_decision
        actor=game.to_act;other=1-actor
        obs=game.observation(actor);current=clone_memory(memories[actor])
        numeric.add((int(game.street),actor,tuple(game.stacks),tuple(game.bets),
                     tuple(game.acted),game.last_increment,game.raises_this_street))
        assert strategy.history_events(obs)==list(events[actor])
        totals['history_prefixes']+=1;streets[int(obs.street)]+=1
        if full_policy:
            begin=time.perf_counter();chosen=agent.choose_action(obs,current)
            max_decision=max(max_decision,time.perf_counter()-begin)
            assert chosen in obs.legal_actions
            cache=current['cache'];size=len(cache['outcomes']);samples[size]+=1
            assert size==(1280 if len(obs.board)==5 else 768)
            assert np.all(np.isfinite(cache['q'])) and np.all((cache['q']>=0)&(cache['q']<=1))
            # Repeating the same request must preserve learning and sampling.
            before_counts=current['counts'].copy();before_rng=current['rng']
            repeated=agent.choose_action(obs,current)
            assert repeated==chosen and current['rng']==before_rng and current['cache'] is cache
            np.testing.assert_array_equal(current['counts'],before_counts)
            totals['replayed_decisions']+=1
        else:
            strategy.learn_actions(obs,current);cache=None
        checked_counts(current,events[actor])
        for action in game.legal_actions():
            child=game.clone();child.apply(action)
            updated=list(memories);updated[actor]=clone_memory(current)
            updated[actor]['last']=(obs,action,cache)
            context=0 if not obs.to_call else 2 if raised[actor] else 1
            event=(len(game.history),int(obs.street),context,int(action),
                   obs.to_call/max(1,obs.pot+obs.to_call),int(Action.RAISE_HALF in obs.legal_actions))
            next_events=list(events);next_events[other]=events[other]+(event,)
            next_path=path+(int(action),);totals['edges']+=1
            if child.is_terminal:
                totals['terminal_histories']+=1
                totals['max_actions']=max(totals['max_actions'],len(next_path))
                result=child.result();assert sum(result.nets)==0
                endings[('showdown' if result.went_to_showdown else 'fold')+'_'+str(int(obs.street))]+=1
                trace.update(bytes(next_path)+b'|')
                for seat in (0,1):
                    memory=clone_memory(updated[seat]);last=memory['last']
                    known=next_events[seat] if last is not None else ()
                    unseen=[ev for ev in known if ev[0]>=memory['seen_count']]
                    inferred=strategy.terminal_event(last[0],last[1],child.hand_result(seat)) if last else None
                    assert len(unseen)<=1
                    if unseen:
                        assert inferred is not None
                        np.testing.assert_allclose(inferred,unseen[0],rtol=0,atol=1e-12)
                    else:assert inferred is None
                    totals['terminal_inference_checks']+=1
                    if full_policy:
                        agent.on_hand_end(child.hand_result(seat),memory)
                        assert memory['hands_played']==1 and memory['last'] is None and memory['cache'] is None
                        assert memory['completed_hands']=={0}
                        checked_counts(memory,known)
                        before=memory['counts'].copy();models=memory['models'].copy()
                        agent.on_hand_end(child.hand_result(seat),memory)
                        np.testing.assert_array_equal(memory['counts'],before)
                        np.testing.assert_array_equal(memory['models'],models)
                        assert memory['hands_played']==1
                        totals['duplicate_results']+=1
                continue
            flags=list(raised)
            if action in (Action.RAISE_HALF,Action.RAISE_POT):flags[actor]=True
            if child.street!=game.street:flags=[False,False]
            visit(child,updated,tuple(next_events),tuple(flags),next_path)

    with patch('game.omaha_score',lru_cache(maxsize=None)(omaha_score)):
        visit(Game(deal,button),memories,((),()),(False,False),())
    assert totals['terminal_histories']==25538 and totals['history_prefixes']==15952
    assert totals['edges']==41489 and totals['max_actions']==14 and len(numeric)==678
    assert fingerprints=={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in sources},'Source changed during sweep'
    return dict(case=name,button=button,mode='full_policy' if full_policy else 'accounting_only',
                totals=dict(totals),unique_numeric_states=len(numeric),prefixes_by_street=dict(streets),
                endings=dict(endings),sample_counts=dict(samples),sequence_sha256=trace.hexdigest(),
                max_decision_seconds=max_decision,elapsed_seconds=time.perf_counter()-started,
                cards=dict(hole_cards=deal.hole_cards,board=deal.board),
                source_sha256=fingerprints)


def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',nargs='+',default=['all'])
    p.add_argument('--buttons',nargs='+',type=int,default=[0,1]);p.add_argument('--output',required=True)
    p.add_argument('--accounting-only',action='store_true');a=p.parse_args()
    selected=cases();names=list(selected) if a.cases==['all'] else a.cases
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    for name in names:
        for button in a.buttons:
            report=sweep(name,selected[name],button,not a.accounting_only)
            (out/f'{name}-button{button}.json').write_text(json.dumps(report,indent=2)+'\n')
            print(name,'button',button,report['totals'],round(report['elapsed_seconds'],2),'seconds',flush=True)


if __name__=='__main__':main()
