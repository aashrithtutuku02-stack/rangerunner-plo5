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
    p.add_argument('--baseline',default='incumbent')
    p.add_argument('--opponents',nargs='+',default=['incumbent'])
    p.add_argument('--seeds',nargs='+',required=True)
    p.add_argument('--deals',type=int,default=1000)
    p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    sources={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
             for name in ['strategy.py','range_model.py','fast_engine.py','bet_ev.py','river_precision.py']}
    extra_names=['evaluate_candidate.py','research_candidates.py','research_bluff.py','bluff_read.py','bluff_pure.py','opponents/release_3aa.py','opponents/calling_3aa.py','research_street.py','street_learning.py','calling_read.py',
                 'opponents/release_9efa.py','opponents/model_9efa.py','opponents/bet_ev_9efa.py',
                 'research_reraise.py','reraise_ev.py','research_learning.py','model_learning.py',
                 'range_precision.py','research_range_precision.py','research_recency.py',
                 'opponents/release_451b.py','opponents/model_451b.py','opponents/bet_ev_451b.py',
                 'research_polar.py','research_joint.py','research_gated.py','polar_model.py','polar_bet_ev.py',
                 'independent_opponents.py','opponents/polar20_3a4a.py','opponents/release_52c5.py','opponents/bet_ev_52c5.py',
                 'opponents/release_b15a_model.py','adversaries.py','adversary_cases.json',
                 'stress_benchmark.py','game.py','evaluator.py','preflop.npz',
                 'native/plo5_fast.c','native/plo5_fast_linux_x86_64.so']
    extra={n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest()
           for n in extra_names if (Path(__file__).parent/n).exists()}
    summary=[]
    for name in a.opponents:
        differences=[];scores=[]
        for seed in a.seeds:
            # A generous offline bank prevents CPU scheduling from reducing
            # the policy's requested samples, including selective expansion.
            # Actual 8-second behavior is checked separately through HTTP.
            baseline=run(Opponent(name),seed,a.deals,make(a.baseline),time_bank_seconds=80.,capture_samples=True)
            candidate=run(Opponent(name),seed,a.deals,make(a.candidate),time_bank_seconds=80.,capture_samples=True)
            if name==a.baseline:assert all(x==0 for x in baseline['paired'])
            delta=[x-y for x,y in zip(candidate['paired'],baseline['paired'])]
            r=dict(opponent=name,seed=seed,policy=a.candidate,baseline_policy=a.baseline,source_sha256=sources,
                   additional_source_sha256=extra,sample_mode='fixed-policy-sampling',baseline=baseline,candidate=candidate,delta=delta)
            (out/f'{name}-{seed}.json').write_text(json.dumps(r,indent=2))
            differences.extend(delta);scores.extend(candidate['paired'])
            print(name,seed,'candidate',round(candidate['mean'],4),'change',round(statistics.mean(delta),4),flush=True)
        mean=statistics.mean(differences);se=statistics.stdev(differences)/len(differences)**.5
        r=dict(opponent=name,candidate_score=statistics.mean(scores),improvement=mean,ci=[mean-1.96*se,mean+1.96*se],deals=len(differences))
        summary.append(r);print('POOLED',r,flush=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))


if __name__=='__main__':main()
