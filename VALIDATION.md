# Release validation — iteration 5

Measured November 7, 2026, America/Chicago; raw timestamps and seed labels may use November 8 UTC. The team name is **winner**. Historical reports remain available in earlier commits and `validation/iteration2/`, `iteration3/` and `iteration4/`.

## Measured improvement and its limits

The selected polarized/gated model improved the equal-opponent mean by **+0.12054 bb per duplicate deal** against frozen release `52c5a1733a59e95246584b6b7e84ec2b72abeff8`. Its descriptive shared-deal normal 95% interval was **[+0.025, +0.216]**. All four fresh seed means were positive; the separate four-seed t interval was **[+0.043, +0.198]**.

This is a finite local benchmark result, not a solved-game or universal superiority claim. The direct match against 52c5 remained a draw; several paired point estimates declined. No externally developed elite bot was tested. The three independently written challengers share the project card engine and referee types.

## What changed

The old value-focused models made raises increasingly likely as strength rose. Two additional calibrated models allow both strong value bets and weak bluffs, while keeping each model's fold curve decreasing with strength. A public postflop aggression estimate gates their effective share: low betting frequency returns mass to the three original value models. Their original conditional prior ratios are preserved. See [POLARIZATION.md](POLARIZATION.md) for the closed-form calibration, gate and assumptions.

The first unconditional polarized candidate gained against bluffers but regressed against tight, check-raising and adaptive challengers. Within-hand mixture conditioning and prior-centered regularization were also tested; their mixed results did not justify enabling them. Six candidate variants and their development losses are retained in [iteration5 evidence](validation/iteration5/README.md). Only the selected gated policy is active in `agent.py`.

The supplied referee, evaluator, server plumbing, requirements, original Dockerfiles and build checker, native engine and preflop asset remain unchanged from 52c5. The release and experimental comparison strategies have frozen helpers so production changes cannot silently alter the baseline.

## Fresh-deal comparison

The final cohort uses four new 1,000-deal seeds (`iteration5-final-holdout-20261108-e/f/g/h`) against sixteen opponents. Each candidate and control plays both seats on the same deals: **256,000 physically played hands**, including controls. The 64,000 paired policy observations share **4,000 deal clusters**. The pooled interval clusters opponents sharing a deal before estimating uncertainty. A separate seed-level interval uses four seed means and Student t with three degrees of freedom. These remain descriptive intervals because learning couples successive hands; they are not simultaneous guarantees.

Offline comparisons use an 80-second accounting bank to keep default 768/1,280 samples fixed, independently of host scheduling. Real 8-second behavior is checked separately below. Identical frozen-policy controls returned exactly zero on every duplicate deal.

| Opponent | Current bb/deal | Change from 52c5 | Paired-change 95% interval |
|---|---:|---:|---|
| balanced | +3.152 | +0.130 | [-0.255, +0.514] |
| bluffer | +7.108 | +0.715 | [+0.014, +1.416] |
| call | +11.571 | +0.001 | [-0.007, +0.009] |
| checkraise | +2.337 | +0.077 | [-0.194, +0.349] |
| independent-adaptive | +1.453 | -0.071 | [-0.325, +0.183] |
| independent-polar | +3.838 | -0.293 | [-0.981, +0.396] |
| independent-value | +1.799 | -0.067 | [-0.318, +0.185] |
| nit | +1.329 | -0.010 | [-0.137, +0.117] |
| opportunist | +2.414 | -0.075 | [-0.491, +0.341] |
| polarized | +3.455 | +0.335 | [-0.077, +0.746] |
| pot | +8.895 | +0.340 | [-0.019, +0.699] |
| range-tight | +0.270 | +0.189 | [-0.159, +0.537] |
| release-52c5 | -0.125 | -0.125 | [-0.371, +0.121] |
| search000 | +0.106 | -0.102 | [-0.349, +0.146] |
| search024 | +1.419 | +0.197 | [-0.052, +0.446] |
| switcher | +3.870 | +0.687 | [+0.230, +1.143] |

The current-policy score intervals give **13 descriptive wins, 3 draws and 0 losses** over this cohort. The draws are 52c5, range-tight and search000. These labels describe the local sample, not guaranteed match outcomes. The largest negative paired point estimate was against independent-polar; its interval includes both loss and gain.

| Fresh seed suffix | Equal-opponent change, bb/deal |
|---|---:|
| e | +0.12581 |
| f | +0.16200 |
| g | +0.05103 |
| h | +0.14331 |

Raw returns, sample counts, fingerprints and pooled/seed summaries are under `validation/iteration5/final-holdout*`. Earlier evaluation seeds were not reused for this final cohort. Reported returns are big blinds per duplicate deal, summing two seat-swapped hands.

## Correctness and complete betting-history scope

**243 tests passed.** The added tests independently integrate 100,000 ranks for action-frequency calibration, check extreme frequencies and endpoint ranks, compare compiled/Python probabilities and joint bet values, preserve positive-model equivalence, verify gating limits and probability mass, and check the promoted policy against its frozen research candidate. Existing scoring, visibility, replay/rollback, budget, half-reset and HTTP negative tests remain in place. The original supplied tests are unchanged. Two local warnings concern third-party deprecations.

GitHub passed both full-history jobs on the exact implementation commit `9a8695dc4de668ae260b050b26a436281527644e`: [run 42448304410](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/actions/runs/42448304410). Each job checks eight fixed deals for one button position and validates complete counts and source identities.

