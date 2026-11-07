#!/bin/sh
# Optional local rebuild. The tournament runs the included Linux x86-64 binary.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ "$(uname -s)" != Linux ] || [ "$(uname -m)" != x86_64 ]; then
    echo 'The included kernel targets Linux x86-64; this platform uses the Numba fallback.'
    exit 0
fi
"${CC:-cc}" -O3 -std=c99 -fPIC -shared -fno-semantic-interposition \
    -march=x86-64 -mtune=generic \
    "$ROOT/native/plo5_fast.c" -o "$ROOT/native/plo5_fast_linux_x86_64.so"
echo 'Native kernel rebuilt. Run python -m pytest -q.'
