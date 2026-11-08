from pathlib import Path
import os,subprocess,time,sys,shutil,hashlib,json
root=Path('/workspace/work/rangerunner');out=root/'validation/iteration7';os.chdir(root)
for name in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'):os.environ.pop(name,None)
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
while not all(Path('/workspace/work/iteration7-holdout-'+label+'/summary.json').exists() for label in ('ac','bd')):time.sleep(3)
protocol=json.loads((out/'final-holdout-protocol.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in protocol['source_sha256'].items())
print('Fixed-source evaluation workers finished; starting serial runtime checks',flush=True)
def run(command,filename):
 print('Running',filename,flush=True)
 with (out/filename).open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
restrictions=['--read-only','--tmpfs','/tmp:rw,nosuid,nodev,size=512m','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--cpus','1','--memory','4g','--volume',str(root)+':/app:ro']
run(['docker','run','--rm','--network','none',*restrictions,'--volume','/workspace/work/iteration7-runtime-identity.py:/verify.py:ro','rangerunner-sandbox:optimized','python','/verify.py'],'runtime-identity.json')
run(['docker','run','--rm','--network','none',*restrictions,'rangerunner-sandbox:optimized','python','tools/worst_line_load.py','--hands','1000'],'worst-line-load.json')
try:
 subprocess.run(['docker','run','--detach','--name','rr-iteration7-smoke','--network','none',*restrictions,'--env','AGENT_TOKEN=local-check','rangerunner-sandbox:optimized'],check=True,stdout=subprocess.DEVNULL)
 run(['docker','exec','rr-iteration7-smoke','python','tools/smoke_test.py','--port','5008','--startup','15'],'offline-smoke.txt')
finally:subprocess.run(['docker','rm','-f','rr-iteration7-smoke'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for policy in ('release-9efa','release'):
 run([sys.executable,'tools/cpu_match.py','--policy',policy,'--seed','iteration7-cpu-caller-final','--output',str(out/'cpu'/policy)],f'cpu-{policy}.txt')
run([sys.executable,'benchmark.py','--deals','1000','--seeds','iteration7-http-final','--opponents','random','calling_station','always_half','always_pot','adversary:range-tight','adversary:independent-adaptive','adversary:passive-trap','adversary:caller-switcher','--output',str(out/'http')],'http-summary.txt')
run([sys.executable,'tools/check_results.py',str(out/'http')],'http-fault-check.txt')
run([sys.executable,'tools/fresh_match.py','--opponent','adversary:release-9efa','--seed','iteration7-fresh-final','--output',str(out/'fresh-process')],'fresh-summary.txt')
run([sys.executable,'tools/check_results.py',str(out/'fresh-process')],'fresh-fault-check.txt')
for seed in ('a','b'):
 for bot,checkout in (('fargield','external-fargield'),('starfish','external-shriharish')):
  dest=out/'external-final'/seed/bot
  run([sys.executable,'tools/fresh_match.py','--opponent',f'external:/workspace/work/{checkout}','--seed',f'iteration7-public-final-{seed}','--output',str(dest)],f'external-{seed}-{bot}.txt')
  run([sys.executable,'tools/check_results.py',str(dest)],f'external-{seed}-{bot}-fault-check.txt')
print('ALL SERIAL CHECKS PASSED',flush=True)
