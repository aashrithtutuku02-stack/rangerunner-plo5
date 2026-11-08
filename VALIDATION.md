# Release validation — iteration 4

Measured November 7, 2026, America/Chicago; raw runtime logs may use November 8
UTC. Historical evidence remains available. This release is compared with
[`f452b09`](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/commit/f452b09e8ebd6fd6eb9d17035f41e5b626712fcb),
whose [validation report](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/blob/f452b09e8ebd6fd6eb9d17035f41e5b626712fcb/VALIDATION.md)
is retained. Current raw reports are under `validation/iteration4/`.

## Issues reproduced and fixed

Seven new replay/lifecycle cases failed against the previous release. The
original failures are preserved in `iteration4/development-replay-failures-f452.txt`.
The release now prevents stale history prefixes from rewinding learning,
prevents old requests from reopening completed hands, makes duplicate results
idempotent, clears reused half-memory dictionaries, and preserves samples under
equivalent hole/flop orderings. It also handles a direct callback before policy
initialization without poisoning later startup.

Additional recovery tests verify that failed decisions and failed result
processing restore learning and random state before a corrected retry. Completed
hands and history prefixes are tracked only in per-half memory. Turn and river
arrival order remain significant. The original server continues to report
request/result errors; they are not hidden. Calculation time is still included
in the internal budget estimate.

The registered name remains **winner**. The betting model, its numeric value
formula, engine, preflop asset and server plumbing are unchanged from f452.

## Exhaustive betting histories, within a defined scope

[SCENARIO_COVERAGE.md](SCENARIO_COVERAGE.md) defines the claim and assumptions.
For each fixed deal and button position, every legal action from every history
prefix is followed. No distinct history is merged, including separate raise
labels that happen to clip to the same all-in target.

At the supplied 80-chip, 1/2-blind, four-raise-cap rules, each sweep covers
15,952 decision prefixes, 25,538 complete histories, 41,489 edges, 678 numeric
states and at most 14 actions. Eight fixed deals and both buttons produced:

| Check | Total |
|---|---:|
| Complete terminal histories | 408,608 |
| Decision prefixes evaluated by the policy | 255,232 |
| Repeated decisions checked | 255,232 |
| Terminal-response inference checks | 817,216 |
| Duplicate results checked | 817,216 |
| Learning-state comparisons to referee-derived events | 1,072,448 |

Every chosen action was legal, learned state was finite and normalized, and
opponent prices/contexts/raise opportunities matched the public referee events.
Default 768/1,280-sample calculation was used throughout. The shared host's
largest observed calculation in this sweep was about 0.059 seconds; these are
offline measurements, not an HTTP timing certificate.

The deals cover random cards, an unbeatable flush, the A6789 wheel, quads, a
split, four equal board ranks, four equal hole ranks, and flush over full house.
The pure supplied terminal evaluator is memoized by exact input cards; game
transition, visibility and payment code remain unchanged. The bot is evaluated
at every prefix and then every legal continuation is forced. This is
counterfactual correctness coverage, not a win rate or independent matches.

Reports include exact source identities, card inputs, coverage counts and the
complete action-sequence digest. The checker rejects missing cases/buttons,
accounting-only reports, incomplete counts, altered digests and mixed versions:

```sh
python tools/check_scenarios.py validation/iteration4/scenarios --check-source
```

## Automated tests

**217 tests passed.** In addition to the unchanged supplied tests, the suite
includes all 376,992 five-card rankings, native/fallback sampling and input
guards, exhaustive history-accounting tests, replay recovery and deep half
resets. The HTTP matrix covers 72 endpoint/startup/token/body combinations,
with additional batched-result and corrected-retry cases. Budget tests cover
full, half and minimum counts on all streets, plus cache reuse after a budget
drop. Exact scoring invariance is checked under hole/flop order and all 24 suit
renamings on the card corpus. Hidden opponent/future cards are altered in 192
public-frame comparisons across roles and streets, without changing decisions.
Two local warnings concern third-party pytest/Starlette deprecations.

Malformed requests have their expected error/refusal statuses; those deliberate
negative tests are separate from the fault-free match results below.

## Playing performance and preserved regular behavior

The final performance cohort contains **164,000 physically played hands**,
including controls: 136,000 in matched comparisons against 34 opponents,
24,000 in real HTTP matches, 2,000 with restarted processes, and 2,000 in the
one-CPU HTTP match. The forced longest-line load is counted separately. Shared
and duplicate deals are reused, so this is not a count of independent deals.

