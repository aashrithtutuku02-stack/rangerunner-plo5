"""Keep exact public-action counts while testing a fading frequency model."""
import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace


def make(name):
    assert name in ('recent-frequency','recent-none')
    decay=.995 if name=='recent-frequency' else 1.
    path=Path(__file__).with_name('opponents')/'release_451b.py'
    spec=importlib.util.spec_from_file_location('research_'+name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    original_init=m.initialize;original_snapshot=m.state_snapshot;original_observe=m.observe_event
    def initialize(config,memory):
        original_init(config,memory)
        memory['recent_counts']=memory['counts'].copy()
        memory['frequency_prior']=memory['counts'].copy()
    def snapshot(memory):
        result=original_snapshot(memory)
        result['recent_counts']=memory['recent_counts'].copy()
        return result
    def observe(memory,event):
        original_observe(memory,event)
        original_observe({'counts':memory['recent_counts']},event)
    m.initialize=initialize;m.state_snapshot=snapshot;m.observe_event=observe
    m.model_counts=lambda memory:memory['recent_counts']
    for name in ('_decide','_finish','range_weights'):
        source=inspect.getsource(getattr(m,name))
        assert "memory['counts']" in source
        source=source.replace("memory['counts']","model_counts(memory)")
        exec(compile(source,str(path)+'::recency','exec'),m.__dict__)
    original_finish=m._finish
    def finish(result,memory):
        original_finish(result,memory)
        if decay<1:
            prior=memory['frequency_prior']
            memory['recent_counts']=prior+decay*(memory['recent_counts']-prior)
    m._finish=finish
    return SimpleNamespace(new_half=initialize,choose_action=m.decide,on_hand_end=m.finish,name='recent-frequency' if decay<1 else 'recent-none')
