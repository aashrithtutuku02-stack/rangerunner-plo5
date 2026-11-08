"""Duplicate-deal stress suite, with fresh memory and no hidden-card access.

Direct calls accelerate strategy discovery. Use the HTTP judge for final
time-bank and server validation. Logs include losses and confidence intervals.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

import agent
import calling_read
from adversaries import Opponent, names
from game import AgentConfig, Game, make_deal


def run(opponent, seed, deals, hero=agent,time_bank_seconds=8.0,capture_samples=False):
    config = AgentConfig(num_hands=deals,time_bank_seconds=time_bank_seconds)
    paired = [0.0]*deals
    timings = []
    sample_counts={};expanded=set();max_decision=0.
    read_decisions=0;read_hands=set();max_response_window=0
    for seat in (0,1):
        hm, vm = {}, {}
        hero.new_half(config,hm);opponent.new_half(config,vm)
        cost = [0.0,0.0]
        for i in range(deals):
            g=Game(make_deal(seed,i),i%2,i)
            while not g.is_terminal:
                current=g.to_act;obs=g.observation(current)
                begin=time.perf_counter()
                action = hero.choose_action(obs,hm) if current==seat else opponent.choose_action(obs,vm)
                elapsed=time.perf_counter()-begin
                cost[current]+=elapsed
                if capture_samples and current==seat:
                    max_decision=max(max_decision,elapsed)
                    window=hm.get('response_window',())
                    max_response_window=max(max_response_window,len(window))
                    if calling_read.confident_caller(window):
                        read_decisions+=1;read_hands.add((seat,i))
                    cache=hm.get('cache')
                    if cache is not None:
                        size=len(cache['outcomes']);sample_counts[size]=sample_counts.get(size,0)+1
                        if size==4096:expanded.add((seat,cache['key']))
                assert action in obs.legal_actions,(opponent.name,obs,action)
                g.apply(action)
            paired[i]+=g.result().nets[seat]/2.0
            begin=time.perf_counter();hero.on_hand_end(g.hand_result(seat),hm)
            cost[seat]+=time.perf_counter()-begin
            opponent.on_hand_end(g.hand_result(1-seat),vm)
        timings.append(dict(hero=cost[seat],opponent=cost[1-seat]))
    mean=statistics.mean(paired)
    se=statistics.stdev(paired)/(deals**.5) if deals>1 else 0.0
    return dict(opponent=opponent.name,seed=seed,deals=deals,time_bank_seconds=time_bank_seconds,mean=mean,
                ci=[mean-1.96*se,mean+1.96*se],timings=timings,paired=paired,
                sampling=dict(samples_per_decision=sample_counts,expanded_boards=len(expanded),
                              calling_read_decisions=read_decisions,calling_read_hands=len(read_hands),
                              max_response_window=max_response_window,
                              max_decision_seconds=max_decision) if capture_samples else None)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--deals',type=int,default=500)
    p.add_argument('--seeds',nargs='+',default=['discovery-a'])
    p.add_argument('--opponents',nargs='+',default=names())
    p.add_argument('--output',default='stress-results')
    p.add_argument('--cases',help='JSON list of selected parameterized adversary cases')
    args=p.parse_args()
    root=Path(args.output);root.mkdir(parents=True,exist_ok=True)
    opponents=[Opponent(c['name'],c['params']) for c in json.loads(Path(args.cases).read_text())] if args.cases else [Opponent(name) for name in args.opponents]
    for opponent in opponents:
        for seed in args.seeds:
            r=run(opponent,seed,args.deals)
            (root/f'{opponent.name}-{seed}.json').write_text(json.dumps(r,indent=2))
            print(f'{opponent.name:12} {seed}: {r["mean"]:+.3f} [{r["ci"][0]:+.3f}, {r["ci"][1]:+.3f}]',flush=True)


if __name__=='__main__':main()
