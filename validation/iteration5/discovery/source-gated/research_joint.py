"""Research-only conditioning of the model mixture on the current history."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np


def make(name):
    spec=importlib.util.spec_from_file_location('research_'+name,Path(__file__).with_name('strategy.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    def weights(obs,memory,cache):
        events=m.history_events(obs,memory['config'].raise_cap)
        likelihood=m.range_model.likelihoods(cache['q'],memory['counts'],m.range_model.event_array(events),m.SLOPES)
        # A single normalizer conditions both hand and model on observed
        # actions. The downstream joint kernel multiplies by the model prior.
        normalizer=float(memory['models']@likelihood.sum(axis=1))
        scaled=likelihood/max(1e-100,normalizer)
        return memory['models']@scaled,scaled
    m.range_weights=weights
    if name=='polar-joint-prior':
        original=m._finish
        def finish(result,memory):
            before=memory['models']
            original(result,memory)
            if memory['models'] is not before:
                memory['models']=memory['models']-.015/len(m.SLOPES)+.015*np.array([.1,.2,.5,.1,.1])
        m._finish=finish
    return SimpleNamespace(new_half=m.initialize,choose_action=m.decide,on_hand_end=m.finish,name=name)
