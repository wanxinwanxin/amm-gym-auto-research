#!/usr/bin/env bash
# Optional dep: jax is needed for arena_eval/diff_simple_amm and the
# smooth-vs-exact correlation experiment. As of cycle 9 the sandbox
# OOMs at `pip install jax[cpu]` (3.9 GB total RAM, no swap), so
# diff-simple-amm work is blocked on this host.
#
# This check passes if jax is importable. If it fails, the cycle should
# either skip diff/smooth work or attempt a smaller-footprint install
# (e.g. via wheel index, --no-build-isolation).
set -u
if python3 -c "import jax" >/dev/null 2>&1; then
    ver="$(python3 -c 'import jax; print(jax.__version__)')"
    echo "ok: jax importable ($ver)"
    exit 0
fi
echo "FAIL: jax not importable; diff/smooth experiments are blocked on this sandbox"
echo "Fix: pip install --break-system-packages --no-cache-dir jax jaxlib (may OOM)"
exit 1
