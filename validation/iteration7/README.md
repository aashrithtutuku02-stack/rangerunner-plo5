# Iteration 7 evidence

The released candidate uses a conservative rolling read of frequent callers.
See the root [validation report](../../VALIDATION.md) and [calling-read design](../../CALLING_READ.md).

* `final-holdout-protocol.json`: source identities, acceptance criteria, 24 local
  opponents and four fresh 1,000-deal seeds recorded before evaluation.
* `final-holdout/` and `final-holdout-summary.json`: all 96 paired comparison
  records, shared-deal intervals, four-seed t interval and read activation counts.
* `final-source/`: changed comparison sources frozen before the cohort. Other
  unchanged dependencies are recoverable from baseline commit 9efa86c.
* `unit-tests.txt`: 306 final tests passed. The descriptive development unit log
  retains an old experimental negative-control test that initially compared the
  changing production policy instead of its frozen re-raise prototype; that
  isolation is corrected in the final tests.
* `runtime-protocol.json`, `runtime-checks.py`, `runtime-identity-check.py`,
  `runtime-identity.json`, `worst-line-load.json`, `offline-smoke.txt`: serial
  restricted-runtime checks and exact source identities. `runtime-resume.py`
  resumes the HTTP checks after the baseline Docker binding repair.
* `development-cpu-startup/`: original unreachable-baseline reports and the
  original harness. These are transport failures, not playing-strength evidence.
* `cpu/` and `cpu-comparison.json`: matched-seed old/new one-CPU HTTP matches.
* `http/`, `fresh-process/` and `external-final/`: original real-bank referee
  reports, fresh servers between halves and independent public-bot diagnostics.

Development cohorts remain separate from fresh evaluation:

* `discovery/margin-once-a`, `margin-none-a`: 600 deals × ten opponents, seed a.
* `street-split-b`, `street-mix-b`: 600 deals × ten opponents, separate seed b.
* `margin-none-c`, `street-mix-c`: 800 deals × twenty opponents, common seed c.
* `margin-value-d2`, `margin-passive-d2`: 600 deals × 24 opponents, common seed d2.
* `initial-calling-draft/`: incomplete discovery stopped to retain capped/all-in
  folds as negative evidence. Its original helper and partial records remain.
* `source-initial`, `source-broad`, `source-calling`: exact changed research
  sources for their respective phases; original dependencies remain in 9efa86c.

Each paired policy observation uses four physical hands: both seats for both
candidate and control. Opponents sharing a seed use the same deals. The pooled
summary clusters shared deals instead of counting each opponent as independent
new cards. Learning creates additional dependence; intervals are descriptive.
All rejected experiments remain disabled in production. No external bot source
is copied into this repository.
