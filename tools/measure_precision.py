"""Compare sampled river estimates to complete 65,780-hand enumeration."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import numpy as np
import fast_engine as engine
import range_model
import river_precision
from game import make_deal


def estimate(values,outcomes):
    q=engine.percentiles(values)
    counts=np.ones((4,3,3));counts[3,1]=[5.,5.,2.]
    L=range_model.likelihoods(q,counts,range_model.event_array([(0,3,1,2,1/3,1)]),np.array([0.,8.,16.]))
    L/=L.sum(axis=1)[:,None]
    return float(outcomes.mean()),float((np.array([.1,.3,.6])@L)@outcomes)


def main():
    p=argparse.ArgumentParser();p.add_argument('--boards',type=int,default=24)
    p.add_argument('--repeats',type=int,default=32);p.add_argument('--output',required=True)
    a=p.parse_args();rows=[]
    engine.warm_engine();range_model.warmup()
    rng=np.random.default_rng(720519)
    for board_index in range(a.boards):
        deal=make_deal('iteration3-estimator-truth',board_index)
        h=np.array(deal.hole_cards[0],dtype=np.int32);b=np.array(deal.board,dtype=np.int32)
        exact_values,exact_outcomes=engine.reference.exact_river(h,b)
        truth=estimate(exact_values,exact_outcomes)
        for repeat in range(a.repeats):
            state=np.uint64(rng.integers(1,2**63))
            hands,values,outcomes,_,next_state=engine.simulate(h,b,1280,state)
            small=estimate(values,outcomes)
            cache=dict(hole=h,board=b,hands=hands,values=values,outcomes=outcomes)
            extra_state=np.uint64(rng.integers(1,2**63))
            river_precision.extend(dict(rng=next_state,precision_rng=extra_state),cache)
            large=estimate(cache['values'],cache['outcomes'])
            rows.append(dict(board=board_index,repeat=repeat,truth=truth,initial=small,expanded=large))
        print('board',board_index+1,'of',a.boards,flush=True)
    metrics={}
    for i,kind in enumerate(['uniform','selective_raise_range']):
        rmse={size:float(np.sqrt(np.mean([(r[size][i]-r['truth'][i])**2 for r in rows])))
              for size in ['initial','expanded']}
        metrics[kind]=dict(rmse=rmse,reduction=1-rmse['expanded']/rmse['initial'])
    result=dict(boards=a.boards,repeats=a.repeats,trials=len(rows),
                initial_samples=1280,expanded_samples=4096,metrics=metrics,rows=rows,
                source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
                               for n in ['river_precision.py','range_model.py','fast_engine.py']})
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
