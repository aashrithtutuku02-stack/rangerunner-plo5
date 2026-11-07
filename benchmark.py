"""Run reproducible full HTTP matches against the supplied baselines."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from evaluator import warmup
from game import AgentConfig
from judge_engine import HttpAgentHandle, play_match, format_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deals', type=int, default=1000)
    parser.add_argument('--seeds', nargs='+', default=['17'])
    parser.add_argument('--opponents', nargs='+', default=['random', 'calling_station', 'always_half', 'always_pot'])
    parser.add_argument('--output', default='benchmark-results')
    parser.add_argument('--agent', default='agent.py')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = root / args.output
    output.mkdir(exist_ok=True, parents=True)
    processes = []
    logs = []
    try:
        config = AgentConfig(num_hands=args.deals)
        sources = []
        for opp in args.opponents:
            source = (root/'adversary_agent.py' if opp.startswith('adversary:')
                      else Path(opp) if opp.endswith('.py') else root / 'baseline-bots' / f'baseline_{opp}.py')
            if not source.exists() and not opp.endswith('.py'):
                source = root / f'baseline_{opp}.py'
            sources.append(source)
        for port, source in [(5008, root / args.agent)]:
            log = (output / f'server-{port}.log').open('w')
            logs.append(log)
            env = dict(os.environ, PORT=str(port), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
            index=port-5009
            if index>=0 and args.opponents[index].startswith('adversary:'):
                env['OPPONENT_PROFILE']=args.opponents[index].split(':',1)[1]
            processes.append(subprocess.Popen([sys.executable, str(source)], cwd=root, env=env, stdout=log, stderr=log))
        hero = HttpAgentHandle('http://127.0.0.1:5008', config)
        assert hero.wait_healthy(15), 'Our bot did not start within 15 seconds'
        warmup()
        for i, opp in enumerate(args.opponents):
            port=5009+i
            log=(output/f'server-{port}.log').open('w');logs.append(log)
            env=dict(os.environ,PORT=str(port),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
            if opp.startswith('adversary:'):env['OPPONENT_PROFILE']=opp.split(':',1)[1]
            process=subprocess.Popen([sys.executable,str(sources[i])],cwd=root,env=env,stdout=log,stderr=log)
            processes.append(process)
            villain = HttpAgentHandle(f'http://127.0.0.1:{5009+i}', config)
            assert villain.wait_healthy(15), f'{opp} did not start'
            for seed in args.seeds:
                result = play_match(hero, villain, seed, args.deals)
                report = format_report(result)
                print(opp, 'seed', seed, flush=True)
                print(report, flush=True)
                label = Path(opp).stem.replace(':','-')
                (output / f'{label}-{seed}.json').write_text(result.to_json(indent=2))
                (output / f'{label}-{seed}.txt').write_text(report)
            villain._close()
            process.terminate();process.wait(timeout=5)
        hero._close()
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        for log in logs:
            log.close()


if __name__ == '__main__':
    main()
