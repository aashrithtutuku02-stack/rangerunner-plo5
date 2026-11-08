# Iteration 6 evidence

The released change is exact probability-kernel acceleration, with no claimed
new playing-strength gain. See the archived [validation report](RELEASE_REPORT.md).

* `regression-protocol.json`, `regression/` and `regression-summary.json`: frozen
  451b versus optimized release, 39 opponents × 1,000 duplicate deals, all paired
  deltas exactly zero, original 768/1,280 samples and 80-second offline bank.
* `kernel-speed.*`: nine alternating warmed repeats × 200 calls, bit-identical
  outputs. Kernel timings exclude simulation, startup and HTTP.
* `worst-line-*`, `runtime-summary.json`, `single-cpu.*`, `cpu-check.py`,
  `runtime-identity.json`, `offline-smoke.txt`: serial restricted resource checks.
* `external-final/` and `external-summary.json`: four fresh seeds × two pinned
  public bots, with original half reports and active-core/source diagnostics.
* `http/` and `fresh-process/`: real referee and lifecycle tests.
* `unit-tests.txt` and `protected-files.json`: final local tests and unchanged
  supplied files. The earlier unit log is retained with its descriptive name.

Rejected strategy development is preserved separately:

* `discovery/full-a`, `river-a`: 600 deals × ten opponents, first discovery seed.
* `full-b`, `half-b`, `option-b`, `postflop-b`, `family-b`, `facing-b` under
  `discovery/`: 800 deals × twenty opponents on a second common discovery seed.
* `ess-c` and `recent-c`: 800 deals × twenty opponents on a third discovery seed.
* `discovery/external/`: three candidates × two public bots, one discovery seed.
  This is development evidence, separate from the final fresh external cohort.
* `discovery/source-*`: adapter snapshots for the development phases.
* `rejected-reraise-protocol.json`: frozen source identities and four new seeds
  recorded before the final re-raise cohort. Its original proposed-promotion
  wording is historical; results caused that candidate to be rejected.
* `rejected-reraise-holdout/`, `rejected-reraise-summary.json` and
  `rejected-reraise-source/`: all 80 records and the exact tested changed sources.
  The head-to-head decline and uncertain pooled change remain visible.

Paired policy observations use four physical hands each (both seats for each
policy). Opponents sharing a seed reuse the same card deals. The comparison
summary clusters those shared deals rather than counting each opponent as a
new independent card sample. Learning creates additional dependence; intervals
are descriptive. Public external bots are not copied into this repository.
The current implementation preserves the previous released strategy after the
research candidates failed to demonstrate a reliable gain.
