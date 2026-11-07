"""Paired policy comparisons. Direct calls do not enforce an HTTP time bank."""
import argparse
import json
from pathlib import Path
import statistics

from adversaries import Opponent
from stress_benchmark import run
from research_candidates import make


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--candidates',nargs='+',default=['complete','calibrated','bayes','recent'])
    p.add_argument('--opponents',nargs='+',default=['incumbent','nit','balanced','switcher','search000','search024','pot','call'])
    p.add_argument('--deals',type=int,default=500)
    p.add_argument('--seed',default='iteration2-discovery')
    p.add_argument('--output',default='comparison-results')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    baseline=make('incumbent')
    controls={}
    for name in a.opponents:
        controls[name]=run(Opponent(name),a.seed,a.deals,baseline)
        (out/f'incumbent-{name}.json').write_text(json.dumps(controls[name],indent=2))
    for candidate in a.candidates:
        hero=make(candidate);diffs=[];means=[]
        for name in a.opponents:
            r=run(Opponent(name),a.seed,a.deals,hero)
            delta=[x-y for x,y in zip(r['paired'],controls[name]['paired'])]
            mean=statistics.mean(delta);se=statistics.stdev(delta)/len(delta)**.5
            r.update(candidate=candidate,improvement=mean,improvement_ci=[mean-1.96*se,mean+1.96*se],paired_improvement=delta)
            (out/f'{candidate}-{name}.json').write_text(json.dumps(r,indent=2))
            diffs.extend(delta);means.append(mean)
            print(candidate,name,f'score={r["mean"]:+.3f} delta={mean:+.3f} CI={r["improvement_ci"]}',flush=True)
        print(candidate,'balanced pool mean improvement',statistics.mean(means),flush=True)


if __name__=='__main__':main()
