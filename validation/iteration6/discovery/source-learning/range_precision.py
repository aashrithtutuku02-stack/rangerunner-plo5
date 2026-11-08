"""Bounded extra sampling for uncertain calls against sparse weighted ranges."""
import math
import numpy as np
import fast_engine as engine

INITIAL_STATE=np.uint64(0xD1B54A32D192ED03)
TARGET=4096
LIMIT=64


def refine(obs,memory,cache,weights,models,reweight,min_street=1):
    original=(cache,weights,models)
    if int(obs.street)<min_street or not obs.to_call or len(cache['outcomes'])>=TARGET:return original
    if memory.get('precision_used',0)>=LIMIT or memory['cpu']>.60*memory['config'].time_bank_seconds:return original
    ess=1/max(1e-100,float(weights@weights))
    if ess>=96:return original
    equity=float(weights@cache['outcomes'])
    call=min(obs.to_call,obs.my_stack);price=call/max(1,obs.pot+call)
    variance=float(weights@((cache['outcomes']-equity)**2))
    distance=min(.12,.04+1.5*math.sqrt(max(0.,variance)/ess))
    if abs(equity-price)>distance:return original
    state=memory.get('precision_rng',INITIAL_STATE)
    extra=engine.simulate(cache['hole'],cache['board'],TARGET-len(weights),state)
    updated=dict(cache)
    for name,tail in zip(('hands','values','outcomes'),extra[:3]):
        updated[name]=np.concatenate((cache[name],tail))
    q=engine.percentiles(updated['values'])
    if len(cache['board'])>=3:q[:,1]=.78*q[:,1]+.22*q[:,0]
    if len(cache['board'])>=4:q[:,2]=.90*q[:,2]+.10*q[:,0]
    updated['q']=q
    new_weights,new_models=reweight(obs,memory,updated)
    # Copy-on-write: a failed expansion must not mutate the cached arrays
    # held by the caller's rollback snapshot or consume its auxiliary stream.
    memory['cache']=updated;memory['precision_rng']=np.uint64(extra[-1])
    memory['precision_used']=memory.get('precision_used',0)+1
    return updated,new_weights,new_models
