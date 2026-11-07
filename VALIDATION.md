# Release validation

Measured on 2026-11-07. All confidence intervals are ordinary 95% normal
intervals of the judge's paired duplicate-deal returns. They are not a
multiple-comparison guarantee and do not establish universal superiority.

## Final source tests

**50 automated tests passed.** This includes the unchanged supplied HTTP
protocol tests, every one of the 376,992 five-card rankings against the supplied
evaluator, full/partial Omaha boards, native/Numba sample and RNG equivalence,
a forced fallback subprocess, invalid native inputs, model posterior arithmetic,
compiled/Python likelihood equivalence, the unbeatable-flush case, and all 678
reachable numeric betting states for one fixed legal deal. Two warnings concern
third-party pytest/Starlette deprecations.

## Final evaluation scope

The final policy, compiled likelihood kernel, source and asset identities were
frozen before this suite. The final checks cover **142,000 dealt hands**:
42 direct-call matches across 21 opponent policies on two held-out seeds,
16 direct-call matches across eight selected-search opponents on two new seeds,
11 full HTTP matches, one match with fresh servers between halves, and one
single-CPU container match. Each match is 1,000 duplicate deals / 2,000 hands.

Direct-call suites enforce legal game actions and reset half memory but do not
enforce the HTTP time bank. Runtime claims below come from the real HTTP judge.
The test policies share this project's equity engine; they are not independent
elite poker bots. Development seeds were used for the 32-profile adversary search
and prior selection. The final independent seeds were not used for further strategy selection. Earlier
evaluation failures that led to changes are classified as development evidence.

## Policy-family suite

Each row pools two held-out seeds (2,000 duplicate deals / 4,000 hands).

| Opponent policy | Mean bb/deal | 95% interval | Verdict |
|---|---:|---|---|
| balanced | +3.028 | [+2.466, +3.590] | Win |
| bluffer | +6.235 | [+5.301, +7.169] | Win |
| call | +11.947 | [+11.248, +12.646] | Win |
| checkraise | +2.348 | [+1.823, +2.873] | Win |
| fold | +1.500 | [+1.500, +1.500] | Win |
| half | +13.205 | [+12.324, +14.085] | Win |
| loose | +5.616 | [+4.815, +6.417] | Win |
| maniac | +8.595 | [+7.590, +9.600] | Win |
| nit | +0.795 | [+0.479, +1.112] | Win |
| overfolder | +0.672 | [+0.367, +0.977] | Win |
| polarized | +2.517 | [+1.879, +3.154] | Win |
| pot | +8.045 | [+6.958, +9.132] | Win |
| random | +11.891 | [+10.799, +12.982] | Win |
| range-aware | +1.044 | [+0.518, +1.570] | Win |
| range-flat | +9.376 | [+8.424, +10.328] | Win |
| range-tight | +0.106 | [-0.275, +0.487] | Draw |
| smallball | +3.790 | [+3.262, +4.318] | Win |
| sticky | +6.718 | [+5.980, +7.457] | Win |
| switcher | +3.069 | [+2.319, +3.819] | Win |
| tight | +2.224 | [+1.788, +2.661] | Win |
| trapper | +2.092 | [+1.608, +2.577] | Win |

Pooled family verdicts: 20 wins, 1 draws,
0 losses. Raw files are in `validation/final-policy-suite/`.

## Selected parameter-search challengers

Eight harder cases were selected from 32 discovery profiles before final tests.
Each row pools two independent final seeds (2,000 duplicate deals).

| Case | Mean bb/deal | 95% interval | Verdict |
|---|---:|---|---|
| search000 | -0.293 | [-0.910, +0.323] | Draw |
| search005 | +0.523 | [+0.152, +0.894] | Win |
| search013 | +2.102 | [+1.683, +2.521] | Win |
| search014 | +1.054 | [+0.641, +1.467] | Win |
| search021 | +0.574 | [+0.264, +0.883] | Win |
| search022 | +1.739 | [+1.363, +2.115] | Win |
| search024 | -0.165 | [-0.793, +0.464] | Draw |
| search030 | +1.131 | [+0.783, +1.479] | Win |

Raw cases and their preselected parameters are in `adversary_cases.json` and
`validation/final-selected-cases/`. Draws and negative point estimates are
retained rather than reported as wins.

## Real HTTP judge

