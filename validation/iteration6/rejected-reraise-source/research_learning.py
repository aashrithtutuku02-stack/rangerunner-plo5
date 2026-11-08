"""Family-level forgetting isolated from the released betting policy."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import model_learning


def make(name):
    assert name=='family-forgetting'
    spec=importlib.util.spec_from_file_location('research_'+name,Path(__file__).with_name('opponents')/'release_451b.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    original=m._finish
    def finish(result,memory):
        before=memory['models']
        original(result,memory)
        if memory['models'] is not before:
            # Undo only the frozen policy's final uniform forgetting step.
            # Production can apply the new rule directly to the posterior.
            posterior=(memory['models']-.015/len(m.SLOPES))/.985
            memory['models']=model_learning.regularize(posterior,m.SLOPES<0)
    m._finish=finish
    return SimpleNamespace(new_half=m.initialize,choose_action=m.decide,on_hand_end=m.finish,name=name)
