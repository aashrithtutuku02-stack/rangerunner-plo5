# Release validation — iteration 6

Team **winner**, agent **RangeRunner**. The baseline is frozen release
`451b1cb9ae931c5b42a9137e388614606bfaac53`. This update accelerates the existing
strategy and adds independent public-bot validation. **No new win-rate gain is
claimed.** The earlier +0.12054 bb/deal improvement over 52c5 belongs to iteration
5; its complete report is preserved in [iteration 5](validation/iteration5/RELEASE_REPORT.md).

## Exact probability acceleration

The flat model's action probability is independent of hand rank. The likelihood
and raise-value kernels now compute that constant once per model/event instead
of once per sampled hand. Polarized checks skip a fold integral that would have
been discarded. The accumulation order, model parameters, priors, samples,
strategy, native engine and referee are unchanged.

Nine alternating warmed timing repeats, each with 200 calls, measured
**1.10–1.81× faster math kernels** at the normal 768/1,280 sample sizes. These
are kernel measurements, excluding card simulation, startup and HTTP; they are
not a whole-bot speedup. Every timed output was bit-identical to the frozen
release. Tests cover six sample sizes, endpoint ranks, unavailable raises,
all-ins and 90 randomized raise-value cases. See [kernel timings](validation/iteration6/kernel-speed.json).

A preregistered fresh-seed regression played candidate and frozen control in
both seats against **39 local opponents**, 1,000 duplicate deals each. All
**39,000 paired differences were exactly zero**, with original 768/1,280 samples
and no experimental expansion. That is **156,000 physical hands including
controls**, sharing 1,000 card-deal clusters; this is policy preservation,
not additional evidence of a strength gain. [Protocol](validation/iteration6/regression-protocol.json),
[summary](validation/iteration6/regression-summary.json) and all raw records are retained.

## Independent public opponents

Two public challenge bots ran from pinned, separate checkouts with their own
published default strategies. Their evaluator and rules match the supplied
bundle byte for byte. The original HTTP referee enforced the real 8-second
banks and request deadlines; both processes restarted before every half.

Four fresh seeds per bot, each 1,000 duplicate deals, produced **16,000 physical
hands**. Scores are big blinds per duplicate deal, summing both seat-swapped
hands. Pooled intervals below use the 4,000 deal returns per bot; learning
creates dependence, so these are descriptive normal intervals.

| Public bot | Mean bb/deal | Descriptive 95% interval | Wins / draws / losses, four seeds |
|---|---:|---|---|
| fargield | +1.0345 | [+0.7145, +1.3545] | 3 / 1 / 0 |
| starfish | +2.9229 | [+2.5478, +3.2980] | 4 / 0 / 0 |

Both players had zero reported errors, forfeits, exhausted banks and skipped
calls. External active-core, model exception, asset and native-fault checks
passed; budget fallback counts are in the [summary](validation/iteration6/external-summary.json).
Every half retains source hashes checked against its pinned Git commit.
The public repositories' tournament rank and elite strength are unknown; this
does not establish superiority over every bot. Their code is not redistributed.
See [repositories and reproduction](EXTERNAL_BENCHMARKS.md) and
[raw final reports](validation/iteration6/external-final).

## Rejected strategic experiments

Six conditioned re-raise variants, family-based model forgetting, recent-action
frequency learning and low-effective-sample expansion were tested. None
established a reliable broad gain. All remain disabled in production.

The best re-raise discovery candidate was evaluated on four fresh seeds against
20 opponents: **320,000 physical hands including controls**. Its equal-opponent
change was **+0.01507 bb/deal**, with shared-deal interval
**[-0.08948, +0.11961]**. Against frozen 451b itself,
the change was **-0.39975**, interval
**[-0.69398, -0.10552]**. That failure prevented deployment.
The broader variants also had large always-raising regressions in discovery.

All development and fresh-evaluation returns, exact source snapshots and the
pre-evaluation protocol are preserved in [iteration 6](validation/iteration6/README.md).
Numerical correctness of an approximate betting model is not evidence that it
plays better. [RERAISE_MODEL.md](RERAISE_MODEL.md) explains the rejected model.

## Correctness and bounded exhaustive coverage

