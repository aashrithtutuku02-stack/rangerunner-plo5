"""Street-specific learning and raise-ranking experiments on frozen 9efa."""
import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace
import numpy as np


def make(name):
    assert name in ('margin-once','margin-none','street-split','street-shrink','street-mix')
    path=Path(__file__).with_name('opponents')/'release_9efa.py'
    spec=importlib.util.spec_from_file_location('research_'+name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if name.startswith('margin-'):
        source=inspect.getsource(m._decide)
        needle='    for index,candidate in enumerate((Action.RAISE_HALF, Action.RAISE_POT)):'
        source=source.replace(needle,'    passive_best = best_ev\n'+needle)
        source=source.replace('        if ev > best_ev + margin:',
            ('        if ev > best_ev and ev > passive_best + margin:' if name=='margin-once' else
             '        if ev > best_ev:'))
        exec(compile(source,str(path)+'::'+name,'exec'),m.__dict__)
    else:
        from street_learning import install
        install(m,name)
    return SimpleNamespace(new_half=m.initialize,choose_action=m.decide,on_hand_end=m.finish,name=name)
