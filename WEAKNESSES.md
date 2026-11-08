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

8. **Selective likelihoods inflated action frequency.** Raising the old model
   slope could turn a low observed raise rate into a much larger model average.
   The new ordered model calibrates intercepts over a uniform rank percentile.
   Its marginal frequencies, normalization and monotonicity are checked by
   numerical integration and by compiled/Python equivalence.
9. **Final responses were missing from learning evidence.** Verified final
   calls and checks are now part of showdown learning, including preflop
   showdowns. Inconsistent pots or stale callbacks are rejected.
10. **Unavailable raises were treated as possible choices.** Observed action
    history now reconstructs whether raising was legal. All-ins and capped
    streets merge raise likelihood into call likelihood; censored calls do not
    spuriously teach that an opponent dislikes raising. A final allowed raise
    is no longer penalized for an impossible immediate re-raise.
11. **Bet evaluation repeated Python and array work.** Both raise sizes now
    integrate the joint posterior in a warmed compiled loop. The numerical
    formula is unchanged and checked against the independent vector formula.
    More available CPU time does not by itself guarantee better poker results.
12. **Clipped all-in sizes repeated the same calculation.** When half-pot and
    pot raises reach the same all-in target, the kernel now reuses the value.
    The existing action preference and legal sizes are preserved.
13. **Replayed events could corrupt lifecycle state.** Old observations could
    rewind the history cursor or reopen a completed hand, and duplicate results
    changed completion counters. Completed-hand tracking and prefix checks now
    discard stale requests without changing the live hand's learning or RNG.
14. **Failures could leave partial learning behind.** Decision and result
    processing now restore learning state after an exception, so a corrected
    retry does not double-count an action. The original server still reports
    the error to its caller.
15. **Equivalent card ordering caused extra sampling.** Cache keys now normalize
    hole order and flop order while preserving turn/river arrival order.
16. **Direct half initialization retained unknown keys.** Initialization now
    clears a reused dictionary as well as resetting all known learning fields.

## Remaining strategic limits

* The game has not been solved to a Nash equilibrium. Betting policy and
  opponent likelihoods are approximate, and action selection is mostly
  deterministic given the samples and learned state.
* The calibration assumes rank percentiles, which imperfectly represent actual
  equity and can contain ties or compressed early-street distributions. Matching
  the rank-model margins does not guarantee calibrated predictions for every
  board, history, opponent, or population.
* There are only a few opponent selectivity models. Highly unusual sizing,
  multi-street traps, or opponents that deliberately change their strategy can
  differ from every model. Street and facing-bet frequency buckets are coarse.
  Finer river buckets, including probes and check-raises, were tested; the
  additional sampling uncertainty and mixed playing results did not justify
  replacing the current model. Both independent and pooled-prior variants are
  retained as research tools.
* Early-street made-hand percentiles are imperfect proxies for how an opponent
  values draws. Hero equity is simulated, but opponent action likelihoods do not
  solve its decision problem.
* Future betting and reraises are accounted for with heuristic discounts and
  penalties. The bot does not search the full multi-street game tree.
  A bounded river-search experiment was tested and retained for research, but
  its inconsistent gains did not justify enabling it in the tournament bot.
* Opponent learning depends on public actions and selectively revealed showdown
  cards. It cannot observe folded cards; limited showdowns and selection effects
  can produce inaccurate reads. The two tournament halves deliberately do not
  share learned information.
* Live and preflop equity estimates have sampling error. The sampled opponent
  range can be sparse, particularly after several selective bets. Timing-based
  sample reduction increases that uncertainty.
  Extra river sampling improved numerical accuracy against full enumeration,
  but the match comparison did not establish a playing-strength gain. That
  experiment remains disabled. More accurate estimates of an approximate
  opponent model do not guarantee better actual decisions.
* A few test opponents yield confidence intervals containing zero. Those are
  draws, not demonstrated wins. Passing local tests is not evidence of defeating
  independently developed elite bots or a guaranteed tournament result.

## Runtime and test scope

The 678-state graph test covers every reachable numeric betting state for one
fixed legal deal; it is not an exhaustive enumeration of all card deals and
history combinations. The new full-history suite separately covers every legal
betting history on eight fixed deals and both buttons; see
[SCENARIO_COVERAGE.md](SCENARIO_COVERAGE.md) for the precise boundary. It does not
cover every card deal or every possible network/API sequence. Five-card ranking comparison is exhaustive, while full
Omaha combinations and sampler equivalence use large deterministic samples.

CPU scheduling, transport latency, and future library versions can alter timing.
The shared development workspace has only two parent CPU cores. Concurrent CPU
stress suites can over-subscribe that parent even when a bot container has a
1-CPU limit; overloaded timing failures are retained alongside serial, isolated
resource checks. A CPU quota is a maximum, not an exclusive CPU reservation.
The current native target is Linux x86-64; other platforms use the slower Numba
fallback. The compiled backend and fallback are both tested. The team identity
defaults to `winner`; an environment override can still change it.

Raw discovery losses and the failed CPU run are preserved so that the release
report does not hide the cases that motivated changes.
