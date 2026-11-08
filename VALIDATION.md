# Release validation — iteration 3

Measured November 7, 2026, America/Chicago. Some raw runtime logs use November 8
UTC. Historical reports and evidence remain available, including the
[previous release report](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/blob/b15a8402286cb93f901c84f3eabd2911be5784ea/VALIDATION.md).
Current evidence is under `validation/iteration3/`.

## Delivered changes

The registered team identity defaults to **winner**. The only `agent.py` change
is that default; its original server plumbing, token handling and port settings
are preserved.

`bet_ev.py` compiles the joint model/hand expectation for both raise sizes,
avoiding repeated probability arrays and Python dispatch. Identical clipped
all-in targets share one calculation. The learned opponent model and betting
policy formula are retained from release `b15a840`.

The fixed-workload numeric benchmark measured **1.76x** throughput for
ordinary two-size evaluation and **5.24x** for duplicate all-in sizes.
These are component microbenchmarks, not whole-bot speed multipliers. Seven
repeats of 300 evaluations used 1,280 samples and checked the compiled results
against the frozen vector formula before timing. Raw timings, source hashes and
reproduction code are in `iteration3/kernel-timing.json` and
`tools/measure_bet_ev.py`.

## Tests and final regression

**110 automated tests passed.** Coverage includes the unchanged supplied HTTP
protocol tests, all 376,992 five-card rankings against the supplied evaluator,
native/fallback sample equivalence, invalid native inputs, 678 reachable numeric
betting states for one fixed legal deal, calibrated likelihoods and posterior
arithmetic, verified terminal learning and raise opportunities, compiled/vector
raise-value equivalence, frozen-policy controls and comparison-summary guards.
Research tests also check numeric river-tree transitions/payoffs, information-set
decisions, contextual learning and auxiliary sampling. Those research features
remain disabled in production. Two local warnings concern third-party
pytest/Starlette deprecations. The updated analysis guard passed separately too.

The final local cohort contains **124,000 physically played hands**, including
controls: 96,000 in paired regression, 24,000 through the actual HTTP judge,
2,000 with fresh processes and 2,000 in a one-CPU container. These are not
124,000 independent deals. Duplicate and common deals are intentionally reused.
Numerical estimator trials are not counted as played hands.

The paired regression uses 12 opponents on two new 1,000-deal seeds. Both the
new calculation and frozen release play each opponent on the same cards, for
24,000 paired policy observations across 2,000 shared-deal clusters.
**Every paired score change is exactly zero.** The frozen self-controls also
return zero. This verifies preserved returns on the tested suite; it is not a
new win-rate gain or a guarantee for all inputs, runtimes or opponents.

The opponents are the previous release, nit, balanced, checkraise, polarized,
opportunist, oscillating, switcher, search000, search024, pot and call.
The previous strategy and helper are byte-preserved under `opponents/`, apart
from redirecting the helper import. They share the unchanged card engine and
preflop asset. Offline comparisons use an 80-second internal accounting budget
to prevent CPU scheduling from reducing requested samples. They do not enforce
tournament timing; the actual 8-second tests are separate.

Raw records, source identities, per-deal returns and summary:
`iteration3/regression/`. Reproduce the analysis:

```sh
python tools/summarize_comparison.py validation/iteration3/regression
```

The summarizer rejects mixed source versions, candidates, baselines and sample
modes, duplicate cases and incomplete shared-deal grids. Pool uncertainty groups
opponents sharing the same seed/deal before calculating a normal interval.

## Actual HTTP judge

All 12 full matches used separate servers and the unchanged referee, with the
real 8-second bank, 1-second request deadline and 5-error forfeit rule.
**Both players in every match had zero errors, forfeits, exhausted banks and
skipped decisions.** All four supplied baselines were beaten. Advanced draws
remain visible. Both the health check and judge reports identify the bot as
`winner / RangeRunner`. Raw reports are in `iteration3/http/`.

| Opponent | Mean bb/deal | 95% interval | Max charged time/half | Verdict |
|---|---:|---|---:|---|
| adversary-bluffer | +5.631 | [+4.298, +6.964] | 1.54 s | AGENT1_WIN |
| adversary-checkraise | +2.961 | [+2.225, +3.697] | 1.62 s | AGENT1_WIN |
| adversary-nit | +1.517 | [+1.107, +1.927] | 1.42 s | AGENT1_WIN |
| adversary-opportunist | +2.619 | [+1.744, +3.494] | 1.41 s | AGENT1_WIN |
| adversary-range-tight | +0.237 | [-0.308, +0.782] | 1.27 s | CHOP |
| adversary-release-b15a | +0.000 | [+0.000, +0.000] | 1.50 s | CHOP |
| adversary-switcher | +2.686 | [+1.735, +3.636] | 1.61 s | AGENT1_WIN |
| always_half | +14.211 | [+13.012, +15.410] | 1.55 s | AGENT1_WIN |
| always_pot | +7.643 | [+6.118, +9.168] | 1.13 s | AGENT1_WIN |
| calling_station | +11.232 | [+10.263, +12.201] | 1.48 s | AGENT1_WIN |
| random | +12.161 | [+10.637, +13.685] | 1.70 s | AGENT1_WIN |
| reference_agent | +3.076 | [+2.432, +3.721] | 1.66 s | AGENT1_WIN |

