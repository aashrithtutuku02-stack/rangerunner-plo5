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

**Set `PARTICIPANT` in `agent.py` to your registered team name before submitting.**
The default `YOUR_TEAM_NAME` is a placeholder. `PORT`, `AGENT_TOKEN`, and the
original server protocol are preserved. The environment variable `PARTICIPANT`
can override the identity locally.

## Play and test

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
enforcement), including 21 policy families and eight selected search opponents:

```sh
python stress_benchmark.py --deals 1000 --seeds discovery-example
python stress_benchmark.py --deals 1000 --cases adversary_cases.json
```

Use genuinely fresh servers between halves to check tournament lifecycle behavior:

```sh
python tools/fresh_match.py --opponent adversary:range-tight
```

Deals repeat with the same seed. Timing-based sample allocation can change
individual decisions across machines, so identical cards do not guarantee
identical numeric reports. Confidence intervals are in **bb per duplicate deal**,
summing both seat-swapped hands, as defined by the supplied judge.

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
* `strategy.py` learns action frequencies per street for checks, initial bets,
  and re-raises. It mixes card-independent and selective value/bluff models,
  conditions the model and hand range jointly, and accounts for the price of
  observed calls and prospective responses.
* `range_model.py` compiles the repeated likelihood loops at startup. This
  keeps the model calculations out of slow repeated Python/NumPy dispatch.
* Live samples are reused within a street and decrease if measured decision
  and result-processing time gets ahead of the half's internal budget.
* All learned state, random state, and sample caches live in `memory` and reset
  every half. Global assets and compiled functions contain no learned match state.

Optional native rebuild:

```sh
bash tools/build_native.sh
```

To recreate the preflop asset outside tournament play:

```sh
python train_preflop.py --samples 8192
```

`reference_range.py` is the frozen original range strategy used by the local
range-aware challengers. These and the other adversaries are testing policies,
not independent elite poker engines. The prior search and parameter-search tools
use discovery deals; final evaluation deals are separate.

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

Set the registered team name, run the checks on the final commit, and push all
files. The challenge requires a public repository for submission; change the
repository's visibility when ready. Register your team and submit the public
URL and full commit SHA through the challenge forms. No registration or form
submission is performed by this project.

The original participant instructions are in `README_STARTER.md`.
