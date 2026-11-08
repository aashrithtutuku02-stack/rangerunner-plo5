import hashlib,json,sys,importlib.metadata
from pathlib import Path
sys.path.insert(0,'/app')
import agent,strategy,fast_engine,calling_read
from game import AgentConfig,Game,make_deal
import numpy as np
memory={};agent.new_half(AgentConfig(),memory)
obs=Game(make_deal('runtime-model-identity',0),0).observation(0)
_,rows=strategy.range_weights(obs,memory,{'q':np.ones((2,4))*.5})
names=['agent.py','strategy.py','calling_read.py','range_model.py','bet_ev.py','fast_engine.py','equity_engine.py','game.py','evaluator.py','preflop.npz','native/plo5_fast.c','native/plo5_fast_linux_x86_64.so']
research=[n for n in sys.modules if n.startswith(('research_','river_precision','river_search','betting_context','polar_model','polar_bet_ev','reraise_ev','range_precision','model_learning','street_learning'))]
assert agent.PARTICIPANT=='winner' and agent.AGENT_NAME=='RangeRunner'
assert not research and fast_engine.BACKEND=='portable C'
assert all(n in memory for n in ('seen_history','completed_hands','last_completed'))
assert memory['response_window']==() and not calling_read.confident_caller(memory['response_window'])
print(json.dumps(dict(participant=agent.PARTICIPANT,agent_name=agent.AGENT_NAME,backend=fast_engine.BACKEND,research_imports=research,lifecycle_guards_initialized=True,calling_read_initialized=True,calling_read_window=calling_read.WINDOW,calling_read_min_responses=calling_read.MIN_RESPONSES,slopes=strategy.SLOPES.tolist(),nominal_model_weights=memory['models'].tolist(),initial_effective_model_weights=(memory['models']*rows.sum(axis=1)).tolist(),packages={n:importlib.metadata.version(n) for n in ('numpy','numba','fastapi','uvicorn')},source_sha256={n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in names}),indent=2))
