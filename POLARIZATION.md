# Value bets and bluffs in the opponent model

The previous three likelihood models made raises progressively more likely as
an opponent's estimated strength increased. That can overvalue a raise made
with a weak bluff. The new family retains all three models and adds two models
whose raises can come from either end of the continuing range. Their initial
combined weight is 20%; showdown evidence updates the mixture within each half.
It does not hard-code that every opponent bluffs.

Let `q` be a uniform strength percentile, `f` and `r` the estimated fold and
raise frequencies, and `s` the sharpness. As before, the fold curve is
`F(q) = sigmoid(af - s * (q - 0.5))`. Its intercept is calibrated so that the
integral over `[0,1]` equals `f`. This preserves decreasing fold probability
with increasing strength in every model.

For the polarized models, define the percentile within the continuing range:

```
u(q) = (q - integral(F(t), t=0..q)) / (1 - f)
z(q) = 2 * abs(u(q) - 0.5)
R(q) = (1 - F(q)) * sigmoid(ar + s * (z(q) - 0.5))
C(q) = 1 - F(q) - R(q)
```

Under the uniform-rank assumption, `u` is uniform conditional on continuing,
and `z` is uniform too. Calibrating the conditional raise curve to `r/(1-f)`
therefore preserves the requested unconditional fold/call/raise frequencies.
Both the fold integral and calibrated intercept have closed forms, avoiding
numerical integration during play. Numerical tests independently integrate
100,000 ranks and compare the compiled kernels with the vector formula.

Signed slopes distinguish the two families: `[0, 8, 16, -8, -16]`, with initial
weights `[.1, .2, .5, .1, .1]`. Negative slopes select the polarized family;
their absolute values set sharpness. The positive models retain the previous
formula. Response evaluation integrates the joint model/hand distribution,
including the same legality constraints and heuristic future-betting costs.

This remains an approximation. Rank ties, draw strength, selective showdowns,
unusual bluff/value ratios and changing strategies can violate its assumptions.
Equal low/high tails within the continuing range do not solve equilibrium bluff
sizing. Fresh-deal comparisons and their losses are recorded in `VALIDATION.md`.
