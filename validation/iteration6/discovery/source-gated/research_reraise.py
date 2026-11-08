"""Opt-in re-raise experiments against a fully frozen 451b policy."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import reraise_ev


def make(name):
    assert name in ('reraise-full','reraise-half','reraise-river','reraise-optiongate','reraise-postflop')
    spec=importlib.util.spec_from_file_location('research_'+name,Path(__file__).with_name('opponents')/'release_451b.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    old=m.bet_ev;street=-1
    reraise_ev.warmup()
    def raise_values(*args):
        if name=='reraise-river' and street!=3:return old.raise_values(*args)
        if name=='reraise-postflop' and street==0:return old.raise_values(*args)
        blend=.5 if name=='reraise-half' else 1.
        if name=='reraise-optiongate' and street<3:
            frequency=args[5];rate=float(frequency[2]/frequency.sum())
            blend=min(1.,max(0.,(.70-rate)/.35))
        return reraise_ev.raise_values(*args,blend)
    m.bet_ev=SimpleNamespace(raise_values=raise_values)
    original=m._decide
    def decide(obs,memory):
        nonlocal street
        street=int(obs.street)
        return original(obs,memory)
    m._decide=decide
    return SimpleNamespace(new_half=m.initialize,choose_action=m.decide,on_hand_end=m.finish,name=name)
