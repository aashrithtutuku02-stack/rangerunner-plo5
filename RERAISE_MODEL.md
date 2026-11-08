# Experimental conditioned re-raise values

This prototype remains disabled. Fresh tests did not establish a broad gain
and showed a head-to-head decline against the current release.

The earlier kernel priced an opponent re-raise as a call and then subtracted a
risk penalty based on hero equity against the whole current range. A selective
re-raising range can have substantially different equity. The new calculation
integrates that branch separately and chooses one shared fold/call response.

For each candidate raise, let `I` be hero's immediate investment and `F` the pot
after an opponent call. The existing joint hand/model distribution supplies the
probability mass `M` of an opponent re-raise and its equity-weighted mass `W`.
For a re-raise requiring an additional matched hero contribution `D`, the branch
value is:

```
max(-M * I, W * (F + 2 * D) - M * (I + D))
```

The maximum is taken after integrating all hidden hands and models. Hero cannot
choose a different response for each sampled opponent hand. Uncalled excess is
refunded, so the called pot increases by twice the matched contribution. The
kernel averages half-pot and pot re-raises with fixed weights 25% and 75%, using
the referee's integer minimum, pot-limit, stack and raise-cap rules.

Only decisions facing an actual voluntary bet use this deeper calculation.
Opening decisions and posted-blind completions preserve the previous formula.
Before the river, its blend with the old value is
`clip((.70 - observed_raise_share)/.35, 0, 1)`, using the existing public-action
frequency bucket. Against near-continuous raising it preserves the previous
early-street estimate. On the river, it uses the full one-step value. Capped and
all-in responses preserve the original value because no re-raise is available.

These restrictions followed development failures. Applying the one-step estimate
to every opening bet overvalued early commitment against always-raising bots.
Later-card information and the ability to fold on a later street have value
that a check-down approximation misses. A river-only version, a half blend,
an aggression-only limit and a postflop-only version also had mixed results.
Development losses are retained under `validation/iteration6/`.

The model remains approximate: it omits further hero re-raises, assumes later
streets check down, and does not learn the half/pot sizing mixture. The original
rank-based opponent likelihoods and equity samples also have error. Referee
branch tests establish chip accounting and information-set consistency, not
optimal play. Fresh-deal match comparisons determine whether to deploy it.