The final HTTP matches used separate servers and the unchanged referee, with
its 8-second bank, 1-second request deadline and 5-error forfeit rule.
Every bot in all 11 matches had **zero errors, forfeits, exhausted banks and
skipped calls**. Advanced draws are allowed and shown explicitly.

| Opponent | Mean bb/deal | 95% interval | Max charged time/half | Verdict |
|---|---:|---|---:|---|
| EquityValueReference | +1.887 | [+1.218, +2.556] | 1.98 s | AGENT1_WIN |
| Adversary-bluffer | +5.295 | [+3.928, +6.661] | 2.01 s | AGENT1_WIN |
| Adversary-nit | +1.007 | [+0.479, +1.535] | 3.13 s | AGENT1_WIN |
| Adversary-switcher | +2.795 | [+1.678, +3.912] | 2.02 s | AGENT1_WIN |
| Adversary-checkraise | +1.790 | [+1.025, +2.555] | 1.74 s | AGENT1_WIN |
| CallingStation | +11.637 | [+10.644, +12.630] | 7.79 s | AGENT1_WIN |
| Adversary-range-tight | +0.511 | [-0.053, +1.075] | 2.53 s | CHOP |
| RandomBot | +11.666 | [+10.085, +13.247] | 6.50 s | AGENT1_WIN |
| Adversary-search000 | +0.390 | [-0.438, +1.217] | 1.41 s | CHOP |
| AlwaysPot | +6.834 | [+5.253, +8.415] | 1.50 s | AGENT1_WIN |
| AlwaysHalf | +12.521 | [+11.252, +13.790] | 1.55 s | AGENT1_WIN |

Raw reports: `validation/final-http/`.

The fresh-process test restarted both servers between half 1 and half 2 and
combined their reports with the official judge: CHOP,
-0.032 bb/deal. Both players again had zero faults and
no skipped decisions. See `validation/fresh-process/`.

## Restricted runtime and the repaired time-bank failure

The final code passed the supplied smoke test with network disabled, read-only
files, user 10001, a 512 MB writable /tmp, 1 CPU, 4 GB RAM, all capabilities
dropped, no-new-privileges, and a 256 PID limit. The health check answered after
about 2.3 seconds, within the 15-second startup deadline. Sample decisions took
2–4 milliseconds, within the 1-second deadline.

A separate full match gave the bot its own 1-CPU/4-GB, read-only container while
the judge and CallingStation ran on the host. Only the local HTTP port was
published; the separate no-network smoke test checks offline operation.
The final bot won +11.995 bb/deal,
interval [+11.029, +12.962], with charged half times
2.49 and
2.30 seconds out of 8, and zero
errors, forfeits, exhausted banks or skipped calls. Runtime image core sources,
native binary and equity asset were verified to match this release by SHA-256.

The earlier development build exhausted both half banks and skipped 207 and
427 decisions. Those failed reports are preserved as
`validation/development-time-bank-failure.*`. The final compiled likelihood loop
and more conservative internal budget address the computation cost. Additional
parallel runs over-subscribed the two-core development parent and exhausted
banks; those reports are preserved in `validation/development/`. The reported
release CPU and fresh-process checks were run serially with available CPU
capacity. A container CPU quota is a maximum, not an exclusive reservation.

The local VFS Docker storage could not build every organizer image layer within
this workspace's disk limit. Local restricted tests use `docker/Dockerfile.sandbox`,
with the exact bot dependencies. The committed GitHub Actions workflow runs the
unchanged full organizer Dockerfiles, added-image-size check and restricted smoke
test on an Ubuntu Docker runner. The workflow result must be checked for the
actual pushed commit; local sandbox success is not a substitute for that result.

A selected check-raising policy also beat the earlier release candidate on one
seed by -1.152 bb/deal, interval [-2.074, -0.229]. That result, its source snapshot,
and final independent-seed draws after separating initial-bet and re-raise
statistics are retained. This was a measured weakness, not evidence of universal
winning play.

## Remaining limits and original files

See [WEAKNESSES.md](WEAKNESSES.md). The hardest similar range-aware strategy and
some selected challengers draw statistically; this is not an unbeatable bot.
No elite independent engine or solved-game exploitability bound was used.

The original rules, evaluator, referee, supplied tests, organizer Dockerfiles,
and server plumbing were verified unchanged. Strategy modules, native kernel,
preflop asset, local adversaries, tests and CI are added. Set the registered team
identity in `agent.py` before submitting.
