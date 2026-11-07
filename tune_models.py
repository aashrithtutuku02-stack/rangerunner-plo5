"""Offline prior search on discovery deals; do not use final evaluation seeds."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from adversaries import Opponent
from stress_benchmark import run


VARIANTS=[
    ('base',[0,4,8,16],[.2,.35,.3,.15]),
    ('strict40',[0,4,8,16],[.1,.2,.3,.4]),
    ('strict60',[0,4,8,16],[.1,.1,.2,.6]),
    ('strict75',[0,4,8,16],[.05,.05,.15,.75]),
    ('tight3',[0,8,16],[.1,.3,.6]),
    ('sharp32',[0,8,16,32],[.1,.2,.4,.3]),
]


def policy(name,slopes,prior):
    spec=importlib.util.spec_from_file_location('policy_'+name,Path(__file__).with_name('strategy.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.SLOPES=np.array(slopes,dtype=float)
    def init(config,memory):
        module.initialize(config,memory);memory['models']=np.array(prior,dtype=float)
    return SimpleNamespace(new_half=init,choose_action=module.decide,on_hand_end=module.finish)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',default='prior-search')
    p.add_argument('--opponents',nargs='+',default=['range-tight'])
    p.add_argument('--deals',type=int,default=1000)
    p.add_argument('--variants',nargs='*')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    for name,slopes,prior in VARIANTS:
        if a.variants and name not in a.variants:continue
        hero=policy(name,slopes,prior)
        for opponent in a.opponents:
            r=run(Opponent(opponent),'prior-discovery',a.deals,hero)
            r.update(variant=name,slopes=slopes,prior=prior)
            (out/f'{name}-{opponent}.json').write_text(json.dumps(r,indent=2))
            print(name,opponent,f'{r["mean"]:+.3f}',r['ci'],flush=True)
