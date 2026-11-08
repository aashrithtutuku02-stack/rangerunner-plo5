"""Resource test: force a longest legal line, while evaluating every bot turn.

Forced actions make this a counterfactual load test, not a strength benchmark.
Run inside a one-CPU container; HTTP/transport timing is tested separately.
"""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import numpy as np
import agent
from evaluator import omaha_score
from game import Action,AgentConfig,Game,make_deal


def longest_line():
    memo={}
    def solve(game):
        key=(game.street,game.to_act,tuple(game.stacks),tuple(game.bets),
             tuple(game.acted),game.last_increment,game.raises_this_street)
        if key in memo:return memo[key]
        best=()
        for action in game.legal_actions():
            child=game.clone();child.apply(action)
            path=(int(action),)+(solve(child) if not child.is_terminal else ())
            if (len(path),path[-1]==1)>(len(best),bool(best and best[-1]==1)):best=path
        memo[key]=best;return best
    with patch('game.omaha_score',lru_cache(maxsize=None)(omaha_score)):
        result=solve(Game(make_deal('longest-line-discovery',0),0))
    assert len(result)==14 and result[-1]==Action.CHECK_CALL
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--hands',type=int,default=1000);a=p.parse_args()
    sources=['strategy.py','bet_ev.py','game.py','evaluator.py','fast_engine.py','preflop.npz',
             'native/plo5_fast_linux_x86_64.so','tools/worst_line_load.py']
    fingerprints={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources}
    actions=longest_line();memories=[{},{}];config=AgentConfig(num_hands=a.hands)
    for memory in memories:agent.new_half(config,memory)
    costs=[0.,0.];max_call=0.;sizes=[Counter(),Counter()];started=time.perf_counter()
    for i in range(a.hands):
        game=Game(make_deal('iteration4-longest-load',i),i%2,i)
        for forced in actions:
            seat=game.to_act;obs=game.observation(seat);memory=memories[seat]
            begin=time.perf_counter();chosen=agent.choose_action(obs,memory)
            elapsed=time.perf_counter()-begin;costs[seat]+=elapsed;max_call=max(max_call,elapsed)
            assert chosen in obs.legal_actions and forced in obs.legal_actions
            sizes[seat][len(memory['cache']['outcomes'])]+=1
            memory['last']=(obs,Action(forced),memory['cache'])
            game.apply(forced)
        assert game.is_terminal and game.result().went_to_showdown
        for seat,memory in enumerate(memories):
            begin=time.perf_counter();agent.on_hand_end(game.hand_result(seat),memory)
            elapsed=time.perf_counter()-begin;costs[seat]+=elapsed;max_call=max(max_call,elapsed)
            assert np.all(np.isfinite(memory['models'])) and abs(memory['models'].sum()-1)<1e-12
    assert all(m['hands_played']==a.hands and len(m['completed_hands'])==a.hands for m in memories)
    assert max_call<1.,'One call exceeded the tournament request deadline'
    assert max(costs)<8.,'One policy exceeded its calculation bank'
    assert fingerprints=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources}
    print(json.dumps(dict(hands=a.hands,forced_actions=[Action(v).name for v in actions],
        policy_calculation_seconds=costs,max_call_seconds=max_call,sample_counts=sizes,
        elapsed_seconds=time.perf_counter()-started,source_sha256=fingerprints,
        scope='Counterfactual function load under container resources; excludes HTTP transport'),indent=2))


if __name__=='__main__':main()
