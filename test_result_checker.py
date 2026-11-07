import json
from pathlib import Path
import subprocess
import sys
import pytest


def report():
    stats=dict(errors=0,forfeited=False,timed_out=False,skipped_calls=0)
    return dict(kind='match_result',num_deals=1000,verdict='AGENT1_WIN',
                agent_stats={p:[dict(stats),dict(stats)] for p in ['agent1','agent2']})


def check(root):
    return subprocess.run([sys.executable,str(Path(__file__).with_name('tools')/'check_results.py'),str(root)],capture_output=True,text=True)


def test_combined_match_is_checked_without_treating_halves_as_matches(tmp_path):
    (tmp_path/'half1.json').write_text(json.dumps(dict(kind='half_result')))
    (tmp_path/'combined.json').write_text(json.dumps(report()))
    assert check(tmp_path).returncode==0
    (tmp_path/'combined.json').unlink()
    assert check(tmp_path).returncode!=0


@pytest.mark.parametrize('fault',['errors','forfeited','timed_out','skipped_calls'])
def test_any_real_judge_fault_fails_verification(tmp_path,fault):
    r=report();r['agent_stats']['agent1'][1][fault]=1
    (tmp_path/'combined.json').write_text(json.dumps(r))
    assert check(tmp_path).returncode!=0
