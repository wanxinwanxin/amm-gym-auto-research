#!/usr/bin/env bash
# Optional dep: jax is needed for arena_eval/diff_simple_amm and the
# smooth-vs-exact correlation experiment. The sandbox has 3.9 GB total
# RAM (no swap), so a fresh `pip install jax` triggers a transitive
# wheel build that OOMs (exit 143). The fix is to vendor pre-built
# manylinux2014_aarch64 wheels in vendored-wheels/ and install from
# there with --no-index. See bin/setup_jax_from_vendored.sh.
#
# This check passes if jax is importable, installing from the vendored
# wheels on first run if needed. Fails if the wheels are missing or
# broken.
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

if python3 -c "import jax" >/dev/null 2>&1; then
    ver="$(python3 -c 'import jax; print(jax.__version__)')"
    echo "ok: jax importable ($ver)"
    exit 0
fi

if [[ ! -x "$ROOT/bin/setup_jax_from_vendored.sh" ]]; then
    echo "FAIL: jax not importable and bin/setup_jax_from_vendored.sh missing"
    exit 1
fi

if ! "$ROOT/bin/setup_jax_from_vendored.sh" >/tmp/jax_setup.log 2>&1; then
    echo "FAIL: vendored-wheels install failed; see /tmp/jax_setup.log"
    tail -n 5 /tmp/jax_setup.log >&2
    exit 1
fi

if ! python3 -c "import jax" >/dev/null 2>&1; then
    echo "FAIL: vendored install reported ok but jax still not importable"
    exit 1
fi

ver="$(python3 -c 'import jax; print(jax.__version__)')"
echo "ok: jax installed (vendored, $ver)"
exit 0
