"""Play a full real-bank match with hero restricted to one CPU and 4 GB."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--policy',choices=['release','release-9efa'],default='release')
    p.add_argument('--seed',default='one-cpu-match')
    p.add_argument('--image',default='rangerunner-sandbox:optimized')
    p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    for name in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'):
        env.pop(name,None)
    files=['agent.py','strategy.py','calling_read.py','range_model.py','bet_ev.py','fast_engine.py',
           'equity_engine.py','game.py','evaluator.py','judge_engine.py','preflop.npz',
           'native/plo5_fast_linux_x86_64.so','tools/cpu_match.py']
    if a.policy!='release':files+=['research_agent.py','research_candidates.py',
        'opponents/release_9efa.py','opponents/model_9efa.py','opponents/bet_ev_9efa.py']
    fingerprints={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files}
    name='rr-cpu-'+a.policy
    command=['docker','run','--detach','--name',name,'--read-only','--tmpfs','/tmp:rw,nosuid,nodev,size=512m',
        '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--cpus','1','--memory','4g',
        '--publish','127.0.0.1:5040:5008','--env','AGENT_TOKEN=cpu-check','--volume',str(ROOT)+':/app:ro']
    if a.policy!='release':command+=['--env','RANGERUNNER_POLICY='+a.policy]
    command+=[a.image]
    if a.policy!='release':command+=['python','-m','uvicorn','research_agent:agent.app',
        '--host','0.0.0.0','--port','5008','--no-access-log']
    opponent=None;started=False
    with (out/'opponent.log').open('w') as log:
        try:
            subprocess.run(command,env=env,check=True,stdout=subprocess.DEVNULL);started=True
            opposite=dict(env,PORT='5041',AGENT_TOKEN='cpu-check')
            opponent=subprocess.Popen([sys.executable,str(ROOT/'baseline-bots/baseline_calling_station.py')],
                cwd=ROOT,env=opposite,stdout=log,stderr=log)
            judge=dict(env,AGENT1_TOKEN='cpu-check',AGENT2_TOKEN='cpu-check')
            subprocess.run([sys.executable,'judge_engine.py','--agent1','5040','--agent2','5041',
                '--deals','1000','--seed',a.seed,'--json',str(out/'match.json')],cwd=ROOT,env=judge,check=True)
        finally:
            if opponent is not None:
                opponent.terminate();opponent.wait(timeout=10)
            if started:
                with (out/'container.log').open('w') as f:
                    subprocess.run(['docker','logs',name],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
                subprocess.run(['docker','rm','-f',name],env=env,check=True,stdout=subprocess.DEVNULL)
    assert fingerprints=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files}
    subprocess.run([sys.executable,'tools/check_results.py',str(out)],cwd=ROOT,env=env,check=True)
    result=json.loads((out/'match.json').read_text())
    assert result['verdict']=='AGENT1_WIN','CallingStation was not beaten under the actual CPU limit'
    meta=out/'metadata';meta.mkdir(exist_ok=True)
    (meta/'source.json').write_text(json.dumps(dict(policy=a.policy,seed=a.seed,command=command,
        source_sha256=fingerprints,scope='Hero alone is limited to one CPU/4GB; host judge and opponent run serially with no offline stress'),indent=2)+'\n')


if __name__=='__main__':main()
