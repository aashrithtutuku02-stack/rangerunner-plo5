"""Fail on omitted, malformed or faulted full judge reports."""
import json
from pathlib import Path
import sys

root=Path(sys.argv[1])
files=list(root.glob('*.json'))
assert files, f'No judge reports in {root}'
for path in files:
    result=json.loads(path.read_text())
    assert result['num_deals']==1000,(path,'not a full match')
    for player in ('agent1','agent2'):
        assert len(result['agent_stats'][player])==2
        for half in result['agent_stats'][player]:
            assert not half['errors'],(path,player,half)
            assert not half['forfeited'],(path,player,half)
            assert not half['timed_out'],(path,player,half)
            assert not half['skipped_calls'],(path,player,half)
    if path.stem.split('-')[0] in ('random','calling_station','always_half','always_pot'):
        assert result['verdict']=='AGENT1_WIN',(path,result['verdict'])
print(f'{len(files)} full matches: no errors, forfeits, exhausted banks or skipped decisions.')
