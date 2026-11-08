# Frozen incumbent

`incumbent_36ba.py` and `incumbent_range_model.py` preserve the strategy and
likelihood mathematics of release `36ba2d9719d0cad40d67d900c887d4f03727f2ae`.
The strategy's import points to its frozen helper so changing the new helper
cannot silently change the comparison opponent. Both policies use the same
unchanged card engine and preflop asset. Learned state is separate per half.

These files are local regression opponents, not independent elite poker bots.

`release_b15a.py` and `release_b15a_model.py` similarly freeze release
`b15a8402286cb93f901c84f3eabd2911be5784ea`, with only the helper import
redirected. Use opponent/baseline name `release-b15a` to compare against it.

`release_f452.py` freezes release `f452b09e8ebd6fd6eb9d17035f41e5b626712fcb`.
Its unchanged likelihood mathematics uses `release_b15a_model.py`; the shared
`bet_ev_52c5.py`, native engine and preflop asset preserve the f452 formulas.
Its two helper imports are redirected to frozen modules. Its test name is
`release-f452`.

`release_52c5.py` freezes release
`52c5a1733a59e95246584b6b7e84ec2b72abeff8`, including its lifecycle guards.
The only substitutions are the imports of the frozen likelihood helper and
`bet_ev_52c5.py`. That kernel redirects its helper import too. These preserve
the old three-model strategy when the production model changes. The helper
is byte-identical to the likelihood model in 52c5. Its test name is
`release-52c5`. Native card code and the preflop asset remain shared and unchanged.

`independent_opponents.py` contains three separately written local challengers:
value-focused, polarized and fold-adaptive. Their decision logic imports no
released strategy, likelihood model or bet kernel. They share the card engine
and referee data types, so they are not external elite-bot validation.

`polar20_3a4a.py` freezes the first polarized candidate's strategy from
`3a4a16cfb63dc279165995d01325ddc94d1dbdfc`. Its helper imports point to the frozen
research `polar_model.py` and `polar_bet_ev.py`. The polar, joint-conditioning and
gated research adapters clone this base so later production changes cannot
silently alter earlier experiments. It is an experimental reference, not the
previous tournament release.

`release_451b.py`, `model_451b.py` and `bet_ev_451b.py` freeze release
`451b1cb9ae931c5b42a9137e388614606bfaac53`. Only the helper imports are
redirected. This is the baseline for the iteration 6 probability-kernel speed
optimization; fixed-sample duplicate returns must remain exactly unchanged.
Its opponent/baseline name is `release-451b`.

`reraise_candidate_6.py` preserves the rejected experimental re-raise router
for its numerical tests. Production imports none of these research routers.
