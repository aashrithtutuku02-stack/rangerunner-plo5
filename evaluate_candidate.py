"""Compare policy and incumbent on common discovery or held-out deal seeds."""
import argparse
import json
from pathlib import Path
import statistics
import hashlib

from adversaries import Opponent
from research_candidates import make
from stress_benchmark import run


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--candidate',default='release')
    p.add_argument('--opponents',nargs='+',default=['incumbent'])
    p.add_argument('--seeds',nargs='+',required=True)
    p.add_argument('--deals',type=int,default=1000)
    p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    sources={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
             for name in ['strategy.py','range_model.py','fast_engine.py']}
    summary=[]
    for name in a.opponents:
        differences=[];scores=[]
        for seed in a.seeds:
            # A generous offline bank keeps the default sample count fixed.
            # Actual 8-second behavior is checked separately through HTTP.
            baseline=run(Opponent(name),seed,a.deals,make('incumbent'),time_bank_seconds=80.)
            candidate=run(Opponent(name),seed,a.deals,make(a.candidate),time_bank_seconds=80.)
            if name=='incumbent':assert all(x==0 for x in baseline['paired'])
            delta=[x-y for x,y in zip(candidate['paired'],baseline['paired'])]
            r=dict(opponent=name,seed=seed,policy=a.candidate,source_sha256=sources,sample_mode='fixed-default-counts',baseline=baseline,candidate=candidate,delta=delta)
            (out/f'{name}-{seed}.json').write_text(json.dumps(r,indent=2))
            differences.extend(delta);scores.extend(candidate['paired'])
            print(name,seed,'candidate',round(candidate['mean'],4),'change',round(statistics.mean(delta),4),flush=True)
        mean=statistics.mean(differences);se=statistics.stdev(differences)/len(differences)**.5
        r=dict(opponent=name,candidate_score=statistics.mean(scores),improvement=mean,ci=[mean-1.96*se,mean+1.96*se],deals=len(differences))
        summary.append(r);print('POOLED',r,flush=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))


if __name__=='__main__':main()
