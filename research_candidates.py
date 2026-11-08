"""Discovery-only policy variants; production changes require held-out tests."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import math
import time
import numpy as np

import calibrated_model
from game import Action,Street
from opponents import incumbent_36ba


def clone(name):
    path=Path(__file__).with_name('opponents')/'incumbent_36ba.py'
    spec=importlib.util.spec_from_file_location('research_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def finish_complete(module,result,memory,bayes=False,decay=False):
    begin=time.perf_counter()
    last=memory.get('last')
    memory['hands_played']+=1
    if last is None or last[0].hand_index!=result.hand_index:return
    obs,action,cache=last
    events=module.history_events(obs)
    if action in (Action.RAISE_HALF,Action.RAISE_POT):
        context=2 if obs.to_call and obs.raises_this_street else 1
        response=1 if result.went_to_showdown else 0
        call=min(obs.opp_stack,obs.raise_to[action]-obs.opp_bet)
        invest=obs.raise_to[action]-obs.my_bet
        price=call/max(1,obs.pot+invest+call)
        events.append((len(obs.action_history)+1,int(obs.street),context,response,price))
        memory['counts'][int(obs.street),context,response]+=1
    elif (action==Action.CHECK_CALL and obs.to_call==0
          and obs.is_button==(obs.street==Street.PREFLOP) and result.went_to_showdown):
        events.append((len(obs.action_history)+1,int(obs.street),0,1,0.))
        memory['counts'][int(obs.street),0,1]+=1
    if not result.opp_hole and not bayes:
        memory['last']=None;memory['cache']=None
        memory['cpu']+=time.perf_counter()-begin
        return
    q=cache['q']
    if result.opp_hole:
        opp=np.array(result.opp_hole,dtype=np.int32)
        actual=np.zeros(4)
        actual[0]=module.engine.preflop_quality(opp)
        for s,n in ((1,3),(2,4),(3,5)):
            if len(obs.board)>=n:actual[s]=module.engine.score(opp,cache['board'][:n])
        aq=np.zeros((1,4))
        for s in range(4):
            if s==0 or len(obs.board)>=(0,3,4,5)[s]:
                col=cache['values'][:,s]
                aq[0,s]=((col<actual[s]).sum()+.5*(col==actual[s]).sum())/len(col)
        aq[0,1]=.78*aq[0,1]+.22*aq[0,0]
        aq[0,2]=.90*aq[0,2]+.10*aq[0,0]
        q=np.concatenate([q,aq])
    L=module.range_model.likelihoods(q,memory['counts'],module.range_model.event_array(events),module.SLOPES)
    if result.opp_hole:
        evidence=np.log(np.maximum(L[:,-1],1e-100))
        if not bayes:evidence-=np.log(np.maximum(L[:,:-1].mean(axis=1),1e-100))
    elif bayes:evidence=np.log(np.maximum(L.mean(axis=1),1e-100))
    else:evidence=np.zeros(len(module.SLOPES))
    evidence-=evidence[0]
    posterior=memory['models']*np.exp(np.clip(evidence,-.6,.6))
    memory['models']=.985*posterior/posterior.sum()+.015/len(posterior)
    if decay:memory['counts']*=.995
    memory['last']=None;memory['cache']=None
    memory['cpu']+=time.perf_counter()-begin


def make(name):
    if name=='release-f452':
        from opponents import release_f452 as previous
        return SimpleNamespace(new_half=previous.initialize,choose_action=previous.decide,on_hand_end=previous.finish,name=name)
    if name=='precision':
        from research_precision import make as precision_candidate
        return precision_candidate()
    if name in ('release-b15a','tree','tree-learn','tree-context','context-only','context-shrink'):
        from research_river import make as river_candidate
        return river_candidate(name)
    if name=='release':
        import strategy as current
        return SimpleNamespace(new_half=current.initialize,choose_action=current.decide,on_hand_end=current.finish,name=name)
    if name=='incumbent':m=incumbent_36ba
    else:m=clone(name)
    if name in ('calibrated','evidence','bayes','recent'):
        calibrated_model.warmup();m.range_model=calibrated_model;m.action_prob=calibrated_model.action_prob
    if name in ('bayes','recent'):
        original_response=m.response_prob
        def weights(obs,memory,cache):
            L=m.range_model.likelihoods(cache['q'],memory['counts'],m.range_model.event_array(m.history_events(obs)),m.SLOPES)
            posterior=memory['models']*L.mean(axis=1)
            posterior/=max(1e-100,posterior.sum())
            cache['current_models']=posterior
            L/=np.maximum(L.sum(axis=1)[:,None],1e-100)
            return posterior@L,L
        def response(obs,memory,cache,additional,price,model_weights=None):
            context=dict(memory);context['models']=cache.get('current_models',memory['models'])
            return original_response(obs,context,cache,additional,price,model_weights)
        m.range_weights=weights;m.response_prob=response
    if name in ('complete','calibrated','evidence','bayes','recent'):
        finish=lambda result,memory:finish_complete(m,result,memory,bayes=name in ('evidence','bayes','recent'),decay=name=='recent')
    else:finish=m.finish
    return SimpleNamespace(new_half=m.initialize,choose_action=m.decide,on_hand_end=finish,name=name)
