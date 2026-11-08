import os,subprocess,sys
from pathlib import Path
root=Path('/workspace/work/rangerunner')
log=Path('/workspace/work/iteration5-cpu-baseline.log').open('w')
process=None
try:
 subprocess.run(['docker','run','--detach','--name','rr-iteration5-cpu','--read-only','--tmpfs','/tmp:rw,nosuid,nodev,size=512m','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--cpus','1','--memory','4g','--publish','127.0.0.1:5040:5008','--env','AGENT_TOKEN=cpu-check','--volume','/workspace/work/rangerunner:/app:ro','rangerunner-sandbox:optimized'],check=True)
 env=dict(os.environ,PORT='5041',AGENT_TOKEN='cpu-check',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 process=subprocess.Popen([sys.executable,str(root/'baseline-bots'/'baseline_calling_station.py')],cwd=root,env=env,stdout=log,stderr=log)
 env=dict(os.environ,AGENT1_TOKEN='cpu-check',AGENT2_TOKEN='cpu-check')
 result=subprocess.run([sys.executable,'judge_engine.py','--agent1','5040','--agent2','5041','--deals','1000','--seed','iteration5-cpu-final','--json','/workspace/work/iteration5-final-cpu.json'],cwd=root,env=env)
 sys.exit(result.returncode)
finally:
 if process is not None:
  process.terminate();process.wait(timeout=10)
 subprocess.run(['docker','rm','-f','rr-iteration5-cpu'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 log.close()