Across eight fixed deals and both buttons, every legal betting history was followed without merging histories: **408,608 terminal histories**, **255,232 decision prefixes**, **255,232 repeated decisions**, **817,216 terminal-inference checks**, **817,216 duplicate-result checks**, and **1,072,448 learning-state comparisons**. Each case/button has 678 numeric states and a longest line of fourteen actions. Default 768/1,280-sample calculation is used. This is counterfactual correctness coverage, not independent games or a win rate.

The exact boundary and reproducible commands are in [SCENARIO_COVERAGE.md](SCENARIO_COVERAGE.md). It is exhaustive for the selected fixed deals and supplied rules, not for all card deals, all packets or all possible opponents. GitHub status and per-step conclusions are retained in `iteration5/gated-ci.json`; full sweep artifacts remain on the run. Automated artifact/log retrieval in this environment returned HTTP 403, so no missing raw artifact is represented as locally downloaded evidence.

## Real HTTP judge and restricted runtime

Fifteen local HTTP matches, one fresh-process match and one one-CPU HTTP match add **34,000 physical hands** to the final performance cohort (**290,000 including the offline controls**). They use the unchanged judge, real 8-second half banks, 1-second request deadlines and 5-error forfeit limit. **Both players in every match had zero errors, forfeits, exhausted banks and skipped calls.** All four supplied baselines were beaten.

| HTTP opponent | bb/deal | 95% interval | Max charged time/half | Verdict |
|---|---:|---|---:|---|
| adversary-bluffer | +6.438 | [+5.270, +7.605] | 1.47 s | AGENT1_WIN |
| adversary-checkraise | +2.196 | [+1.457, +2.934] | 1.55 s | AGENT1_WIN |
| adversary-independent-adaptive | +1.501 | [+0.968, +2.034] | 2.16 s | AGENT1_WIN |
| adversary-independent-polar | +3.413 | [+2.311, +4.514] | 1.96 s | AGENT1_WIN |
| adversary-independent-value | +1.662 | [+1.153, +2.171] | 1.91 s | AGENT1_WIN |
| adversary-nit | +1.321 | [+0.879, +1.763] | 2.05 s | AGENT1_WIN |
| adversary-opportunist | +2.166 | [+1.293, +3.038] | 1.66 s | AGENT1_WIN |
| adversary-range-tight | +0.189 | [-0.375, +0.753] | 1.68 s | CHOP |
| adversary-release-52c5 | +0.247 | [-0.236, +0.730] | 1.80 s | CHOP |
| adversary-switcher | +4.246 | [+3.251, +5.241] | 1.71 s | AGENT1_WIN |
| always_half | +13.777 | [+12.615, +14.940] | 1.22 s | AGENT1_WIN |
| always_pot | +8.046 | [+6.467, +9.626] | 1.51 s | AGENT1_WIN |
| calling_station | +11.652 | [+10.658, +12.646] | 2.14 s | AGENT1_WIN |
| random | +10.597 | [+8.995, +12.198] | 1.70 s | AGENT1_WIN |
| reference_agent | +3.378 | [+2.704, +4.053] | 1.91 s | AGENT1_WIN |

Restarting both servers between halves against 52c5 returned +0.456 bb/deal, interval [-0.082, +0.994], CHOP. See `iteration5/http/` and `fresh-process/`.

The isolated one-CPU/4-GB read-only container beat CallingStation by +11.3555 bb/deal, interval [+10.379, +12.332]. Its charged half times were **3.283 and 3.419 seconds of 8**. The judge and opponent ran on the host; no other CPU stress suite ran concurrently. The exact runner and reports are retained in `iteration5/cpu-check.py` and `single-cpu.*`.

The network-disabled one-CPU longest-line test forced fourteen legal actions on each of 1,000 random deals while evaluating both players. All **14,000 decisions and 2,000 result calculations** succeeded. Per-player calculation totals were **4.358 and 4.356 seconds**, with largest call **0.0101 seconds**. This excludes HTTP and overrides selected actions to reach the long line; it is a resource test, not playing-strength evidence. See `iteration5/worst-line-load.json`.

The supplied smoke test passed with network disabled, read-only source, user 10001, one CPU, 4 GB RAM, writable 512 MB `/tmp`, dropped capabilities, no-new-privileges and 256 PIDs. Startup was about 2.5 seconds. Some supplied synthetic frames have out-of-order hand IDs and exercise stale-frame fallbacks; full-policy evidence comes from legal history sweeps, normal matches and the longest-line load.

Container inspection verified `winner / RangeRunner`, the portable C backend, lifecycle guards, the five-model nominal and effective initial weights, no research imports, and exact source/native/asset fingerprints. Local restricted checks use the cached small sandbox image with current source mounted read-only and unchanged dependencies. GitHub separately passed the exact organizer build, size cap, restricted smoke and longest-line checks. See `iteration5/runtime-identity.json`, `protected-files.json` and `gated-ci.json`.

## Remaining limits

The game is unsolved here. Opponent likelihoods, bluff/value tails, future betting and equity samples remain approximations. The final cohort supports a modest average gain for the tested opponent pool, not a demonstrated win against every matchup or the strongest bots in the world. See [WEAKNESSES.md](WEAKNESSES.md) for the remaining strategic and runtime boundaries.
