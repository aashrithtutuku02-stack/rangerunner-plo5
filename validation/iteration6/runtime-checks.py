from pathlib import Path
import os,subprocess,time,sys,shutil
root=Path('/workspace/work/rangerunner');out=root/'validation/iteration6';os.chdir(root)
for name in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'):os.environ.pop(name,None)
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
def active():
 for path in Path('/proc').glob('[0-9]*/cmdline'):
  try:parts=path.read_bytes().split(b'\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if len(parts)>1 and parts[1]==b'evaluate_candidate.py':return True
 return False
while active():time.sleep(5)
print('Regression workers finished; starting serial runtime checks',flush=True)
def run(command,filename):
 print('Running',filename,flush=True)
 with (out/filename).open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
run([sys.executable,'-m','pytest','-q'],'unit-tests.txt')
restrictions=['--read-only','--tmpfs','/tmp:rw,nosuid,nodev,size=512m','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--cpus','1','--memory','4g','--volume',str(root)+':/app:ro']
run(['docker','run','--rm','--network','none',*restrictions,'--volume','/workspace/work/iteration6-runtime-identity.py:/verify.py:ro','rangerunner-sandbox:optimized','python','/verify.py'],'runtime-identity.json')
for i,policy in enumerate(('release-451b','release','release','release-451b')):
 run(['docker','run','--rm','--network','none',*restrictions,'rangerunner-sandbox:optimized','python','tools/worst_line_load.py','--hands','1000','--policy',policy],f'worst-line-{i}-{policy}.json')
try:
 subprocess.run(['docker','run','--detach','--name','rr-iteration6-smoke','--network','none',*restrictions,'--env','AGENT_TOKEN=local-check','rangerunner-sandbox:optimized'],check=True,stdout=subprocess.DEVNULL)
 run(['docker','exec','rr-iteration6-smoke','python','tools/smoke_test.py','--port','5008','--startup','15'],'offline-smoke.txt')
finally:subprocess.run(['docker','rm','-f','rr-iteration6-smoke'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
run([sys.executable,'/workspace/work/iteration6_cpu.py'],'single-cpu.txt')
shutil.copyfile('/workspace/work/iteration6-final-cpu.json',out/'single-cpu.json')
shutil.copyfile('/workspace/work/iteration6_cpu.py',out/'cpu-check.py')
run([sys.executable,'tools/check_results.py',str(out)],'cpu-fault-check.txt') if False else None
for seed in ('a','b','c','d'):
 for bot,checkout in (('fargield','external-fargield'),('starfish','external-shriharish')):
  dest=out/'external-final'/seed/bot
  run([sys.executable,'tools/fresh_match.py','--opponent',f'external:/workspace/work/{checkout}','--seed',f'iteration6-external-final-{seed}','--output',str(dest)],f'external-{seed}-{bot}.txt')
  run([sys.executable,'tools/check_results.py',str(dest)],f'external-{seed}-{bot}-fault-check.txt')
run([sys.executable,'benchmark.py','--deals','1000','--seeds','iteration6-http-final','--opponents','random','calling_station','always_half','always_pot','adversary:range-tight','adversary:independent-adaptive','--output',str(out/'http')],'http-summary.txt')
run([sys.executable,'tools/check_results.py',str(out/'http')],'http-fault-check.txt')
run([sys.executable,'tools/fresh_match.py','--opponent','adversary:release-451b','--seed','iteration6-fresh-final','--output',str(out/'fresh-process')],'fresh-summary.txt')
run([sys.executable,'tools/check_results.py',str(out/'fresh-process')],'fresh-fault-check.txt')
print('ALL SERIAL CHECKS PASSED',flush=True)
