"""Opt-in strategy variants; production remains unchanged during discovery."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import polar_model
import polar_bet_ev


PRIORS={
 'polar10':([0.,8.,16.,-12.],[.1,.25,.55,.1]),
 'polar20':([0.,8.,16.,-8.,-16.],[.1,.2,.5,.1,.1]),
 'polar40':([0.,8.,16.,-8.,-16.],[.1,.2,.3,.2,.2]),
}


def make(name):
    spec=importlib.util.spec_from_file_location('research_'+name,Path(__file__).with_name('opponents')/'polar20_3a4a.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.range_model=polar_model;m.bet_ev=polar_bet_ev
    polar_model.warmup();polar_bet_ev.warmup()
    slopes,prior=PRIORS[name];m.SLOPES=np.array(slopes)
    original=m.initialize
    def initialize(config,memory):
        original(config,memory);memory['models']=np.array(prior)
    m.initialize=initialize
    return SimpleNamespace(new_half=initialize,choose_action=m.decide,on_hand_end=m.finish,name=name)
