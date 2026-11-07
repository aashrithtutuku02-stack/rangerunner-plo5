# Weaknesses and limits

No finite opponent suite proves that a poker bot wins against every possible
opponent. An identical strategy can draw in expectation; a specially constructed
counter-strategy may exploit any approximation here. This bot is for the supplied
short-deck PLO5 rules, not ordinary Hold'em or arbitrary poker variants.

## Problems found and addressed

1. **Selective opponents were underestimated.** A stricter range-aware challenger
   beat the development bot by about 1.1 bb per duplicate deal. The selected
   model prior includes much more selective betting ranges. Independent-seed
   results and confidence intervals are retained, including draws.
2. **Response mixtures lost model/hand dependence.** Multiplying an averaged
   hand range by separately averaged response probabilities created artificial
   cross-model combinations. Responses now use the joint model/hand posterior.
   A direct law-of-total-probability test checks the correction.
3. **Observed call prices were ignored.** History likelihoods now use the same
   price adjustment as prospective responses. Initial forced contributions are
   recovered from chip conservation rather than hard-coded blind amounts.
4. **The strict CPU test exhausted the bank.** A development build skipped
   decisions in a 1-CPU match. The likelihood loops now compile once at startup,
   and the internal budget accounts for hand-result processing and leaves a
   larger margin. The final constrained match reports are included.
5. **Native inputs could be unsafe if misused.** Public scoring/simulation APIs
   now reject malformed shapes, duplicates, invalid card IDs, and invalid sample
   counts or random states before entering native code.
6. **Check-raising behavior was averaged into initial-bet responses.** A
   selected search policy produced a clear loss on one evaluation seed. Initial
   bets and re-raises now use distinct learned frequency buckets, replacing a
   fixed re-raise multiplier. Final independent-seed results are retained.
7. **Some extremely weak hands were unnecessarily completed.** The small-blind
   exception was removed. Four low hole-card quads can correctly fold even for
   the 1-chip completion price.

## Remaining strategic limits

* The game has not been solved to a Nash equilibrium. Betting policy and
  opponent likelihoods are approximate, and action selection is mostly
  deterministic given the samples and learned state.
* There are only a few opponent selectivity models. Highly unusual sizing,
  multi-street traps, or opponents that deliberately change their strategy can
  differ from every model. Street and facing-bet frequency buckets are coarse.
* Early-street made-hand percentiles are imperfect proxies for how an opponent
  values draws. Hero equity is simulated, but opponent action likelihoods do not
  solve its decision problem.
* Future betting and reraises are accounted for with heuristic discounts and
  penalties. The bot does not search the full multi-street game tree.
* Opponent learning depends on public actions and selectively revealed showdown
  cards. It cannot observe folded cards; limited showdowns and selection effects
  can produce inaccurate reads. The two tournament halves deliberately do not
  share learned information.
* Live and preflop equity estimates have sampling error. The sampled opponent
  range can be sparse, particularly after several selective bets. Timing-based
  sample reduction increases that uncertainty.
* A few test opponents yield confidence intervals containing zero. Those are
  draws, not demonstrated wins. Passing local tests is not evidence of defeating
  independently developed elite bots or a guaranteed tournament result.

## Runtime and test scope

The 678-state graph test covers every reachable numeric betting state for one
fixed legal deal; it is not an exhaustive enumeration of all card deals and
history combinations. Five-card ranking comparison is exhaustive, while full
Omaha combinations and sampler equivalence use large deterministic samples.

CPU scheduling, transport latency, and future library versions can alter timing.
The shared development workspace has only two parent CPU cores. Concurrent CPU
stress suites can over-subscribe that parent even when a bot container has a
1-CPU limit; overloaded timing failures are retained alongside serial, isolated
resource checks. A CPU quota is a maximum, not an exclusive CPU reservation.
The current native target is Linux x86-64; other platforms use the slower Numba
fallback. The compiled backend and fallback are both tested. The team identity
must still be set correctly before tournament submission.

Raw discovery losses and the failed CPU run are preserved so that the release
report does not hide the cases that motivated changes.
