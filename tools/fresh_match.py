"""Restart both HTTP servers between halves, as the tournament does."""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--opponent',default='adversary:range-tight')
    p.add_argument('--seed',default='fresh-process-holdout')
    p.add_argument('--deals',type=int,default=1000)
    p.add_argument('--output',default='fresh-results')
    a=p.parse_args();root=Path(__file__).resolve().parent.parent
    out=root/a.output;out.mkdir(parents=True,exist_ok=True)
    source=(root/'adversary_agent.py' if a.opponent.startswith('adversary:')
            else root/'baseline-bots'/f'baseline_{a.opponent}.py')
    for half in (1,2):
        processes=[];logs=[]
        try:
            for port,path in ((5030,root/'agent.py'),(5031,source)):
                env=dict(os.environ,PORT=str(port),AGENT_TOKEN='fresh-check',
                         OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
                if a.opponent.startswith('adversary:'):
                    env['OPPONENT_PROFILE']=a.opponent.split(':',1)[1]
                log=(out/f'half{half}-{port}.log').open('w');logs.append(log)
                processes.append(subprocess.Popen([sys.executable,str(path)],cwd=root,env=env,stdout=log,stderr=log))
            env=dict(os.environ,AGENT1_TOKEN='fresh-check',AGENT2_TOKEN='fresh-check')
            subprocess.run([sys.executable,'judge_engine.py','--agent1','5030','--agent2','5031',
                            '--half',str(half),'--deals',str(a.deals),'--seed',a.seed,
                            '--json',str(out/f'half{half}.json')],cwd=root,env=env,check=True)
        finally:
            for proc in processes:proc.terminate()
            for proc in processes:proc.wait(timeout=5)
            for log in logs:log.close()
    subprocess.run([sys.executable,'judge_engine.py','combine',str(out/'half1.json'),
                    str(out/'half2.json'),'--json',str(out/'combined.json')],cwd=root,check=True)


if __name__=='__main__':main()
