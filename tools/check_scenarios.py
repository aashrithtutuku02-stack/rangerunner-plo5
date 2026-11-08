"""Reject incomplete sweeps, accounting-only runs and mixed source versions."""
import argparse
import hashlib
import json
from pathlib import Path

CASES={'random','nut_flush','wheel','quads','split','four_board','four_hole','flush_fullhouse'}
EXPECTED={'history_prefixes':15952,'replayed_decisions':15952,'learning_checks':67028,
          'edges':41489,'terminal_histories':25538,'max_actions':14,
          'terminal_inference_checks':51076,'duplicate_results':51076}
DIGEST='ee4bc615ab40a89dc1f4e58c41d42f2c2470e0915c6164b3f04da67a3823da83'


def summarize(reports,buttons=(0,1)):
    assert reports,'No scenario reports'
    seen=set();versions=set();totals={k:0 for k in EXPECTED if k!='max_actions'}
    for r in reports:
        key=(r['case'],r['button']);assert key not in seen,'Duplicate scenario'
        seen.add(key)
        assert r['mode']=='full_policy','Accounting-only reports do not test the full policy'
        assert r['totals']==EXPECTED,'Incomplete betting tree or replay checks'
        assert r['response_read_checks']==EXPECTED['learning_checks'],'Incomplete calling-read checks'
        assert r['unique_numeric_states']==678 and r['sequence_sha256']==DIGEST
        assert set(r['sample_counts'])=={'768','1280'}
        assert sum(r['sample_counts'].values())==15952
        versions.add(json.dumps(r['source_sha256'],sort_keys=True))
        for k in totals:totals[k]+=r['totals'][k]
    assert seen=={(c,b) for c in CASES for b in buttons},'Missing or unexpected case/button'
    assert len(versions)==1,'Mixed source versions'
    return dict(cases=sorted(CASES),buttons=list(buttons),reports=len(reports),totals=totals,
                max_actions=14,response_read_checks=sum(r['response_read_checks'] for r in reports),sequence_sha256=DIGEST,
                max_observed_decision_seconds=max(r['max_decision_seconds'] for r in reports),
                source_sha256=json.loads(next(iter(versions))))


def main():
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--button',type=int,choices=[0,1])
    p.add_argument('--check-source',action='store_true');p.add_argument('--output');a=p.parse_args()
    reports=[]
    for path in Path(a.directory).glob('*-button*.json'):
        r=json.loads(path.read_text())
        assert path.stem==f"{r['case']}-button{r['button']}"
        reports.append(r)
    result=summarize(reports,(a.button,) if a.button is not None else (0,1))
    if a.check_source:
        root=Path(__file__).resolve().parent.parent
        assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==sha
                   for n,sha in result['source_sha256'].items()),'Reports do not match current source'
    text=json.dumps(result,indent=2)+'\n'
    if a.output:Path(a.output).write_text(text)
    print(text)


if __name__=='__main__':main()
