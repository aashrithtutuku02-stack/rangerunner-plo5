"""Frozen-release adapter for testing selective extra river sampling."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import river_precision


def make():
    spec=importlib.util.spec_from_file_location('precision_policy',Path(__file__).with_name('opponents')/'release_b15a.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    original=m.cache_samples
    def cache(obs,memory):
        result=original(obs,memory)
        if len(obs.board)==5 and obs.to_call>0:
            weights,_=m.range_weights(obs,memory,result)
            if river_precision.needs_more(obs,memory,result,weights):river_precision.extend(memory,result)
        return result
    m.cache_samples=cache
    def initialize(config,memory):
        m.initialize(config,memory);river_precision.initialize(memory)
    return SimpleNamespace(new_half=initialize,choose_action=m.decide,on_hand_end=m.finish,name='precision')
