# Opt-in bluff bots — 25-minute experiment

The validated tournament entrypoint remains `python agent.py`, with team name
`winner`. The new bluff policies are **opt-in experiments**: fresh tests did not
establish a reliable improvement over that release.

Start the mixed-bluff bot with the same HTTP protocol, token and port settings:

```sh
python bluff_agent.py
```

The default experimental mode is `bluff-quarter`. Alternatives:

```sh
RANGERUNNER_POLICY=bluff-half python bluff_agent.py
RANGERUNNER_POLICY=bluff-pure python bluff_agent.py
```

The first two mix in an extra opening bluff on 25% or 50% of otherwise eligible
weak-hand decisions. The mix is deterministically hashed from the bot's own
private cards and public frame, so retries and equivalent hole/flop orderings
preserve the decision. No opponent cards, future cards or external information
are used. This makes equivalent weak hands play differently across deals; it is
not a claim of a game-theoretically optimal or unexploitable bluff distribution.

A bluff requires all of the following:

* The existing strategy chose a free check; no opponent bet is being raised.
* Estimated equity is below 45%, and a raise is legal.
* At least 16 comparable responses support a conservative fold-frequency read.
* Folds to more expensive bets cannot justify a cheaper proposed bluff.
* A conservative score beats the current passive value plus the existing
  proportional safety margin. Calling-heavy opponents do not qualify.

Fold evidence separates preflop and postflop, retains at most 128 responses per
group and includes calls when re-raising was unavailable. Blind completions are
excluded because they precede a voluntary hero bet. Verified final folds and
calls participate in learning. Immutable tuples preserve rollback and replay
safety, and every new half resets the read.

The mixed score uses a 50% haircut to hero equity against the continuing range.
The `bluff-pure` alternative credits zero equity when called. Neither score is a
proven payoff bound: opponent range selection, behavior changes and later
betting remain approximate. The fold confidence bound is a heuristic under
dependent observations, not a guarantee of future fold frequency.

## Fresh results

Frozen baseline: `3aa177f6e9e98ea64cd3482a6b6c5bc35c50a8eb`.
All comparison seeds were separate from the discovery seed. Both policies played
both seats on the same cards, with default sample counts retained using an
80-second offline accounting bank. Original 8-second HTTP checks are separate.

| Candidate | Fresh scope | Mean change, bb/duplicate deal | Shared-deal 95% interval |
|---|---|---:|---|
| 25% mixed bluffs | 10 opponents × four seeds × 750 deals | +0.00948 | [-0.02931, +0.04828] |
| Fold-only score | 8 opponents × two seeds × 750 deals | -0.01567 | [-0.07271, +0.04138] |

That is **168,000 physical hands including controls** in the fresh comparisons.
Opponents sharing a seed reuse the same deals; the summaries cluster shared
deals rather than treating each opponent as independent new cards. Learning
creates further dependence, so intervals are descriptive.

The mixed version's gains against the adaptive challenger and overfolder were
small and uncertain, and its polarized matchup declined slightly. CallingStation,
always-pot and frozen-release comparisons remained unchanged at fixed samples.
The stricter score also failed to establish a gain. The 50% version's discovery
tradeoffs did not justify promoting it. These findings are why the production
strategy remains unchanged.

Raw records, source snapshots, protocols and real HTTP fault checks are under
[validation/iteration8](validation/iteration8/). The original referee, evaluator,
server, native engine, preflop asset and Dockerfiles remain unchanged.