**281 tests passed** on the final local source; two warnings are third-party
deprecations. New tests cover the exact speed optimization and research-model
accounting, legal re-raise branches, shared information-set decisions, atomic
sample refinement and replay-safe frequency learning. Original supplied tests
and production strategy tests remain unchanged.

The GitHub workflow repeats both exhaustive-history jobs on the pushed source:
eight fixed deals and both buttons, every legal betting history without merging
histories. The established scope is **408,608 terminal histories**, **255,232
decision prefixes**, and a longest line of fourteen actions. Counts and source
identities are checked. This is exhaustive for those fixed deals and supplied
rules, not every card deal, every opponent or every network sequence.
[SCENARIO_COVERAGE.md](SCENARIO_COVERAGE.md) defines the boundary.

## One-CPU runtime and HTTP checks

Four serial longest-line runs used the same one-CPU, 4-GB, read-only, network-
disabled container with current source. Each forces fourteen legal actions on
1,000 deals while evaluating all 14,000 decisions and 2,000 result callbacks.
This is a counterfactual resource test, not a strength benchmark.

| Run | Policy | Seat 0 calculation seconds | Seat 1 calculation seconds | Largest call, seconds |
|---|---|---:|---:|---:|
| 1 | release-451b | 4.355 | 4.355 | 0.0038 |
| 2 | release | 4.356 | 4.357 | 0.0041 |
| 3 | release | 4.356 | 4.355 | 0.0155 |
| 4 | release-451b | 4.358 | 4.357 | 0.0269 |

The mean combined calculation cost was 8.712 seconds before and 8.712
after: essentially unchanged because adaptive sampling targets the internal
calculation budget. Mean retained samples per decision rose from
353.9 to 399.9
(13.0% more) on this
forced workload. Two runs per policy are a small runtime sample, and retaining
more samples does not by itself establish a win-rate gain. The raw reports
include every sample-size count. Every player remained below its 8-second bank
and every call below the 1-second deadline.

A separate isolated one-CPU HTTP match beat CallingStation by
+11.9120 bb/deal. The bot's charged half times were
3.379 and
2.989 seconds of eight. Both
players had zero faults, exhausted banks or skipped decisions. Judge and
opponent ran on the host with no concurrent CPU stress suite.

Six ordinary full HTTP matches also passed fault checks:

| Opponent | bb/deal | Verdict |
|---|---:|---|
| adversary-independent-adaptive-iteration6-http-final | +1.7030 | AGENT1_WIN |
| adversary-range-tight-iteration6-http-final | +0.3400 | CHOP |
| always_half-iteration6-http-final | +13.8075 | AGENT1_WIN |
| always_pot-iteration6-http-final | +8.2725 | AGENT1_WIN |
| calling_station-iteration6-http-final | +12.3130 | AGENT1_WIN |
| random-iteration6-http-final | +11.2155 | AGENT1_WIN |

Restarting both servers between halves against frozen 451b returned
-0.2650 bb/deal (CHOP). Timing-based sample
allocation can change decisions across machines even with identical deals.

Restricted smoke passed with user 10001, one CPU, 4 GB RAM, read-only source,
network disabled, dropped capabilities, no-new-privileges, 256 PIDs and a writable
512-MB `/tmp`. Runtime inspection verified **winner / RangeRunner**, portable C,
lifecycle guards, original five-model weights, no research imports and exact
source/native/asset fingerprints. Local checks use the cached small sandbox
image with current source mounted read-only and unchanged dependencies.

GitHub separately runs the exact organizer build, added-image-size check,
restricted smoke and one-CPU longest-line test, plus 16 full HTTP matchups and a
fresh-process match. Check the workflow on this exact commit for its final
status. Local evidence is under [iteration 6](validation/iteration6/).
The supplied referee, evaluator, original server, requirements, original
Dockerfiles/build checker, native engine and preflop asset are unchanged;
[protected fingerprints](validation/iteration6/protected-files.json) verify this.

The game remains unsolved here. Opponent ranges and future betting are
approximate, and finite equity samples can miss rare cases. See
[WEAKNESSES.md](WEAKNESSES.md). Passing these tests is not an unbeatable-bot
guarantee.
