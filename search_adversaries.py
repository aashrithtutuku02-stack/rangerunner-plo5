"""Offline search for weak spots; these seeds are never final evaluation seeds."""
import argparse
import json
from pathlib import Path
import random

from adversaries import Opponent
from stress_benchmark import run


def main():
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=32)
    p.add_argument('--deals',type=int,default=200);p.add_argument('--output',default='search-results')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(777001);summary=[]
    for i in range(a.count):
        value=rng.uniform(.50,.96)
        params=dict(value=value,raise_value=min(.99,value+rng.uniform(.02,.16)),
                    call_extra=rng.uniform(-.03,.25),bluff=rng.choice([0,.05,.15,.3,.55]),
                    half=rng.random()<.35,trap=rng.random()<.2,checkraise=rng.random()<.2)
        name=f'candidate-{i:03}'
        r=run(Opponent(name,params),'parameter-discovery',a.deals)
        r['params']=params;summary.append(r)
        (out/f'{name}.json').write_text(json.dumps(r,indent=2))
        print(name,f'{r["mean"]:+.3f}',params,flush=True)
    (out/'summary.json').write_text(json.dumps(sorted(summary,key=lambda r:r['mean']),indent=2))


if __name__=='__main__':main()
