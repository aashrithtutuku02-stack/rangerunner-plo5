# Independent public challenge bots

The benchmark harness can run compatible public bots from separate local
checkouts. Their source is not part of RangeRunner or its tournament image.
The repositories were found through public GitHub search; their public status
does not establish tournament rank or elite strength.

Pinned versions used in iteration 6:

| Repository | Commit |
|---|---|
| [Fargield/td26-poker-bot-v2](https://github.com/Fargield/td26-poker-bot-v2) | `4ce02282e8e764766d183130d3c44b8af5d2760a` |
| [shriharish1310/tamu-datathon-poker-bot](https://github.com/shriharish1310/tamu-datathon-poker-bot) | `6e5b590bc922f047de670efdd5fd599f7459a75d` |

Clone each repository outside this project and check out the specified commit.
Use the project's Python environment, then run:

```sh
python tools/fresh_match.py --opponent external:/absolute/path/to/checkout --seed my-new-seed --output external-results/bot-name
python tools/check_results.py external-results/bot-name
```

Both servers restart before each duplicate half. The original referee enforces
the actual startup limit, request deadline and 8-second time bank. The external
bot imports its own modules in a separate interpreter; its `game.py` and
`evaluator.py` must match the supplied rules byte for byte. Active module and
preflop-asset hashes are checked against the pinned checkout's Git objects.
Published default settings are used, with environment strategy overrides cleared.

The additional `/_benchmark_status` endpoint reports source hashes and counters,
not cards, samples or learned state. Instrumentation counts fallback calls and
exceptions otherwise caught inside the first bot's opponent model. The second
bot's native diagnostics expose faults and fallback latching. Missing core
imports, missing expected preflop data, callback/model errors and native fault
latching fail the comparison. Any budget-driven fallback count remains visible.
The original strategy decisions are unchanged; measurement overhead is charged.

Reports contain the original half/match JSON, source commits, fingerprints and
per-half diagnostics under `external-status/`. A short protocol probe establishes
compatibility only; it is not playing-strength evidence. Final score comparisons
and their limitations belong in [VALIDATION.md](VALIDATION.md).
