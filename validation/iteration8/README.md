# Iteration 8: opt-in bluff experiments

The tournament strategy remains byte-identical to release 3aa177f. Read
[BLUFF_EXPERIMENTS.md](../../BLUFF_EXPERIMENTS.md) before choosing an experimental
entrypoint. Neither fresh comparison established a reliable strength gain.

* `discovery/`: completed 25%/50% mix comparisons and exact changed sources.
* `draft-discovery/`: incomplete initial prototype, stopped to exclude blind
  completions from voluntary-bet fold evidence; original source retained.
* `mixed-protocol.json`, `mixed-source/`, `mixed-holdout/`, `mixed-summary.json`:
  frozen mixed-bluff evaluation, four fresh 750-deal seeds and ten opponents.
* `pure-protocol.json`, `pure-source/`, `pure-holdout/`, `pure-summary.json`:
  stricter fold-only scoring, two separate fresh seeds and eight opponents.
* `pure-cpu/`, `pure-http/`: real 8-second judge checks for the strict variant,
  including a one-CPU/4GB constrained hero. Both players' fault counters pass.
* `mixed-http/`: fresh-process real-bank checks of the dedicated mixed-bluff
  entrypoint. HTTP verification is functional evidence, not proof of a gain.
* `candidate-unit-tests.txt`: 317 tests passed with the candidate wired into
  production for testing. `unit-tests.txt` records the final safe configuration.

The initial local load command encountered a source-file read-permission issue;
that diagnostic is retained in `worst-line.txt`. Local file permissions were
aligned with the organizer image's read permissions before the successful
one-CPU HTTP checks. No game rule, scoring function or original server changed.

The default strategy and complete-history sweep were restored to the validated
release after the bluff candidates failed the acceptance criteria. Rejected
policies remain explicitly selectable through `bluff_agent.py`; they are never
silently enabled by the tournament entrypoint.
