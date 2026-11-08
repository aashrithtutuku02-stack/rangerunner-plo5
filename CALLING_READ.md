# Conservative reads of frequent callers

The released strategy adds a small exploit to the released range and betting model.
It uses only observed public actions and verified final responses.

The read retains the last 64 eligible responses to a bet. Free checks provide
no evidence about willingness to call a bet. Calls when raising is unavailable
are censored and do not establish a preference for calling over raising.
A fold is still negative evidence when raising was unavailable.

At least 24 eligible responses are required. With call fraction `p` and window
size `n`, the lower Wilson bound is

```
(p + z²/(2n) - z*sqrt(p*(1-p)/n + z²/(4n²))) / (1 + z²/n), z = 1.96
```

The read is active only when that lower bound is at least 0.80. This is a
conservative policy heuristic. Actions within a poker match are dependent and
an opponent can change its behavior; the bound is not a guarantee of future
calling frequency. Restricting the window to 64 responses lets recent folds
and raises invalidate the read rather than being diluted by an entire half.

For an active read and estimated hero equity above one half, the fixed raise
safety margin is removed. The existing expected chip values rank the legal
raise sizes. The equity realization discount, range model and re-raise penalty
are preserved. Estimated equity at or below one half retains the old margin,
as do decisions without an established caller read. The feature does not relax
the bluff guard.

The immutable response tuple is part of per-half memory. Existing transaction
snapshots restore it after inference failures. Duplicate decisions/results do
not append responses twice, and new halves clear the read. Tests cover censored
calls, folds, confidence thresholds, recent behavior changes, value/bluff
separation, rollback, reset and a fixed-sample always-raising negative control.

An unconditional margin removal and separate pre/postflop selectivity models
were also tested. Their mixed or negative development results motivated this
narrower rule. Fresh-deal and real-budget validation support deploying the
guarded rule; full results and limitations are in [VALIDATION.md](VALIDATION.md).
