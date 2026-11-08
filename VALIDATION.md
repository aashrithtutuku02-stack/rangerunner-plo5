# Release validation — iteration 7

Team **winner**, agent **RangeRunner**. The baseline is frozen release
`9efa86c1b7a6557be6b4cb508cced6d57a38432b`.

## Measured strategic improvement

The new caller read improved the equal-opponent average by **+0.18735
big blinds per duplicate deal** across 24 local opponents and four fresh seeds.
The descriptive shared-deal 95% interval is **[+0.16038, +0.21432]**;
the separate four-seed t interval is **[+0.12697, +0.24773]**.
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
| a | +0.21054 |
| b | +0.19065 |
| c | +0.21546 |
| d | +0.13275 |

| Calling style | Candidate bb/deal | Change from 9efa | Paired-change 95% interval |
|---|---:|---:|---|
| call | +13.161 | +1.601 | [+1.378, +1.825] |
| passive-value | +10.157 | +1.710 | [+1.450, +1.971] |
| passive-trap | +6.661 | +0.246 | [+0.046, +0.446] |
| caller-switcher | +9.788 | +0.817 | [+0.514, +1.120] |
| caller-oscillating | +8.953 | +0.121 | [-0.091, +0.333] |

**19 opponent matchups had exactly unchanged paired returns** across
all four seeds. Frozen-release head-to-head change was +0.00000
with interval [+0.00000, +0.00000]. All per-opponent scores,
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
| Frozen 9efa | +11.874 | 3.174 | 2.714 |
| Caller read | +13.259 | 2.714 | 3.581 |

The one-seed paired change was +1.385 bb/deal, interval
[+0.882, +1.888]. This is a small real-budget check; scheduling
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
totals were 4.356 and
4.356 seconds; the largest call was
0.0105 seconds. The response window remained bounded.
This excludes HTTP and overrides chosen actions, so it is a resource test rather
than playing-strength evidence.

Eight ordinary full HTTP matches passed fault checks, including all four
supplied baselines, which were beaten:

| Opponent | bb/deal | Verdict |
|---|---:|---|
| adversary-caller-switcher | +9.826 | AGENT1_WIN |
| adversary-independent-adaptive | +1.818 | AGENT1_WIN |
| adversary-passive-trap | +7.050 | AGENT1_WIN |
| adversary-range-tight | +0.440 | CHOP |
| always_half | +13.405 | AGENT1_WIN |
| always_pot | +7.971 | AGENT1_WIN |
| calling_station | +12.745 | AGENT1_WIN |
| random | +13.102 | AGENT1_WIN |

Restarting both servers before each half against 9efa returned
-0.143 bb/deal (CHOP). Restricted smoke also
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
| fargield | +1.073 | [+0.612, +1.534] | 1 / 1 / 0 |
| starfish | +2.992 | [+2.454, +3.530] | 2 / 0 / 0 |

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
