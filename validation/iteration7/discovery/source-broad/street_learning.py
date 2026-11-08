"""Research-only opponent learning with separate pre/postflop tendencies."""
import numpy as np


def revealed_ranks(m,obs,cache,cards):
    actual=np.zeros(4);actual[0]=m.engine.preflop_quality(cards)
    for street,n in ((1,3),(2,4),(3,5)):
        if len(obs.board)>=n:actual[street]=m.engine.score(cards,cache['board'][:n])
    q=np.zeros((1,4))
    for street,n in enumerate((0,3,4,5)):
        if len(obs.board)>=n:
            col=cache['values'][:,street]
            q[0,street]=((col<actual[street]).sum()+.5*(col==actual[street]).sum())/len(col)
    q[0,1]=.78*q[0,1]+.22*q[0,0]
    q[0,2]=.90*q[0,2]+.10*q[0,0]
    return q


def gated(m,memory,prior):
    observed=memory['counts'][1:,0,1:].sum(axis=0)-np.array([23.,13.])
    rate=(max(0.,observed[1])+4.)/(max(0.,observed.sum())+16.)
    gate=min(1.,max(0.,(rate-.20)/.20))
    effective=prior.copy();polar=m.SLOPES<0
    removed=float(effective[polar].sum())*(1-gate)
    effective[polar]*=gate
    effective[~polar]+=removed*prior[~polar]/max(1e-100,float(prior[~polar].sum()))
    return effective


def install(m,name):
    groups=np.array([0,1,2,3]) if name=='street-shrink' else np.array([0,1,1,1])
    initialize=m.initialize;weights=m.range_weights;finish=m._finish
    def initialize_groups(config,memory):
        initialize(config,memory)
        memory['global_models']=memory['models']
        memory['group_models']=np.tile(memory['models'],(int(groups.max())+1,1))
    def range_weights(obs,memory,cache):
        current=int(groups[int(obs.street)])
        prior=memory['group_models'][current]
        if name=='street-shrink':prior=.5*prior+.5*memory['global_models']
        memory['models']=prior
        if name!='street-mix':return weights(obs,memory,cache)
        events=m.history_events(obs,memory['config'].raise_cap)
        selected=[e for e in events if groups[int(e[1])]==current]
        rows=m.range_model.likelihoods(cache['q'],memory['counts'],m.range_model.event_array(selected),m.SLOPES)
        for other in range(len(memory['group_models'])):
            if other==current:continue
            previous=[e for e in events if groups[int(e[1])]==other]
            likelihood=m.range_model.likelihoods(cache['q'],memory['counts'],m.range_model.event_array(previous),m.SLOPES)
            likelihood/=np.maximum(likelihood.sum(axis=1)[:,None],1e-100)
            rows*=gated(m,memory,memory['group_models'][other])@likelihood
        rows/=np.maximum(rows.sum(axis=1)[:,None],1e-100)
        effective=gated(m,memory,prior)
        rows*=(effective/np.maximum(prior,1e-100))[:,None]
        return prior@rows,rows
    def finish_groups(result,memory):
        last=memory.get('last');memory['models']=memory['global_models']
        before=memory['models'];finish(result,memory)
        memory['global_models']=memory['models']
        if last is None or memory['models'] is before:return
        obs,action,cache=last
        events=m.history_events(obs,memory['config'].raise_cap)
        final=m.terminal_event(obs,action,result,memory['config'].raise_cap)
        if final is not None:events.append(final)
        combined=np.concatenate((cache['q'],revealed_ranks(m,obs,cache,np.asarray(result.opp_hole,dtype=np.int32))))
        updated=memory['group_models'].copy()
        for group in range(len(updated)):
            subset=[e for e in events if groups[int(e[1])]==group]
            if not subset:continue
            likelihood=m.range_model.likelihoods(combined,memory['counts'],m.range_model.event_array(subset),m.SLOPES)
            evidence=np.log(np.maximum(likelihood[:,-1],1e-100))-np.log(np.maximum(likelihood[:,:-1].mean(axis=1),1e-100))
            evidence-=evidence[0]
            posterior=updated[group]*np.exp(np.clip(evidence,-.6,.6))
            updated[group]=.985*posterior/posterior.sum()+.015/len(m.SLOPES)
        memory['group_models']=updated
    m.initialize=initialize_groups;m.range_weights=range_weights;m._finish=finish_groups
