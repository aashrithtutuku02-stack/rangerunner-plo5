# RangeRunner — Short Deck PLO5

Based on the [TAMU Datathon starter bundle](https://github.com/tamu-datathon-org/heads-up-bundle).

An adaptive poker bot for the TAMU Datathon heads-up, 36-card, five-card
Pot-Limit Omaha challenge. It implements the challenge's exact two-hole plus
three-board rule and short-deck hand rankings. It uses native card simulation,
precomputed starting-hand equity, Bayesian opponent ranges, and chip-value
comparisons for the available actions.

This is a tested approximate strategy. It is not a solved poker strategy and
there is no guarantee it beats every opponent. The validation includes close
matches, failed development variants, and a repaired time-bank failure.
See [VALIDATION.md](VALIDATION.md) and [WEAKNESSES.md](WEAKNESSES.md).
The exhaustive betting-history scope is defined in [SCENARIO_COVERAGE.md](SCENARIO_COVERAGE.md).

The latest strategy learns when an opponent consistently calls bets, then
allows thinner value bets after enough voluntary responses support that read.
Free checks and forced calls cannot establish it, and recent folds and raises
can invalidate it. The existing bluff guard remains in place. Fresh comparisons
against the previous release and independent public-bot results are in
[VALIDATION.md](VALIDATION.md); [CALLING_READ.md](CALLING_READ.md) explains the rule.

## Run

Use Python 3.12, matching the tournament.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
python agent.py
```

On Windows, activate with `.venv\Scripts\activate`.

**The registered team name defaults to `winner`.** `PORT`, `AGENT_TOKEN`, and
the original server protocol are preserved. The environment variable
`PARTICIPANT` can override the identity; check it if deploying with custom settings.

## Play and test

The new opt-in bluff bot can be started with `python bluff_agent.py`. It mixes
price-aware opening bluffs with checks and learns from observed folds. Fresh
tests did **not** establish a reliable gain, so `agent.py` retains the proven
tournament strategy. See [BLUFF_EXPERIMENTS.md](BLUFF_EXPERIMENTS.md) for modes,
results and limitations before choosing the experimental entrypoint.

In separate terminals:

```sh
python baseline-bots/baseline_random.py
python judge_engine.py --deals 1000 --seed 17
```

Start and stop opponents automatically, using the actual HTTP judge:

```sh
python benchmark.py --seeds 17 29
python benchmark.py --opponents adversary:nit adversary:range-tight adversary:bluffer adversary:switcher
python tools/check_results.py benchmark-results
```

Opponents start sequentially to keep startup compilation from competing across
many processes. The judge enforces its real time bank. The report checker rejects
errors, forfeits, exhausted banks, skipped decisions, and baseline losses/draws.
Advanced opponents may draw; their confidence intervals remain in the reports.

For accelerated discovery on duplicate deals (direct calls, without HTTP time-bank
enforcement), including 36 named local policies and eight selected search opponents:

```sh
python stress_benchmark.py --deals 1000 --seeds discovery-example
python stress_benchmark.py --deals 1000 --cases adversary_cases.json
```

Use fresh servers between halves to check tournament lifecycle behavior:

```sh
python tools/fresh_match.py --opponent adversary:range-tight
```

Deals repeat with the same seed. Timing-based sample allocation can change
individual decisions across machines, so identical cards do not guarantee
identical numeric reports. Confidence intervals are in **bb per duplicate deal**,
summing both seat-swapped hands, as defined by the supplied judge.

## Compare with the previous release

Earlier released strategies and their helpers are frozen under `opponents/`.
They cannot silently inherit the new action model. A negative-control self-play
test verifies zero paired returns for identical frozen policies.

```sh
python evaluate_candidate.py --candidate release --baseline release-9efa --opponents release-9efa independent-adaptive nit call passive-value caller-switcher --seeds my-new-seed-a my-new-seed-b --output comparison-results
python tools/summarize_comparison.py comparison-results
```

`release-9efa` is the caller-read comparison baseline. `release-3aa` freezes the
validated tournament strategy used to evaluate the new bluff experiments.
The caller read targets
frequent-caller matchups; it is not a claim of improving every opponent matchup.
`release-451b`, `release-52c5`, `release-f452`,
`release-b15a` and `incumbent` select earlier releases for historical comparisons.

These offline comparisons use a generous internal bank to prevent host
scheduling from reducing the policy's requested sample counts. They do not
certify tournament timing; the separate HTTP and container checks use the real
8-second bank. Common-deal comparisons use paired returns. The opponent-pool
summary groups shared deals across opponents before calculating uncertainty.

## Implementation

* `preflop.npz` represents all 376,992 starting hands as 19,998 suit-equivalent
  classes. Each was simulated against 8,192 random opponents and boards. The
  compressed asset is about 80 KB. These are estimated equities, not exact values.
* `native/plo5_fast.c` and its included Linux x86-64 shared library implement the
  scoring and sampling loops. They use baseline CPU instructions and the C ABI.
  No compiler, GPU, downloads, or network access is required during play.
* `fast_engine.py` validates card arrays before passing pointers to native code.
  Other platforms, or `RANGERUNNER_ENGINE=numba`, use the tested Numba fallback
  in `equity_engine.py`.
* `strategy.py` learns opportunity-adjusted frequencies per street for checks,
  initial bets, and re-raises. Calls when raising is unavailable reveal only
  a decision to continue, so they preserve the learned call/raise preference.
  Model likelihoods merge unavailable raises into calls and raise evaluation
  assigns zero probability to an illegal re-raise.
* `bet_ev.py` compiles the joint model/hand expectation for both raise sizes.
  It preserves the previous value formula while avoiding repeated response
  arrays and Python dispatch. It evaluates identical clipped all-in sizes once.
  Kernel equivalence is checked numerically and through common-deal regression.
* `range_model.py` mixes three value-focused models with two polarized models
  that allow strong value bets and weak bluffs. Every model retains decreasing
  fold probability with strength and calibrated uniform-rank action frequencies.
  Closed-form intercepts and a conditional continuing-rank transform avoid
  numerical calibration during play. See [POLARIZATION.md](POLARIZATION.md)
  for the assumptions and derivation.
* Hand learning includes verified final opponent calls, folds and checks,
  including preflop all-in showdowns. Chip totals and street consistency are
  checked so stale callbacks do not invent a missing action.
* The repeated likelihood loops compile at startup. This
  keeps the model calculations out of slow repeated Python/NumPy dispatch.
  The flat model now calculates each constant action probability once, and
  polarized checks skip a fold integral whose result would be discarded.
  Floating-point accumulation order is preserved; equivalence tests require
  bit-identical results against the frozen release.
* Live samples are reused within a street and decrease if measured decision
  and result-processing time gets ahead of the half's internal budget.
* All learned state, random state, and sample caches live in `memory` and reset
  every half. Global assets and compiled functions contain no learned match state.
* Completed results are idempotent. Stale or conflicting history prefixes do not
  rewind learning or replace a current hand. Failed calculations restore the
  prior learning and RNG state while accounting for the time spent.
* `calling_read.py` retains a rolling window of voluntary responses. A minimum
  sample and a conservative call-frequency bound gate thin value betting.
  Its immutable per-half state participates in replay and rollback checks.
* Cache keys normalize hole-card order and the order of the three flop cards;
  the arrival order of turn and river remains significant.

Optional native rebuild:

```sh
bash tools/build_native.sh
```

To recreate the preflop asset outside tournament play:

```sh
python train_preflop.py --samples 8192
```

`reference_range.py` is the frozen original range strategy used by the local
range-aware challengers. `independent_opponents.py` supplies value-focused,
polarized and fold-adaptive challengers with separately written decision logic.
All share project card primitives; none is an externally developed elite poker
engine. The prior search and parameter-search tools use discovery deals;
final evaluation deals are separate.

`river_search.py`, `betting_context.py`, `river_precision.py` and their research
adapters are **experimental testing tools**. River search, finer context reads,
and extra sampling passed their numerical checks but did not establish a
playing-strength improvement. Production uses the polarized/value likelihood
family while retaining the previous action-value formula. Experiment results
are preserved.

Conditioned re-raise values, family-based forgetting, recent-frequency learning
and low-effective-sample expansion also remain experimental. Their numerical
tests passed, but match results did not justify deployment. See
[RERAISE_MODEL.md](RERAISE_MODEL.md) and the iteration 6 evidence. The external
benchmark harness runs pinned public bots from separate checkouts; their source
is not included. See [EXTERNAL_BENCHMARKS.md](EXTERNAL_BENCHMARKS.md).
Unconditional raise-margin removal and separate pre/postflop range models were
also tested and remain disabled; the production caller rule has a narrower scope.

Reproduce the numerical benchmarks:

```sh
python tools/measure_bet_ev.py --output bet-timing.json
python tools/measure_precision.py --output precision-accuracy.json
python tools/measure_probability_speed.py --output probability-timing.json
```

## Docker and continuous integration

The original organizer Dockerfiles and build checker are retained:

```sh
bash tools/check_build.sh
```

This checks the exact organizer base, added image size, and restricted startup
and decisions. The supplied workflow runs it on GitHub's Ubuntu Docker runner,
alongside unit tests and full HTTP matches.

A smaller optional local sandbox, with just the bot's actual dependencies:

```sh
docker build -f docker/Dockerfile.sandbox -t rangerunner-sandbox .
```

The project can run with a read-only repository, no outbound network, 1 CPU,
4 GB RAM, and only `/tmp` writable. Keep the strategy modules, `native/`, and
`preflop.npz` in the repository. Git LFS is not needed.

## Submit

Verify the team name is `winner`, run the checks on the final commit, and push all
files. The challenge requires a public repository for submission. Register your team and submit the public
URL and full commit SHA through the challenge forms. No registration or form
submission is performed by this project.

The original participant instructions are in `README_STARTER.md`.