All 26 named local policies and eight selected parameter-search cases were used
on one new 1,000-deal seed. Each current policy and frozen control plays both
seats. **All 34,000 paired score differences were exactly zero**, preserving
returns on the tested ordinary-play suite. Those observations share 1,000
underlying deal clusters. The frozen source redirects only its helper import;
that helper, bet kernel and engine are byte-identical to their f452 versions.

The candidate's descriptive interval verdicts were **29 wins,
5 draws, 0 losses**. These are finite local-test
results, not a simultaneous statistical guarantee. All challengers share project
code and equity calculations; no independent elite engine was tested.

| Opponent | Mean bb/deal | Descriptive 95% interval | Verdict |
|---|---:|---|---|
| balanced | +2.200 | [+1.405, +2.995] | Win |
| bluffer | +6.492 | [+5.177, +7.807] | Win |
| call | +11.070 | [+10.084, +12.057] | Win |
| checkraise | +2.202 | [+1.482, +2.922] | Win |
| fold | +1.500 | [+1.500, +1.500] | Win |
| half | +13.687 | [+12.504, +14.870] | Win |
| incumbent | +0.108 | [-0.423, +0.639] | Draw |
| loose | +5.240 | [+4.120, +6.360] | Win |
| maniac | +8.169 | [+6.712, +9.626] | Win |
| nit | +1.268 | [+0.879, +1.658] | Win |
| opportunist | +1.806 | [+0.945, +2.666] | Win |
| oscillating | +3.113 | [+2.091, +4.135] | Win |
| overfolder | +1.236 | [+0.851, +1.621] | Win |
| polarized | +2.987 | [+2.209, +3.766] | Win |
| pot | +8.283 | [+6.707, +9.859] | Win |
| random | +10.169 | [+8.602, +11.737] | Win |
| range-aware | +0.206 | [-0.543, +0.955] | Draw |
| range-flat | +9.662 | [+8.244, +11.080] | Win |
| range-tight | +0.293 | [-0.263, +0.849] | Draw |
| release-b15a | +0.000 | [+0.000, +0.000] | Draw |
| release-f452 | +0.000 | [+0.000, +0.000] | Draw |
| search000 | +1.010 | [+0.267, +1.752] | Win |
| search005 | +1.060 | [+0.513, +1.606] | Win |
| search013 | +2.204 | [+1.612, +2.795] | Win |
| search014 | +1.679 | [+1.196, +2.163] | Win |
| search021 | +1.079 | [+0.764, +1.393] | Win |
| search022 | +1.616 | [+1.142, +2.090] | Win |
| search024 | +1.286 | [+0.796, +1.775] | Win |
| search030 | +1.440 | [+0.972, +1.908] | Win |
| smallball | +2.991 | [+2.244, +3.738] | Win |
| sticky | +6.659 | [+5.624, +7.694] | Win |
| switcher | +3.926 | [+2.948, +4.905] | Win |
| tight | +2.184 | [+1.577, +2.791] | Win |
| trapper | +2.494 | [+1.767, +3.220] | Win |

Raw paired returns, source fingerprints and summary are in
`iteration4/regression/`. This release claims a reliability improvement;
it does not claim a new poker win-rate gain.

## Actual HTTP judge and fresh processes

The 12 real matches used the unchanged referee, separate servers, its 8-second
bank, 1-second request deadline and 5-error forfeit limit. **Both players in all
matches had zero errors, forfeits, exhausted banks and skipped decisions.**
All four supplied baselines were beaten. Advanced draws remain visible.
The bot's identity was `winner / RangeRunner`.

| Opponent | Mean bb/deal | 95% interval | Max charged time/half | Verdict |
|---|---:|---|---:|---|
| adversary-bluffer | +5.244 | [+3.956, +6.531] | 1.56 s | AGENT1_WIN |
| adversary-checkraise | +2.277 | [+1.493, +3.062] | 1.58 s | AGENT1_WIN |
| adversary-nit | +1.268 | [+0.833, +1.702] | 1.49 s | AGENT1_WIN |
| adversary-opportunist | +2.619 | [+1.743, +3.494] | 1.47 s | AGENT1_WIN |
| adversary-range-tight | +0.038 | [-0.539, +0.615] | 1.38 s | CHOP |
| adversary-release-f452 | +0.000 | [+0.000, +0.000] | 1.97 s | CHOP |
| adversary-switcher | +3.399 | [+2.412, +4.386] | 1.52 s | AGENT1_WIN |
| always_half | +12.819 | [+11.604, +14.034] | 1.48 s | AGENT1_WIN |
| always_pot | +6.552 | [+5.001, +8.103] | 1.15 s | AGENT1_WIN |
| calling_station | +11.549 | [+10.575, +12.523] | 1.29 s | AGENT1_WIN |
| random | +10.204 | [+8.589, +11.818] | 1.29 s | AGENT1_WIN |
| reference_agent | +3.782 | [+3.091, +4.473] | 1.78 s | AGENT1_WIN |

