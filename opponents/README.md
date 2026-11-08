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