Returns are big blinds per duplicate deal, summing both seat-swapped hands.
Judge intervals are ordinary 95% normal intervals, not simultaneous guarantees
or exact bounds for adaptive learning. They do not establish universal winning
play, and the local adversaries are not independent elite engines.

The fresh-process test restarted both servers between duplicate halves against
the frozen b15a release: +0.000 bb/deal, interval
[+0.000, +0.000], CHOP. Both players
had zero faults or skipped calls. See `iteration3/fresh-process/`.

## Restricted runtime and exact organizer build

The supplied smoke test passed with outbound network disabled, read-only files,
user 10001, a writable 512 MB `/tmp`, one CPU, 4 GB RAM, all capabilities
dropped, no-new-privileges and a 256-PID limit. Startup took **2.0 seconds** and
the sample requests **2–3 milliseconds**. See `iteration3/offline-smoke.txt` and
`iteration3/runtime-restrictions.json`.

A separate full match gave the bot its own one-CPU/4-GB read-only container and
a local HTTP port, with CallingStation and the judge on the host. It returned
+10.6095 bb/deal, interval [+9.640, +11.579],
with charged half times **2.106 and 2.105 seconds out of 8**.
Both players had zero errors, forfeits, exhausted banks and skipped calls.
The exact local invocation and judge report are retained as
`iteration3/cpu-check.py` and `iteration3/single-cpu.*`.

Core source, native binary and preflop asset hashes inside the offline container
matched the release files. Runtime inspection also verified the warmed bet
kernel, team identity and absence of imports for the disabled research features.
See `iteration3/runtime-source-sha256.json` and `iteration3/runtime-identity.json`.

Local restricted checks used the cached small sandbox image with current source
mounted read-only and unchanged dependencies. GitHub Actions separately builds
the unchanged full organizer Dockerfiles, checks added image size, and runs the
restricted smoke test. It also runs 110 tests, 12 HTTP matches and a fresh-server
match. Check the pushed commit's
[workflow result](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/actions/workflows/validate.yml);
local sandbox success does not substitute for the exact build.

The shared host has two parent CPU cores. Final HTTP, fresh-process and CPU
checks ran serially with CPU capacity available. A CPU quota is a maximum, not
an exclusive reservation. Earlier oversubscribed failures remain in historical
evidence and are not presented as final timing results.

## Experiments left disabled

Completed development comparisons cover another **345,600 physical hands**
including controls and shared-deal reuse. River search, separate probe/checkraise
contexts, broader contextual priors and selective extra river sampling were
tested. They did not establish a reliable playing-strength improvement. The
release retains the prior betting policy instead of enabling those changes.
Raw losses, draws, prototype descriptions and source information are retained
under `iteration3/experiments/`.

The bounded river search passed referee-transition, terminal-payoff and
information-set tests but produced inconsistent opponent-specific results.
Finer river contexts reduced data available per read. Pooled priors moderated
that uncertainty without establishing a reliable gain.

The extra-sampling numerical benchmark used 24 boards and 32 repetitions each,
comparing 1,280 and 4,096 samples to all **65,780** legal opponent hands.
RMSE fell from 0.01072 to 0.00600 for uniform ranges (44.1%), and from 0.01445
to 0.00773 for a synthetic selective raise range (46.5%). This benchmark expands
every trial; it does not certify the accuracy or win rate of an adaptive
stopping policy. See `iteration3/estimator-accuracy.json` and
`tools/measure_precision.py`.

The enabled precision experiment's 12-opponent pool changed by -0.0218 bb/deal,
interval [-0.0533, +0.0096]. Its 6,000-deal direct comparison with the previous
release changed by -0.1152, interval [-0.2662, +0.0359]. Both include zero and
retain negative point estimates. That experiment remains disabled. Better
numerical estimates of an approximate opponent model do not ensure better
actual decisions. The separate refinement RNG prevents extra draws from
shifting the future baseline stream; the verified trial source is preserved.

## Integrity and remaining limits

The supplied rules, evaluator, referee, protocol tests, original organizer
Dockerfiles/build checker, card engine, native binary and preflop asset are
unchanged from b15a. `agent.py` changes only the team-name default. The source
manifest identifies files outside the evidence directory, and regression/runtime
fingerprints independently identify the tested policy and assets.

See [WEAKNESSES.md](WEAKNESSES.md). The game is not solved, opponent likelihoods
and future betting remain approximate, and independent elite opponents have not
been evaluated. No finite suite establishes that this bot beats every bot.
The team identity defaults to `winner`; an environment override can change it.