Returns are big blinds per duplicate deal, summing both seat-swapped hands.
Intervals are ordinary judge-style 95% normal intervals, not exact bounds for
adaptive learning. Raw reports are in `iteration4/http/`.

Restarting both servers between duplicate halves against the frozen previous
release returned +0.000 bb/deal,
[+0.000, +0.000], CHOP, with zero
faults and skipped calls. See `iteration4/fresh-process/`.

## Restricted runtime

The current source passed the supplied smoke test with network disabled,
read-only files, user 10001, writable 512 MB `/tmp`, one CPU, 4 GB RAM, dropped
capabilities, no-new-privileges and a 256-PID limit. Startup took about 1.8 seconds.
The supplied synthetic fixtures contain out-of-order hand IDs, so some responses
exercise stale-request fallbacks. Their low latency is an interface check;
full-policy calculation evidence comes from valid histories, matches and the
longest-line run. See `iteration4/offline-smoke.txt`.

A separate full HTTP match gave the bot its own one-CPU/4-GB read-only container,
with CallingStation and the judge on the host. The result was
+11.4645 bb/deal, interval [+10.476, +12.453].
Charged half times were **2.090 and 2.174 seconds of 8**.
Both players had zero faults and skipped decisions. The exact local invocation
is preserved in `iteration4/cpu-check.py` alongside `single-cpu.*`.

The separate one-CPU load test forces a longest legal fourteen-action line for
1,000 random deals, alternating buttons, while evaluating both bots and their
result callbacks. All 14,000 decisions and 2,000 result calculations succeeded.
Measured calculation totals were **3.255
and 3.273 seconds per player**, and the
largest call took **0.052 seconds**. These totals exclude
HTTP and are not a strength benchmark: the evaluated actions are overridden to
reach the long line. Full/half/minimum samples adapt to the 8-second accounting
budget. See `iteration4/worst-line-load.json` and `tools/worst_line_load.py`.

Runtime source, native binary and asset hashes matched the release; runtime
inspection verified the new lifecycle fields, portable C backend, team name and
absence of research-feature imports. See `iteration4/runtime-source-sha256.json`
and `runtime-identity.json`. Local resource checks used the cached small sandbox
image with current source mounted read-only and unchanged dependencies.

GitHub Actions independently runs 217 tests, both full eight-deal history sweeps,
12 real HTTP matches, a fresh-process match, the unchanged full organizer build,
image-size and restricted smoke checks, plus the longest-line load in that exact
organizer image. Check the pushed commit's
[workflow result](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/actions/workflows/validate.yml).
Local sandbox results do not substitute for the organizer build.

Final resource checks ran serially on the two-core development parent with CPU
capacity available. A CPU quota is a maximum, not an exclusive reservation.

## Integrity and limits

The original rules, evaluator, referee, supplied protocol tests, organizer
Dockerfiles/build checker, server plumbing, card engine, native binary, asset
and bet-value kernel are unchanged from f452. Verified paths are in
`iteration4/protected-files.json`; the source manifest identifies release files
outside the evidence directory.

The complete-history claim applies to the selected fixed deals at the current
rules. Card arrangements exceed 505 quadrillion before betting histories. This
suite does not enumerate them all, every JSON value, unbounded retry sequence,
network schedule, hardware fault or arbitrary rule change. It assumes the
referee's single active half and increasing hand indices; ambiguous cross-half
packets cannot always be identified without an episode ID. Real halves use
fresh processes. The limitations and remaining strategic weaknesses are explicit
in [SCENARIO_COVERAGE.md](SCENARIO_COVERAGE.md) and
[WEAKNESSES.md](WEAKNESSES.md). The game remains unsolved and no universal win
guarantee follows from these tests.
