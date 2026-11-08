"""Frozen-release experiments for a price-aware mixed bluff policy."""
import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace
import bluff_read


def make(name):
    assert name in ('bluff-quarter','bluff-half')
    path=Path(__file__).with_name('opponents')/'release_3aa.py'
    spec=importlib.util.spec_from_file_location('research_'+name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    initialize=m.initialize;observe=m.observe_event
    def initialize_bluffs(config,memory):
        initialize(config,memory);memory['fold_windows']=((),())
    def observe_bluffs(memory,event):
        observe(memory,event);memory['fold_windows']=bluff_read.observe(memory['fold_windows'],event)
    m.initialize=initialize_bluffs;m.observe_event=observe_bluffs
    m.bluff_choice=lambda obs,mem,eq,passive,action:bluff_read.choose(obs,mem,eq,passive,action,.25 if name=='bluff-quarter' else .5)
    source=inspect.getsource(m._decide)
    needle='    memory[\'last\'] = (obs, action, cache)'
    assert source.count(needle)==1
    source=source.replace(needle,'    action=bluff_choice(obs,memory,equity,passive_ev,action)\n'+needle)
    exec(compile(source,str(path)+'::'+name,'exec'),m.__dict__)
    return SimpleNamespace(new_half=m.initialize,choose_action=m.decide,on_hand_end=m.finish,name=name)
