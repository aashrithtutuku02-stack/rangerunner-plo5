"""Repeatable numeric equivalence and timing comparison for raise values."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import numpy as np
import bet_ev
from opponents import release_b15a as old
from game import AgentConfig


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    p.add_argument('--repeats',type=int,default=7);p.add_argument('--loops',type=int,default=300)
    a=p.parse_args();bet_ev.warmup()
    rng=np.random.default_rng(17);memory={};old.initialize(AgentConfig(),memory)
    q=rng.random((1280,4));ranges=rng.dirichlet(np.ones(1280),3)
    weights=memory['models']@ranges;outcomes=rng.choice([0.,.5,1.],1280)
    equity=float(weights@outcomes);results={}
    for name,pot,stack,targets in [('ordinary',20,70,[10,20]),('duplicate_all_in',120,20,[20,20])]:
        obs=SimpleNamespace(street=3,to_call=0,raises_this_street=0,my_stack=stack,
                            opp_stack=stack,my_bet=0,opp_bet=0,pot=pot)
        targets=np.array(targets)
        def original():
            values=[]
            for target in targets:
                final=pot+2*target
                f,r=old.response_prob(obs,memory,{'q':q},target,target/final,ranges)
                ev=float(weights@(f*pot+(1-f)*(outcomes*final-target)))
                behind=stack-target
                if behind>0:ev-=float(weights@r)*min(behind,final)*max(0.,.68-equity)
                values.append(ev)
            return values
        def compiled():
            return bet_ev.raise_values(q[:,3],ranges,memory['models'],outcomes,old.SLOPES,
                    memory['counts'][3,1],pot,stack,stack,0,0,0,4,targets,equity)
        np.testing.assert_allclose(original(),compiled(),atol=1e-11)
        timings={}
        for label,fn in [('previous',original),('compiled',compiled)]:
            times=[]
            for _ in range(a.repeats):
                start=time.perf_counter()
                for _ in range(a.loops):fn()
                times.append((time.perf_counter()-start)/a.loops)
            timings[label]=dict(median_seconds=statistics.median(times),runs_seconds=times)
        timings['speedup']=timings['previous']['median_seconds']/timings['compiled']['median_seconds']
        results[name]=timings
    report=dict(samples=1280,repeats=a.repeats,loops=a.loops,results=results,
        source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
                       for n in ['bet_ev.py','range_model.py','opponents/release_b15a.py','opponents/release_b15a_model.py']})
    Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
