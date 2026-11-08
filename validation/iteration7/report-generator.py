from pathlib import Path
import json,statistics,hashlib,shutil,sys
root=Path('/workspace/work/rangerunner');sys.path.insert(0,str(root))
from tools.summarize_comparison import summarize,interval
out=root/'validation/iteration7';protocol=json.loads((out/'final-holdout-protocol.json').read_text())
for name,h in protocol['source_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==h,name
rows=[];dest=out/'final-holdout';dest.mkdir(exist_ok=True)
for label in ('ac','bd'):
 for path in Path('/workspace/work/iteration7-holdout-'+label).glob('*.json'):
  r=json.loads(path.read_text())
  if not isinstance(r,dict) or 'delta' not in r:continue
  assert len(r['delta'])==1000
  for key in ('baseline','candidate'):
   assert set(r[key]['sampling']['samples_per_decision'])<={'768','1280'}
   assert not r[key]['sampling']['expanded_boards']
   assert r[key]['sampling']['max_response_window']<=64
  assert not r['baseline']['sampling']['calling_read_decisions']
  if not r['candidate']['sampling']['calling_read_decisions']:assert not any(r['delta'])
  rows.append(r);shutil.copyfile(path,dest/path.name)
assert len(rows)==96
assert {(r['opponent'],r['seed']) for r in rows}=={(o,s) for o in protocol['opponents'] for s in protocol['seeds']}
s=summarize(rows);seed_means=[r['mean_change'] for r in s['per_seed']]
seed_mean=statistics.mean(seed_means);err=3.182446305284263*statistics.stdev(seed_means)/2
s['seed_t_ci']=[seed_mean-err,seed_mean+err]
assert s['ci'][0]>0 and s['seed_t_ci'][0]>0,'Frozen evaluation failed acceptance criteria'
head=next(r for r in s['per_opponent'] if r['opponent']=='release-9efa');assert head['ci'][1]>=0
scores=[]
for name in protocol['opponents']:
 records=[r for r in rows if r['opponent']==name]
 values=[v for r in records for v in r['candidate']['paired']]
 score,ci=interval(values);change=next(x for x in s['per_opponent'] if x['opponent']==name)
 scores.append(dict(opponent=name,score=score,ci=ci,change=change['change'],change_ci=change['ci'],
  read_decisions=sum(r['candidate']['sampling']['calling_read_decisions'] for r in records),
  read_hands=sum(r['candidate']['sampling']['calling_read_hands'] for r in records)))
s['scores']=scores
(out/'final-holdout-summary.json').write_text(json.dumps(s,indent=2)+'\n')
assert '306 passed' in (out/'unit-tests.txt').read_text()

def match(path):
 r=json.loads(path.read_text());assert r['kind']=='match_result' and r['num_deals']==1000
 for player in ('agent1','agent2'):
  for half in r['agent_stats'][player]:assert not any(half[k] for k in ('errors','skipped_calls','timed_out','forfeited'))
 return r
old=match(out/'cpu/release-9efa/match.json');new=match(out/'cpu/release/match.json')
assert old['verdict']==new['verdict']=='AGENT1_WIN'
delta=[a-b for a,b in zip(new['paired_bb'],old['paired_bb'])];cpu_gain,cpu_ci=interval(delta)
(out/'cpu-comparison.json').write_text(json.dumps(dict(previous=old['mean_bb_per_deal'],candidate=new['mean_bb_per_deal'],change=cpu_gain,ci=cpu_ci,delta=delta,scope='One matched seed, both seats; real 8-second bank, hero constrained to one CPU/4GB; adaptive sampling may differ'),indent=2)+'\n')
load=json.loads((out/'worst-line-load.json').read_text());assert max(load['policy_calculation_seconds'])<8 and load['max_call_seconds']<1
identity=json.loads((out/'runtime-identity.json').read_text());assert identity['participant']=='winner' and identity['calling_read_initialized'] and not identity['research_imports']
http=[(p.stem,match(p)) for p in (out/'http').glob('*.json')];assert len(http)==8
fresh=match(out/'fresh-process/combined.json')
external=[]
for bot in ('fargield','starfish'):
 values=[];matches=[];fallbacks=0
 for seed in ('a','b'):
  folder=out/'external-final'/seed/bot;r=match(folder/'combined.json');values.extend(r['paired_bb'])
  matches.append(dict(seed=seed,score=r['mean_bb_per_deal'],ci=r['ci'],verdict=r['verdict']))
  for half in (1,2):
   meta=json.loads((folder/'external-status'/f'half{half}.json').read_text())
   assert meta['core_available'] and not meta['caught_model_errors'] and not meta['callback_errors']
   if meta['native_diagnostics']:assert not any(meta['native_diagnostics'][n] for n in ('fault_events','fallback_decisions','disabled'))
   fallbacks+=meta['fallback_calls']
 score,ci=interval(values);external.append(dict(opponent=bot,score=score,ci=ci,matches=matches,fallback_calls=fallbacks,deals=len(values)))
(out/'external-summary.json').write_text(json.dumps(external,indent=2)+'\n')
changed=[r for r in scores if r['change']!=0]
zero=[r['opponent'] for r in scores if r['change']==0]
caller_names={'call','passive-value','passive-trap','caller-switcher','caller-oscillating'}
caller_table='\n'.join(f"| {r['opponent']} | {r['score']:+.3f} | {r['change']:+.3f} | [{r['change_ci'][0]:+.3f}, {r['change_ci'][1]:+.3f}] |" for r in scores if r['opponent'] in caller_names)
seed_table='\n'.join(f"| {r['seed'].rsplit('-',1)[1]} | {r['mean_change']:+.5f} |" for r in s['per_seed'])
http_table='\n'.join(f"| {name.removesuffix('-iteration7-http-final')} | {r['mean_bb_per_deal']:+.3f} | {r['verdict']} |" for name,r in sorted(http))
external_table='\n'.join(f"| {r['opponent']} | {r['score']:+.3f} | [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}] | {sum(x['verdict']=='AGENT1_WIN' for x in r['matches'])} / {sum(x['verdict']=='CHOP' for x in r['matches'])} / {sum(x['verdict']=='AGENT2_WIN' for x in r['matches'])} |" for r in external)
text=f'''# Release validation — iteration 7

Team **winner**, agent **RangeRunner**. The baseline is frozen release
`9efa86c1b7a6557be6b4cb508cced6d57a38432b`.

## Measured strategic improvement

The new caller read improved the equal-opponent average by **{s['mean_change']:+.5f}
big blinds per duplicate deal** across 24 local opponents and four fresh seeds.
The descriptive shared-deal 95% interval is **[{s['ci'][0]:+.5f}, {s['ci'][1]:+.5f}]**;
the separate four-seed t interval is **[{s['seed_t_ci'][0]:+.5f}, {s['seed_t_ci'][1]:+.5f}]**.
The gains are concentrated in frequent-caller and changing-caller matchups.
This is a targeted exploit, not a demonstrated gain against elite bots or every
opponent. A duplicate deal sums the two seat-swapped hands, following the
supplied referee's convention.

The bot records only voluntary responses to bets. Free checks and forced calls
cannot establish that an opponent prefers calling. Folds remain negative
evidence even when raising was unavailable. At least 24 eligible responses are
required, using the latest 64. A Wilson lower call-share bound of 0.80 activates
the read. Only estimated value bets with equity above one half can then omit
the fixed raise safety margin. Other decisions preserve the previous guard;
range mathematics, equity samples, equity realization and re-raise penalties
are unchanged. [CALLING_READ.md](CALLING_READ.md) explains the rule and limits.

## Frozen fresh evaluation

The candidate, source identities, acceptance conditions, 24 opponents and four
new 1,000-deal seeds were recorded before evaluation. No parameter changed after
that point. [Protocol](validation/iteration7/final-holdout-protocol.json),
[all 96 records](validation/iteration7/final-holdout/) and
[summary](validation/iteration7/final-holdout-summary.json) are retained.

Each candidate and frozen control plays both seats on common deals:
**384,000 physical hands including controls**, 96,000 paired policy observations,
sharing **4,000 card-deal clusters**. The pooled interval groups opponents that
share a deal; it does not count the 24 opponents as independent new cards.
A second interval uses four seed means and Student t with three degrees of
freedom. Learning creates dependence between successive hands, so intervals
are descriptive rather than guarantees.

| Fresh seed | Equal-opponent gain, bb/deal |
|---|---:|
{seed_table}

| Calling style | Candidate bb/deal | Change from 9efa | Paired-change 95% interval |
|---|---:|---:|---|
{caller_table}

**{len(zero)} opponent matchups had exactly unchanged paired returns** across
all four seeds. Frozen-release head-to-head change was {head['change']:+.5f}
with interval [{head['ci'][0]:+.5f}, {head['ci'][1]:+.5f}]. All per-opponent scores,
intervals, read-activation counts and any negative estimates remain in the
summary and raw records. There is no claim of a new head-to-head win over the previous release.

Offline comparisons use an 80-second accounting bank to retain the original
768/1,280 sample counts independently of host scheduling. No experimental sample
expansion occurred. Comparisons with no active read preserve
every paired return. Real 8-second behavior is checked separately.

## Other ideas tested

An unconditional removal of the raise margin initially gained +0.5283 bb/deal
on ten discovery opponents, then declined -0.0997 on a new twenty-opponent
cohort. Applying the margin once between passive play and all raises declined
-0.1358 on the first cohort. Separate pre/postflop selectivity models were also
mixed: independent group mixtures gained +0.0756 initially, then declined
-0.0582 on the broader cohort. These alternatives remain disabled.

Value-only margin removal and the guarded caller rule were compared on a third
24-opponent discovery cohort. The guarded version preserved all nineteen
non-passive returns, had positive point estimates for all five caller styles,
and was selected for the fresh evaluation. This selection was based on its
narrower behavioral scope, rather than the largest discovery mean. No fresh
seed was reused for selection. Raw results and changed-source snapshots are in
[iteration 7 evidence](validation/iteration7/README.md).

## Correctness and history coverage

**306 tests passed** on the final candidate, with two third-party deprecation
warnings. New tests cover the eligibility of calls and folds, confidence and
recent behavior changes, value/bluff separation, atomic rollback, half resets,
raise-size ranking, independent group learning and the frozen prototype mirror.
The original supplied referee, evaluator, server and starter tests are unchanged.
One older experimental test now compares its frozen re-raise prototype against
its frozen control, so the new caller policy does not silently redefine that
experiment's negative control.

GitHub repeats every legal betting history on eight fixed deals and both button
positions: **408,608 terminal histories**, **255,232 decision prefixes**, with
replayed decisions, terminal inference and duplicate results. The sweep now also
checks the caller-read tuple against independently recorded referee events at
all **1,072,448 learning-state comparisons**. Its artifact checker rejects missing
read coverage and checks exact source identities, including `calling_read.py`.

A single hand has fewer than 24 eligible responses, so those one-hand sweeps
verify construction and replay safety of the read. Dedicated multi-hand tests,
ordinary matches and the fresh cohort exercise its activation and invalidation.
This is exhaustive history coverage for the selected fixed deals, not all card
deals, opponents or possible API traffic. [SCENARIO_COVERAGE.md](SCENARIO_COVERAGE.md)
defines the boundary.

## Real bank and one-CPU validation

Both frozen 9efa and the candidate played CallingStation on the same new
1,000-deal seed with hero limited to one CPU, 4 GB RAM and read-only source,
using the real HTTP referee and 8-second banks. Both won, with zero faults,
forfeits, exhausted banks and skipped calls on either side.

| Policy | bb/deal | Charged seconds, half 1 | Half 2 |
|---|---:|---:|---:|
| Frozen 9efa | {old['mean_bb_per_deal']:+.3f} | {old['agent_stats']['agent1'][0]['time_seconds']:.3f} | {old['agent_stats']['agent1'][1]['time_seconds']:.3f} |
| Caller read | {new['mean_bb_per_deal']:+.3f} | {new['agent_stats']['agent1'][0]['time_seconds']:.3f} | {new['agent_stats']['agent1'][1]['time_seconds']:.3f} |

The one-seed paired change was {cpu_gain:+.3f} bb/deal, interval
[{cpu_ci[0]:+.3f}, {cpu_ci[1]:+.3f}]. This is a small real-budget check; scheduling
can change adaptive sample allocation. The four-seed fixed-sample evaluation
above provides the main comparison. Raw reports, command lines and source
identities are retained under `validation/iteration7/cpu/`.
The initial baseline attempt failed before play because its research server
bound the container loopback interface. The harness now binds that unchanged
app to the container interface; the same policy/cards were rerun successfully.
Those transport-forfeit reports are retained in `development-cpu-startup/`
and excluded from strength comparisons. No frozen policy or evaluation
parameter changed for this repair.

A network-disabled longest-line load evaluated all **14,000 decisions and 2,000
result callbacks** over 1,000 forced fourteen-action hands. Per-player calculation
totals were {load['policy_calculation_seconds'][0]:.3f} and
{load['policy_calculation_seconds'][1]:.3f} seconds; the largest call was
{load['max_call_seconds']:.4f} seconds. The response window remained bounded.
This excludes HTTP and overrides chosen actions, so it is a resource test rather
than playing-strength evidence.

Eight ordinary full HTTP matches passed fault checks, including all four
supplied baselines, which were beaten:

| Opponent | bb/deal | Verdict |
|---|---:|---|
{http_table}

Restarting both servers before each half against 9efa returned
{fresh['mean_bb_per_deal']:+.3f} bb/deal ({fresh['verdict']}). Restricted smoke also
passed with user 10001, one CPU, 4 GB RAM, network disabled, read-only source,
dropped capabilities, no-new-privileges, 256 PIDs and writable 512-MB `/tmp`.
Runtime inspection verified winner / RangeRunner, portable C, lifecycle guards,
original five-model weights, the initialized caller read, no research imports
and exact source/native/asset fingerprints. Local checks use the cached small
sandbox with current source mounted read-only and unchanged dependencies.

## Independent public opponents

Two pinned, independently developed public challenge bots ran with their own
published default strategies in separate interpreters. Both restarted before
every half, with active-core, asset, caught-exception and native-fault diagnostics.
Two new seeds per bot produced **8,000 physical hands** under the original judge.

| Public bot | bb/deal | Descriptive 95% interval | Wins / draws / losses, two seeds |
|---|---:|---|---|
{external_table}

Both players' referee fault counters were zero. Per-half metadata retains source
hashes verified against the pinned Git commits and all fallback counters.
These matches assess the release, not a controlled gain over 9efa. The public
bots' tournament rank and elite strength are unknown. Their code is not
redistributed. [EXTERNAL_BENCHMARKS.md](EXTERNAL_BENCHMARKS.md) records the versions
and reproduction steps.

## Release integrity and limits

GitHub checks the exact organizer build, image-size cap, restricted smoke and
one-CPU longest-line test, plus 306 tests, twenty full HTTP matchups, a
fresh-process match and both complete history jobs. Check the workflow on this
exact commit for its final status. Local results and protected-file fingerprints
are under [iteration 7](validation/iteration7/).

This release adds a targeted opponent read; it does not solve poker. The read can
lag an opponent changing behavior, and calling preferences may depend on price,
street and range. The Wilson threshold is a conservative heuristic under
dependent observations. Equity and future betting remain approximate. See
[WEAKNESSES.md](WEAKNESSES.md). No result here establishes an unbeatable bot.
Earlier full reports remain in [iteration 6](validation/iteration6/RELEASE_REPORT.md)
and [iteration 5](validation/iteration5/RELEASE_REPORT.md).
'''
(root/'VALIDATION.md').write_text(text)
(out/'README.md').write_text('''# Iteration 7 evidence

The released candidate uses a conservative rolling read of frequent callers.
See the root [validation report](../../VALIDATION.md) and [calling-read design](../../CALLING_READ.md).

* `final-holdout-protocol.json`: source identities, acceptance criteria, 24 local
  opponents and four fresh 1,000-deal seeds recorded before evaluation.
* `final-holdout/` and `final-holdout-summary.json`: all 96 paired comparison
  records, shared-deal intervals, four-seed t interval and read activation counts.
* `final-source/`: changed comparison sources frozen before the cohort. Other
  unchanged dependencies are recoverable from baseline commit 9efa86c.
* `unit-tests.txt`: 306 final tests passed. The descriptive development unit log
  retains an old experimental negative-control test that initially compared the
  changing production policy instead of its frozen re-raise prototype; that
  isolation is corrected in the final tests.
* `runtime-protocol.json`, `runtime-checks.py`, `runtime-identity-check.py`,
  `runtime-identity.json`, `worst-line-load.json`, `offline-smoke.txt`: serial
  restricted-runtime checks and exact source identities. `runtime-resume.py`
  resumes the HTTP checks after the baseline Docker binding repair.
* `development-cpu-startup/`: original unreachable-baseline reports and the
  original harness. These are transport failures, not playing-strength evidence.
* `cpu/` and `cpu-comparison.json`: matched-seed old/new one-CPU HTTP matches.
* `http/`, `fresh-process/` and `external-final/`: original real-bank referee
  reports, fresh servers between halves and independent public-bot diagnostics.

Development cohorts remain separate from fresh evaluation:

* `discovery/margin-once-a`, `margin-none-a`: 600 deals × ten opponents, seed a.
* `street-split-b`, `street-mix-b`: 600 deals × ten opponents, separate seed b.
* `margin-none-c`, `street-mix-c`: 800 deals × twenty opponents, common seed c.
* `margin-value-d2`, `margin-passive-d2`: 600 deals × 24 opponents, common seed d2.
* `initial-calling-draft/`: incomplete discovery stopped to retain capped/all-in
  folds as negative evidence. Its original helper and partial records remain.
* `source-initial`, `source-broad`, `source-calling`: exact changed research
  sources for their respective phases; original dependencies remain in 9efa86c.

Each paired policy observation uses four physical hands: both seats for both
candidate and control. Opponents sharing a seed use the same deals. The pooled
summary clusters shared deals instead of counting each opponent as independent
new cards. Learning creates additional dependence; intervals are descriptive.
All rejected experiments remain disabled in production. No external bot source
is copied into this repository.
''')
print(json.dumps(dict(gain=s['mean_change'],ci=s['ci'],seed_t_ci=s['seed_t_ci'],zero_matchups=len(zero),changed=changed,cpu_gain=cpu_gain,external=external),indent=2))
