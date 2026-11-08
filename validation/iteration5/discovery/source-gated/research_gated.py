"""Bound the polarized component using observed public betting aggression."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np


def make(name):
    spec=importlib.util.spec_from_file_location('research_'+name,Path(__file__).with_name('strategy.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    original=m.initialize
    def initialize(config,memory):
        original(config,memory)
        memory['models']=np.array([.08,.24,.48,.1,.1])
    m.initialize=initialize
    def weights(obs,memory,cache):
        events=m.history_events(obs,memory['config'].raise_cap)
        likelihood=m.range_model.likelihoods(cache['q'],memory['counts'],m.range_model.event_array(events),m.SLOPES)
        # Only uncapped free checks and bets are counted in this bucket.
        # Remove initialization pseudo-counts, then pool postflop actions.
        observed=memory['counts'][1:,0,1:].sum(axis=0)-np.array([23.,13.])
        rate=(max(0.,observed[1])+4.)/(max(0.,observed.sum())+16.)
        gate=min(1.,max(0.,(rate-.20)/.20))
        prior=memory['models'];effective=prior.copy()
        removed=float(effective[3:].sum())*(1-gate)
        effective[3:]*=gate
        effective[:3]+=removed*prior[:3]/max(1e-100,float(prior[:3].sum()))
        if name=='polar-gated':
            likelihood/=np.maximum(likelihood.sum(axis=1)[:,None],1e-100)
        normalizer=float(effective@likelihood.sum(axis=1))
        scaled=likelihood*(effective/np.maximum(prior,1e-100))[:,None]/max(1e-100,normalizer)
        return prior@scaled,scaled
    m.range_weights=weights
    return SimpleNamespace(new_half=initialize,choose_action=m.decide,on_hand_end=m.finish,name=name)
