# Experiments retained, disabled in production

These are completed development comparisons against the frozen b15a release.
The final release retains its betting policy and changes calculation cost only.
Each comparison plays both policies on common duplicate deals, with fresh half
memory and an 80-second offline accounting budget. The actual tournament budget
is tested separately through HTTP. The local opponents share project code and
are not independent elite bots.

| Folder | Approach | Why it remains experimental |
|---|---|---|
| river-tree | Bounded river best response, learned sizes | Mixed gains; worse results against check-raising and selective opponents |
| river-tree-context | Tree plus distinct river contexts | Inconsistent changes across opponents |
| early-context-prototype | Independent river context reads | Early prototype, before final terminal-context consistency guards |
| independent-context-c/d | Corrected context reads, compiled calculation | Mean paired change -0.0128 bb/deal across the 12-opponent, two-seed pool |
| pooled-context-prior | Context counts with a broader learned prior | Mixed results, no reliable playing-strength improvement |
| shared-stream-precision | Expand close river calls to 4096 samples | Extra draws also shifted future baseline sampling; retained for diagnosis |
| precision-g/h, precision-head | Separate refinement RNG and selective expansion | Numerical accuracy improved, playing advantage not established |

The separate-stream precision pool changed by -0.0218 bb/deal, descriptive 95%
interval [-0.0533, +0.0096]. The direct comparison against the previous bot,
6,000 duplicate deals, changed by -0.1152, interval [-0.2662, +0.0359]. Both
intervals contain zero. Negative point estimates are retained. The two direct
seeds copied from precision-g/h into precision-head must not be counted twice.
The precision cohort contains 112,000 physical hands including controls.

The numerical accuracy test independently compares 1280- and 4096-sample
estimates to all 65,780 legal opponent hands. It improves RMSE on that benchmark,
which does not establish a poker win-rate gain for the adaptive policy.

Completed development comparisons in these folders contain 345,600 physically
played hands including controls, with shared deal reuse. This excludes partial
setup attempts and numerical samples. It is not a count of independent deals.

These prototypes evolved during research. Earlier working-tree fingerprints
and raw records are historical evidence, not promises that every current
research adapter exactly recreates every early snapshot. The precise enabled
precision policy snapshot is preserved in precision-enabled-source/ and its
five file hashes match precision-g/h and precision-head. The final released
source has separate fingerprints under ../regression/ and the root manifest.

The supplied rules, referee and legal-action assertions were used throughout.
No experiment accessed hidden opponent cards during play. Complete enumeration
and revealed cards are used only in numerical tests and normal showdown learning.
