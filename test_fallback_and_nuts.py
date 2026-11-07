import json
import os
import subprocess
import sys
import numpy as np

import agent
import fast_engine as e
from evaluator import cards_from_str
from game import Action,AgentConfig,Deal,Game


def test_forced_numba_fallback_matches_native_samples():
    code='''import json,numpy as np,fast_engine as e
e.warm_engine()
h=np.array([0,5,10,15,20],dtype=np.int32)
b=np.array([3,8,13,18,23],dtype=np.int32)
r=e.simulate(h,b,64,np.uint64(12345))
print(json.dumps(dict(backend=e.BACKEND,hands=r[0].tolist(),values=r[1].tolist(),outcomes=r[2].tolist(),state=int(r[-1]))))
'''
    env=dict(os.environ,RANGERUNNER_ENGINE='numba',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    reply=subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,text=True,timeout=40,check=True)
    actual=json.loads(reply.stdout)
    expected=e.simulate([0,5,10,15,20],[3,8,13,18,23],64,np.uint64(12345))
    assert actual['backend']=='Numba'
    np.testing.assert_array_equal(actual['hands'],expected[0])
    np.testing.assert_array_equal(actual['values'],expected[1])
    np.testing.assert_array_equal(actual['outcomes'],expected[2])
    assert actual['state']==int(expected[-1])


def test_unbeatable_flush_has_equity_one_and_is_never_folded():
    hole=tuple(cards_from_str('AhKhTcTdJs'))
    board=tuple(cards_from_str('6h9hQh7c8d'))
    # The only three hearts on board span too many ranks for a straight
    # flush; the unpaired board cannot make quads. Both top hearts are ours.
    result=e.simulate(hole,board,2048,np.uint64(11111))
    assert np.all(result[2]==1.0)
    opp=tuple(cards_from_str('AcAdKcKdQc'))
    game=Game(Deal((hole,opp),board),button_seat=0)
    for _ in range(6):game.apply(Action.CHECK_CALL)
    game.apply(Action.RAISE_POT)
    obs=game.observation(game.to_act)
    assert game.to_act==0 and len(obs.board)==5 and obs.to_call>0
    memory={};agent.new_half(AgentConfig(),memory)
    assert agent.choose_action(obs,memory)!=Action.FOLD
