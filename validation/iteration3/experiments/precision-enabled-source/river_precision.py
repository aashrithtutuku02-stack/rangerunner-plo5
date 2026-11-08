"""Spend spare calculation time on uncertain river calls, once per board."""
import numpy as np
import fast_engine as engine

INITIAL_STATE=np.uint64(0xD1B54A32D192ED03)


def initialize(memory):
    memory['precision_rng']=INITIAL_STATE


def needs_more(obs,memory,cache,weights):
    if len(obs.board)!=5 or obs.to_call<=0 or len(cache['outcomes'])!=1280:return False
    config=memory['config']
    pace=memory['cpu']/max(30,obs.hand_index+1)
    target=.40*config.time_bank_seconds/max(1,config.num_hands)
    if pace>target or memory['cpu']>.55*config.time_bank_seconds:return False
    equity=float(weights@cache['outcomes'])
    error=float(np.sqrt(np.sum(weights**2*(cache['outcomes']-equity)**2)))
    call=min(obs.to_call,obs.my_stack)
    price=call/max(1,obs.pot+call)
    return abs(equity-price)<max(.015,1.5*error)


def extend(memory,cache,target=4096):
    """Append uniform draws from a separate, reset-per-half random stream."""
    if len(cache['board'])!=5:raise ValueError('River precision requires five visible board cards')
    extra=target-len(cache['outcomes'])
    if extra<=0:return cache
    hands,values,outcomes,future,rng=engine.simulate(cache['hole'],cache['board'],extra,
                        memory.get('precision_rng',INITIAL_STATE))
    memory['precision_rng']=np.uint64(rng)
    cache['hands']=np.concatenate((cache['hands'],hands))
    cache['values']=np.concatenate((cache['values'],values))
    cache['outcomes']=np.concatenate((cache['outcomes'],outcomes))
    q=engine.percentiles(cache['values'])
    q[:,1]=.78*q[:,1]+.22*q[:,0]
    q[:,2]=.90*q[:,2]+.10*q[:,0]
    cache['q']=q
    return cache
