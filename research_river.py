"""Discovery adapters for the frozen b15a release and bounded river search."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import time
import numpy as np

from game import Action,Street
import river_search
import betting_context


def make(name):
    from opponents import release_b15a
    if name=='release-b15a':
        return SimpleNamespace(new_half=release_b15a.initialize,choose_action=release_b15a.decide,
                               on_hand_end=release_b15a.finish,name=name)
    spec=importlib.util.spec_from_file_location('river_'+name,Path(__file__).with_name('opponents')/'release_b15a.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    river_search.warmup()
    contextual=name in ('tree-context','context-only','context-shrink')
    shrink=name=='context-shrink'
    if shrink:
        helper=m.range_model
        m.range_model=SimpleNamespace(event_array=helper.event_array,action_prob=helper.action_prob,
            likelihoods=lambda q,counts,events,slopes:helper.likelihoods(q,betting_context.shrink_counts(counts),events,slopes))
    original_history=m.history_events
    original_response=m.response_prob
    if contextual:
        m.history_events=lambda obs,raise_cap=4:betting_context.refine_events(obs,original_history(obs,raise_cap))
        original_terminal=m.terminal_event
        def terminal(obs,action,result,raise_cap=4):
            event=original_terminal(obs,action,result,raise_cap)
            if event is not None and int(obs.street)==3:
                event=list(event)
                if action in (Action.RAISE_HALF,Action.RAISE_POT):event[2]=betting_context.response_context(obs)
                else:event[2]=3
                return tuple(event)
            return event
        m.terminal_event=terminal
        def response(obs,memory,cache,additional,price,model_weights=None):
            context=betting_context.response_context(obs)
            if shrink:
                memory=dict(memory);memory['counts']=betting_context.shrink_counts(memory['counts'])
            if context==4:
                memory=dict(memory);memory['counts']=memory['counts'].copy()
                memory['counts'][3,1]=memory['counts'][3,4]
            return original_response(obs,memory,cache,additional,price,model_weights)
        m.response_prob=response
    original_observe=m.observe_event
    def observe(memory,event):
        if name in ('tree-learn','tree-context') and event[3]>=2:
            memory['sizes'][event[1],event[2],event[3]-2]+=1
        original_observe(memory,event)
        if shrink and event[2] in (3,4):
            parent=list(event);parent[2]=0 if event[2]==3 else 1
            original_observe(memory,tuple(parent))
    m.observe_event=observe
    def initialize(config,memory):
        m.initialize(config,memory)
        if contextual:memory['counts']=np.concatenate((memory['counts'],memory['counts'][:,[0,1],:]),axis=1)
        memory['sizes']=np.tile(np.array([1.,3.]),(4,5 if contextual else 3,1))
    def decide(obs,memory):
        action=m.decide(obs,memory)
        if obs.street==Street.RIVER and name not in ('context-only','context-shrink'):
            begin=time.perf_counter()
            cache=memory['cache'];_,models=m.range_weights(obs,memory,cache)
            values=river_search.action_values(obs,memory,cache,models)
            action=Action.CHECK_CALL
            if obs.to_call and values[0]>values[1]:action=Action.FOLD
            best=values[int(action)]
            for candidate in (Action.RAISE_HALF,Action.RAISE_POT):
                if values[int(candidate)]>best+.025*obs.pot+.08:
                    action=candidate;best=values[int(candidate)]
            memory['last']=(obs,action,cache)
            memory['cpu']+=time.perf_counter()-begin
        return action
    return SimpleNamespace(new_half=initialize,choose_action=decide,on_hand_end=m.finish,name=name)
