"""Precision experiments using the frozen released betting policy."""
import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace
import range_precision


def make(name):
    assert name in ('ess-postflop','ess-river')
    path=Path(__file__).with_name('opponents')/'release_451b.py'
    spec=importlib.util.spec_from_file_location('research_'+name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    original=m.initialize
    def initialize(config,memory):
        original(config,memory)
        memory.update(precision_rng=range_precision.INITIAL_STATE,precision_used=0)
    m.initialize=initialize
    m.refine_range=lambda obs,memory,cache,weights,models:range_precision.refine(
        obs,memory,cache,weights,models,m.range_weights,3 if name=='ess-river' else 1)
    source=inspect.getsource(m._decide)
    needle="    outcomes = cache['outcomes']"
    assert source.count(needle)==1
    source=source.replace(needle,"    cache, weights, models = refine_range(obs,memory,cache,weights,models)\n"+needle)
    exec(compile(source,str(path)+'::'+name,'exec'),m.__dict__)
    return SimpleNamespace(new_half=initialize,choose_action=m.decide,on_hand_end=m.finish,name=name)
