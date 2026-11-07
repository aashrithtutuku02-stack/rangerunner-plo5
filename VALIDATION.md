# Release validation — iteration 2

Measured on 2026-11-07 against frozen release
[`36ba2d9`](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/commit/36ba2d9719d0cad40d67d900c887d4f03727f2ae).
The previous release's [validation report](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/blob/36ba2d9719d0cad40d67d900c887d4f03727f2ae/VALIDATION.md)
and raw evidence remain available. Older `validation/` folders describe that
release; the current evidence is under `validation/iteration2/`.

## Changes and selection

The action model now calibrates fold/call/raise frequencies under a uniform
strength-rank assumption. Terminal learning includes verified final responses
and preflop all-in showdowns. History reconstruction tracks whether raising was
legal, and compulsory calls/checks no longer teach a false preference against
raising. Proposed raises cannot be penalized for an illegal fifth raise or an
all-in opponent's impossible re-raise.

Development compared terminal-evidence changes, calibration, full per-hand
Bayesian model updates, and recency decay. More aggressive Bayesian updating and
decay produced mixed opponent-specific results and were left out of production.
The posterior experiment records and their losses are retained under
`iteration2/development-posterior/`; they used development deals and a prior
research snapshot, not the final production policy. `research_candidates.py`
contains those exploratory variants; `--candidate release` selects production.

Production changes were frozen before the final comparisons below. The
incumbent strategy and likelihood helper are frozen separately under
`opponents/`, with only the helper import redirected. Both use the same unchanged
card engine and equity asset. An automated mirror control and every final
incumbent self-match returned exactly zero on paired duplicate deals.

## Tests and evaluation scope

**88 automated tests passed**, including the unchanged supplied protocol tests,
all 376,992 five-card rankings against the supplied evaluator, native/fallback
sampling equivalence and invalid-input guards, 678 reachable numeric betting
states for one fixed legal deal, normalization and numerical calibration checks,
terminal-learning consistency, reconstruction of legal raise opportunities,
censored learning, frozen self-play, report checking, and shared-deal analysis.
Two warnings concern third-party pytest/Starlette deprecations.

The final cohort contains **164,000 physically played hands**, including control
matches: 40,000 in the incumbent comparison, 96,000 in the opponent pool, 24,000
through the actual HTTP judge, 2,000 with fresh processes, and 2,000 in the
one-CPU container. This count includes reused duplicate/common deals and does
not mean 164,000 independent observations.

Returns are big blinds per duplicate deal, summing both seat-swapped hands.
Intervals use normal 95% standard-error estimates of paired returns. The pool
first averages opponents sharing the same seed/deal, so it does not count those
repeated deals as independent. These are descriptive finite-suite estimates,
not simultaneous guarantees, exact bounds for adaptive learning, or evidence of
universal superiority. No independent elite engine or solved-game exploitability
bound was used.

## Held-out comparison with the incumbent

Ten fresh seeds, each with 1,000 duplicate deals, gave **+0.175 bb/deal** against
the frozen previous release, 95% interval **[-0.008, +0.357]**. This is
statistically close; a direct head-to-head win has not been established.

Raw per-deal candidate and control returns, source identities and summaries:
`iteration2/head-to-head/`. The controls are exactly zero.

Offline comparisons use an 80-second internal accounting budget to keep default
simulation counts fixed. The real tournament bank remains 8 seconds; runtime
claims come from the separate HTTP tests. An early timing-dependent comparison
failed its mirror control because host scheduling changed sample allocation;
that experiment was discarded. Fixed sampling and the zero mirror assertion
were added before this final suite.

## Held-out opponent-pool comparison

Twelve opponent policies on two new 1,000-deal seeds gave an equally weighted
average improvement of **+0.565 bb/deal**, interval **[+0.339, +0.792]**, over
the incumbent playing the same opponents and cards. There are 2,000 shared-deal
clusters and 24,000 paired policy observations. The pool includes tight betting,
check-raising, polarized play, changing styles, two selected search challengers,
baselines, and a policy that attacks checked pots.

| Opponent | New score | Change from incumbent | 95% interval of change |
|---|---:|---:|---|
| nit | +1.494 | +0.305 | [+0.041, +0.570] |
| balanced | +3.155 | +0.104 | [-0.506, +0.714] |
| checkraise | +2.774 | +0.736 | [+0.205, +1.266] |
| polarized | +3.436 | +1.342 | [+0.587, +2.097] |
| switcher | +3.874 | +0.854 | [+0.077, +1.631] |
| search000 | +0.715 | +0.903 | [+0.363, +1.442] |
| search024 | +1.286 | +1.226 | [+0.649, +1.802] |
| pot | +8.165 | +0.340 | [-0.326, +1.005] |
| call | +11.616 | +0.010 | [-0.054, +0.074] |
| random | +11.402 | +0.621 | [-0.862, +2.103] |
| opportunist | +2.322 | -0.425 | [-1.069, +0.218] |
| oscillating | +3.306 | +0.770 | [-0.065, +1.605] |

