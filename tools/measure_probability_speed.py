"""Alternating, warmed timing of numerically identical probability kernels."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import numpy as np
import range_model
import bet_ev
from opponents import model_451b as old_model
from opponents import bet_ev_451b as old_bet


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    p.add_argument('--repeats',type=int,default=9);p.add_argument('--loops',type=int,default=200)
    a=p.parse_args();range_model.warmup();old_model.warmup();bet_ev.warmup();old_bet.warmup()
    rng=np.random.default_rng(60412);slopes=np.array([0.,8.,16.,-8.,-16.])
    counts=rng.uniform(1,100,(4,3,3));counts[:,0,0]=0
    histories={
        'free_checks':[(i,i,0,1,0.,1) for i in range(4)],
        'facing_bets':[(0,0,1,2,.25,1),(1,1,1,3,.33,1),(2,2,2,1,.2,0),(3,3,1,0,.3,1)],
        'mixed':[(0,0,1,2,.25,1),(1,1,0,1,0.,1),(2,2,0,2,0.,1),(3,3,2,1,.3,0)],
    }
    results={}
    for n in (768,1280):
        q=rng.random((n,4));models=np.array([.08,.24,.48,.1,.1]);rows=rng.dirichlet(np.ones(n),5)
        outcomes=rng.choice([0.,.5,1.],n);equity=float((models@rows)@outcomes)
        cases=[]
        for name,history in histories.items():
            events=range_model.event_array(history)
            cases.append((name,lambda e=events:old_model.likelihoods(q,counts,e,slopes),
                          lambda e=events:range_model.likelihoods(q,counts,e,slopes)))
        args=(q[:,3],rows,models,outcomes,slopes,np.array([4.,6.,2.]),20,60,60,0,0,1,4,np.array([10,20]),equity)
        cases.append(('raise_values',lambda:old_bet.raise_values(*args),lambda:bet_ev.raise_values(*args)))
        for name,old,new in cases:
            np.testing.assert_array_equal(old(),new())
            timings={'previous':[],'optimized':[]}
            for repeat in range(a.repeats):
                order=[('previous',old),('optimized',new)]
                if repeat%2:order.reverse()
                for label,fn in order:
                    start=time.perf_counter()
                    for _ in range(a.loops):fn()
                    timings[label].append((time.perf_counter()-start)/a.loops)
            before=statistics.median(timings['previous']);after=statistics.median(timings['optimized'])
            results[f'{name}-{n}']=dict(previous_median_seconds=before,optimized_median_seconds=after,
                speedup=before/after,runs_seconds=timings,bit_identical=True)
    names=['range_model.py','bet_ev.py','opponents/model_451b.py','opponents/bet_ev_451b.py','tools/measure_probability_speed.py']
    result=dict(samples=[768,1280],repeats=a.repeats,loops=a.loops,results=results,
        scope='Warmed math-kernel timings; excludes simulation, HTTP and startup',
        source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    for name,r in results.items():print(name,round(r['speedup'],3),'x',flush=True)


if __name__=='__main__':main()
