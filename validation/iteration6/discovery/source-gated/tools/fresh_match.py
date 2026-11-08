"""Restart both HTTP servers between halves, as the tournament does."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import http.client
import json
import hashlib


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--opponent',default='adversary:range-tight')
    p.add_argument('--agent',default='agent.py')
    p.add_argument('--seed',default='fresh-process-holdout')
    p.add_argument('--deals',type=int,default=1000)
    p.add_argument('--output',default='fresh-results')
    a=p.parse_args();root=Path(__file__).resolve().parent.parent
    out=root/a.output;out.mkdir(parents=True,exist_ok=True)
    external=Path(a.opponent[len('external:'):]).resolve() if a.opponent.startswith('external:') else None
    if external:
        for name in ('game.py','evaluator.py'):
            assert (external/name).read_bytes()==(root/name).read_bytes(),(name,'external rules differ')
    source=(root/'tools/external_agent.py' if external else root/'adversary_agent.py' if a.opponent.startswith('adversary:')
            else root/'baseline-bots'/f'baseline_{a.opponent}.py')
    for half in (1,2):
        processes=[];logs=[]
        try:
            for port,path in ((5030,root/a.agent),(5031,source)):
                env=dict(os.environ,PORT=str(port),AGENT_TOKEN='fresh-check',
                         OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
                if a.opponent.startswith('adversary:'):
                    env['OPPONENT_PROFILE']=a.opponent.split(':',1)[1]
                if external and port==5031:
                    env['EXTERNAL_BOT_DIR']=str(external)
                    env.pop('STRAT_PARAMS',None);env.pop('STRAT_IGNORE_FILE',None)
                log=(out/f'half{half}-{port}.log').open('w');logs.append(log)
                processes.append(subprocess.Popen([sys.executable,str(path)],cwd=root,env=env,stdout=log,stderr=log))
            env=dict(os.environ,AGENT1_TOKEN='fresh-check',AGENT2_TOKEN='fresh-check')
            subprocess.run([sys.executable,'judge_engine.py','--agent1','5030','--agent2','5031',
                            '--half',str(half),'--deals',str(a.deals),'--seed',a.seed,
                            '--json',str(out/f'half{half}.json')],cwd=root,env=env,check=True)
            if external:
                connection=http.client.HTTPConnection('127.0.0.1',5031,timeout=5)
                try:
                    connection.request('GET','/_benchmark_status',headers={'X-Agent-Token':'fresh-check'})
                    response=connection.getresponse();assert response.status==200
                    status=json.loads(response.read())
                finally:connection.close()
                assert status['core_available'] and status['core_import_error'] is None
                assert not status['callback_errors'] and not status['caught_model_errors']
                assert status['preflop_table_loaded'] is not False
                assert status['opponent_model_available'] is not False and status['range_module_available'] is not False
                diagnostic=status['native_diagnostics']
                if diagnostic:
                    assert not any(diagnostic[k] for k in ('fault_events','fallback_decisions','disabled'))
                for name,digest in status['source_sha256'].items():
                    original=subprocess.check_output(['git','-C',str(external),'show','HEAD:'+name])
                    assert hashlib.sha256(original).hexdigest()==digest,(name,'modified external source')
                status['commit']=subprocess.check_output(['git','-C',str(external),'rev-parse','HEAD'],text=True).strip()
                status['origin']=subprocess.check_output(['git','-C',str(external),'remote','get-url','origin'],text=True).strip()
                status['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                meta=out/'external-status';meta.mkdir(exist_ok=True)
                (meta/f'half{half}.json').write_text(json.dumps(status,indent=2)+'\n')
        finally:
            for proc in processes:proc.terminate()
            for proc in processes:proc.wait(timeout=5)
            for log in logs:log.close()
    subprocess.run([sys.executable,'judge_engine.py','combine',str(out/'half1.json'),
                    str(out/'half2.json'),'--json',str(out/'combined.json')],cwd=root,check=True)


if __name__=='__main__':main()