The opportunist has a negative change point estimate; its interval includes zero.
This tradeoff is retained. High positive scores against simple baselines are
not evidence of strength against elite bots. Test policies share project code
and the equity engine. See `iteration2/opponent-pool/` for paired raw returns,
source fingerprints and the clustered analysis.

Reproduce analysis without replaying matches:

```sh
python tools/summarize_comparison.py validation/iteration2/head-to-head
python tools/summarize_comparison.py validation/iteration2/opponent-pool
```

For a new independent comparison, choose new seeds:

```sh
python evaluate_candidate.py --candidate release --opponents incumbent nit search024 --seeds new-a new-b --output comparison-results
python tools/summarize_comparison.py comparison-results
```

## Actual HTTP judge and lifecycle

All 12 full HTTP matches used the unchanged referee and separate servers with
the real 8-second bank, 1-second request deadline, and 5-error forfeit rule.
**Both players in every match had zero errors, forfeits, exhausted banks and
skipped calls.** All four supplied baselines were beaten; advanced draws remain
visible. Raw reports are in `iteration2/http/`.

| Opponent | Mean bb/deal | 95% interval | Max charged time/half | Verdict |
|---|---:|---|---:|---|
| adversary-bluffer | +5.978 | [+4.686, +7.269] | 1.90 s | AGENT1_WIN |
| adversary-checkraise | +2.588 | [+1.833, +3.343] | 1.85 s | AGENT1_WIN |
| adversary-incumbent | +0.605 | [+0.053, +1.157] | 2.29 s | AGENT1_WIN |
| adversary-nit | +1.392 | [+0.972, +1.812] | 2.03 s | AGENT1_WIN |
| adversary-opportunist | +2.140 | [+1.288, +2.992] | 1.96 s | AGENT1_WIN |
| adversary-oscillating | +3.076 | [+2.078, +4.074] | 1.98 s | AGENT1_WIN |
| adversary-range-tight | +0.199 | [-0.375, +0.773] | 1.96 s | CHOP |
| always_half | +15.008 | [+13.816, +16.200] | 1.49 s | AGENT1_WIN |
| always_pot | +8.523 | [+6.987, +10.059] | 1.75 s | AGENT1_WIN |
| calling_station | +12.123 | [+11.133, +13.114] | 1.75 s | AGENT1_WIN |
| random | +11.068 | [+9.531, +12.605] | 1.83 s | AGENT1_WIN |
| reference_agent | +3.062 | [+2.403, +3.722] | 2.12 s | AGENT1_WIN |

The fresh-process test restarted both servers between duplicate halves, against
the frozen incumbent. It returned +0.205 bb/deal, interval [-0.357, +0.767],
a draw, with zero faults or skipped calls. See `iteration2/fresh-process/`.

## Restricted runtime and organizer build

The supplied smoke test passed with outbound network disabled, read-only files,
user 10001, writable 512 MB `/tmp`, one CPU, 4 GB RAM, dropped capabilities,
no-new-privileges and a 256-PID limit. Startup took 2.0 seconds and the sampled
requests 2–3 milliseconds. See `iteration2/offline-smoke.txt`.

A separate full real-judge match gave the bot its own one-CPU/4-GB read-only
container and a local HTTP port, with the judge and CallingStation on the host.
It returned +11.296 bb/deal, interval [+10.320, +12.272], and charged **3.23 and
3.30 seconds of each 8-second bank**, with zero faults or skipped calls for
either player. Core runtime source, native binary and preflop asset hashes
matched this source tree (`iteration2/runtime-source-sha256.json`). Local
restricted runs used the small sandbox image with current source mounted
read-only; they do not replace the exact organizer image build.

The shared host has only two parent CPU cores. Earlier oversubscribed timing
runs exhausted banks; final runtime checks ran with CPU capacity available.
A CPU quota sets a maximum and does not reserve a CPU. The original development
bank failure and other earlier losses remain under `validation/development*`.

GitHub Actions runs the unchanged organizer Dockerfiles, added-image-size check
and restricted smoke test on the pushed commit. It also runs the 88 tests,
11 full HTTP matches, and a fresh-server match, checking faults in both players.
Check the current commit's [workflow result](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/actions/workflows/validate.yml)
for build status; historical success alone does not validate a new commit.

## Integrity and limits

The supplied rules, evaluator, referee, protocol tests, original organizer
Dockerfiles/build checker and `agent.py` server are unchanged. The native engine
and preflop asset are also unchanged from the incumbent. The verified list is in
`iteration2/protected-files.json`; `SOURCE_SHA256.json` identifies release files
outside the evidence directory.

The rank calibration is a model assumption, especially imperfect for early
streets and tied strengths. Betting remains approximate and the game is not
solved. See [WEAKNESSES.md](WEAKNESSES.md) for remaining strategic and runtime
limits. Set the registered team identity in `agent.py` before submission.
