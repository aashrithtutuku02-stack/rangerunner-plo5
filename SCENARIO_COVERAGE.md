# Scenario coverage and its limits

The complete betting-history sweep uses the supplied rules: two equal 80-chip
stacks, blinds 1/2, four streets and at most four raises per street. It follows
every legal action from every prefix, including separate half-pot and pot labels
when they clip to the same all-in amount. Histories are never merged.

For one fixed deal and button position, there are **15,952 decision prefixes**,
**25,538 complete terminal histories**, 41,489 action edges, 678 distinct numeric
states and at most 14 actions in a hand. We checked all of those histories on
eight fixed deals and both button positions.

| Full-policy sweep | Checks |
|---|---:|
| Complete terminal histories | 408,608 |
| Distinct decision prefixes evaluated | 255,232 |
| Replayed decisions preserving learning and RNG | 255,232 |
| Terminal-response inference checks, both players | 817,216 |
| Duplicate result callbacks checked | 817,216 |
| Learning-state comparisons to referee-derived events | 1,072,448 |

The bot chooses an action at every prefix. The test then forces every legal
continuation, recording that actual forced action in its pending observation.
This covers histories the current policy would not choose naturally. These are
counterfactual correctness checks, not 408,608 independent matches or a win rate.

The deals cover a random board, an unbeatable flush, the A6789 wheel, actual
quads, a split pot, four equal board ranks, four equal hole ranks, and a flush
beating a full house. The supplied terminal evaluator is memoized by its exact
input cards only; the referee's transition, visibility and payment code remains
unchanged. Scores are also compared to the native engine.

## Other covered scenarios

* All 376,992 five-card rankings are compared to the supplied evaluator.
* Hole-card order, flop order and all 24 suit renamings preserve exact scores on
  the named deals. Equivalent card-order retries reuse the existing samples.
* Hidden opponent cards and unseen future cards are changed in 192 public-frame
  comparisons across both roles and all four streets. Identical public inputs
  produce identical decisions with fresh identical memory.
* The HTTP matrix crosses three endpoints, two startup states, three token
  classes and four body classes: 72 combinations. Refusals before startup,
  bad authentication, malformed bodies and normal requests have their expected
  status codes. Additional cases cover failed-request recovery, duplicate and
  reordered result batches, half resets, and a failed result followed by retry.
* Direct lifecycle cases cover old observations, shorter or conflicting history
  prefixes, completed-hand replays, duplicate callbacks, partial failures and
  reused memory dictionaries. Failures roll back learning and random state;
  calculation time remains charged. Stale observations receive the legal
  conservative default without replacing the live hand's pending state.
* Sampling tests cover full, half and minimum counts on all four streets, and
  reusing a cache after the internal budget drops. Separate real HTTP and
  one-CPU checks enforce the actual tournament deadlines.
* A separate one-CPU, read-only load run repeats a longest fourteen-action line
  for 1,000 hands, evaluating both players and their result callbacks. Those
  actions are forced for load testing, and calculation timings exclude HTTP.
* Ordinary-play regression covers all 26 named local policies and eight selected
  parameter-search cases. These share project code and are not independent
  elite poker engines. The guards preserve regular-play returns on this suite.

## Reproduce

```sh
python -m pytest -q
python scenario_sweep.py --cases all --buttons 0 1 --output scenario-results
python tools/check_scenarios.py scenario-results --check-source
```

The full sweep uses an offline accounting budget that keeps the default 768/
1,280 samples fixed. It does not enforce the real HTTP time bank. Use
`--accounting-only` for a faster public-history check; the report checker rejects
that mode as evidence of a full-policy sweep. GitHub runs both full button sweeps
as separate jobs and verifies their source identities and completeness.
It also runs the longest-line load inside the exact organizer image. The
supplied smoke fixtures contain out-of-order hand IDs, so some smoke responses
exercise the stale-request fallback; full-policy evidence comes from the valid
history sweeps, ordinary matches and longest-line calculation test.

## What this cannot establish

It is exhaustive over betting histories **for each selected deal**, at the
current rules. It is not exhaustive over card deals. There are
505,625,240,363,443,200 arrangements with each player's five-card hand unordered
and the five board positions ordered, before counting action histories. Flop
permutations are equivalent presentations, but even removing that redundancy
leaves an impractical number of distinct situations.

The API has an unbounded number of possible packets and repetitions; the matrix
tests defined classes, not every JSON value or every network schedule. The
supported referee protocol has one active half per server, increasing hand
indices within that half, complete public histories, and legal observations on
the acting player's turn. It does not request actions after a hand ends. A
cross-half packet with a reused hand index cannot always be distinguished from a
current packet without an episode identifier; real tournament halves use fresh
server processes. Arbitrary rule changes and resource starvation are outside
the exhaustive claim.

Correctness coverage does not solve the game or prove that this strategy beats
every opponent. The opponent model and future betting remain approximate.
See [VALIDATION.md](VALIDATION.md) for performance and resource results and
[WEAKNESSES.md](WEAKNESSES.md) for remaining strategic limits.
