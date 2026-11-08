"""Summarize paired policy changes without counting shared deals repeatedly."""
import argparse
import json
from pathlib import Path
import statistics


def interval(values):
    mean=statistics.mean(values)
    se=statistics.stdev(values)/len(values)**.5 if len(values)>1 else 0.
    return mean,[mean-1.96*se,mean+1.96*se]


def summarize(rows):
    assert rows,'No paired comparison records'
    opponents={r['opponent'] for r in rows}
    seen=set();groups={};by_opponent={};sources=set();extras=set();modes=set();baselines=set();policies=set()
    for r in rows:
        key=(r['opponent'],r['seed']);assert key not in seen,'Duplicate opponent/seed'
        seen.add(key)
        assert r['sample_mode'] in ('fixed-default-counts','fixed-policy-sampling')
        modes.add(r['sample_mode']);baselines.add(r.get('baseline_policy','incumbent'))
        policies.add(r.get('policy','unspecified'))
        sources.add(json.dumps(r['source_sha256'],sort_keys=True))
        extras.add(json.dumps(r.get('additional_source_sha256',{}),sort_keys=True))
        assert len(r['delta'])==len(r['candidate']['paired'])==len(r['baseline']['paired'])
        for i,(delta,new,old) in enumerate(zip(r['delta'],r['candidate']['paired'],r['baseline']['paired'])):
            assert abs(delta-(new-old))<1e-12
            groups.setdefault((r['seed'],i),{})[r['opponent']]=delta
        by_opponent.setdefault(r['opponent'],[]).extend(r['delta'])
    assert len(sources)==1,'Mixed source versions'
    assert len(extras)==1,'Mixed additional source versions'
    assert len(modes)==1,'Mixed sampling modes'
    assert len(baselines)==1,'Mixed baseline policies'
    assert len(policies)==1,'Mixed candidate policies'
    assert all(set(group)==opponents for group in groups.values()),'Incomplete shared-deal grid'
    clustered=[statistics.mean(group.values()) for group in groups.values()]
    mean,ci=interval(clustered)
    per_seed=[]
    for seed in sorted({key[0] for key in groups}):
        values=[statistics.mean(group.values()) for (name,_),group in groups.items() if name==seed]
        per_seed.append(dict(seed=seed,mean_change=statistics.mean(values),deals=len(values)))
    details=[]
    for name,values in sorted(by_opponent.items()):
        m,c=interval(values);details.append(dict(opponent=name,change=m,ci=c,deals=len(values)))
    return dict(mean_change=mean,ci=ci,opponents=len(opponents),independent_deal_clusters=len(clustered),
                paired_policy_observations=sum(len(r['delta']) for r in rows),
                played_hands=4*sum(len(r['delta']) for r in rows),
                per_seed=per_seed,per_opponent=details,source_sha256=json.loads(next(iter(sources))),
                additional_source_sha256=json.loads(next(iter(extras))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output')
    a=p.parse_args();rows=[]
    for path in Path(a.directory).glob('*.json'):
        obj=json.loads(path.read_text())
        if isinstance(obj,dict) and 'delta' in obj:rows.append(obj)
    text=json.dumps(summarize(rows),indent=2)+'\n'
    if a.output:Path(a.output).write_text(text)
    print(text)
