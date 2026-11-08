# Iteration 5 evidence

Experiments were run November 7, 2026, America/Chicago. Raw timestamps and seed
labels may use November 8 UTC. The production comparison baseline is frozen
release `52c5a1733a59e95246584b6b7e84ec2b72abeff8`.

The experiment sequence is retained, including regressions:

1. `discovery/polar10` and `polar20`: 600 duplicate deals, ten opponents,
   one discovery seed each. `broad10` and `broad20`: 800 deals, sixteen opponents,
   a second discovery seed. The 20% nominal polarized mixture had the better
   mean on both cohorts.
2. `holdout/` and `holdout-summary.json`: the first selected candidate's four
   fresh 1,000-deal seeds against sixteen opponents. Its pooled change was
   +0.10214 bb/duplicate deal, descriptive normal interval [+0.00130, +0.20299].
   However, the four-seed t interval was [-0.02607, +0.23035], and the
   independent adaptive, checkraise and nit opponents showed descriptive
   declines. This was insufficient evidence of a broad improvement.
3. `discovery/joint-discovery` and `prior-discovery`: research on updating the
   within-hand model mixture, with and without prior-centered regularization.
   These use separate discovery seeds; their mean scores are not paired with
   one another. They remain disabled in production.
4. `discovery/gated-discovery` and `gated-joint-discovery`: a common 600-deal
   discovery seed, sixteen opponents. Gating alone was selected for the final
   evaluation: it had similar pooled improvement and better adaptive and
   opportunist changes. The original value-model prior ratios were restored.
5. `final-holdout-protocol.json` records the final frozen implementation,
   four new seeds and evaluation scope before the final cohort completed.
   `final-holdout/` retains all 64 records. The equal-opponent change was
   +0.12054 bb/duplicate deal, descriptive deal-cluster normal interval
   [+0.02492, +0.21616]. All four seed means were positive, and their
   descriptive t interval was [+0.04315, +0.19793]. Individual paired declines
   remain visible. Final playing and runtime results are described in the root
   `VALIDATION.md`.

Each comparison record contains both policies' seat-swapped returns, paired
differences, sample counts and source identities. Four physical hands are
played for each paired policy observation: two candidate seats and two control
seats. Opponents within one seed share the same deals. The summary clusters
those shared deals before calculating uncertainty; it does not pretend that
sixteen opponents create sixteen independent card samples. Intervals remain
descriptive because learning creates dependence between successive hands.

The first discovery cohort predates the additional-helper hash field. It is
development evidence. Later source snapshots preserve adapter versions;
`3a4a16c` records the first polarized implementation, and `9a8695d` records the
gated implementation. Frozen research and release opponents do not inherit
later production policy changes. The comparison runner also verifies identical
frozen policies have exactly zero duplicate-deal returns.

The successful first-candidate GitHub status is in `candidate-ci.json` and on
[GitHub](https://github.com/aashrithtutuku02-stack/rangerunner-plo5/actions/runs/42438522916).
It checks all four jobs, including both exhaustive history sweeps and the exact
organizer container. That status concerns the first candidate; it is not a
substitute for checking the final implementation. GitHub report artifacts are
linked from the run. Automated artifact/log download in this environment
returned HTTP 403, so no missing artifact is represented as a downloaded report.
