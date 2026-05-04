#!/usr/bin/env bash
# Install jax (and its deps) from wheels vendored in vendored-wheels/.
#
# Why: the sandbox has 3.9 GB RAM and pip install jax OOMs at build time.
# The vendored wheels are pre-built for cp310 / manylinux2014_aarch64 so
# pip can install with --no-index (no network, no build).
#
# Usage:
#   bin/setup_jax_from_vendored.sh
#
# Exits 0 if jax is already importable, or if installation from vendored
# wheels succeeds. Exits nonzero with a clear message otherwise.

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WHEELS="$ROOT/vendored-wheels"

if python3 -c "import jax" >/dev/null 2>&1; then
    ver="$(python3 -c 'import jax; print(jax.__version__)')"
    echo "ok: jax already importable ($ver)"
    exit 0
fi

if [[ ! -d "$WHEELS" ]]; then
    echo "FAIL: $WHEELS not found; cannot install jax offline"
    exit 1
fi

# Need at least one jax wheel and one jaxlib wheel in the dir.
shopt -s nullglob
jax_whls=("$WHEELS"/jax-*.whl)
jaxlib_whls=("$WHEELS"/jaxlib-*.whl)
if [[ ${#jax_whls[@]} -eq 0 || ${#jaxlib_whls[@]} -eq 0 ]]; then
    echo "FAIL: $WHEELS missing jax or jaxlib wheel"
    exit 1
fi

# --no-index forbids PyPI fallback (which would re-trigger the build OOM).
# --find-links points pip at the local dir for jax + transitive deps.
# --break-system-packages is needed on the sandbox's system python3.
if ! python3 -m pip install \
        --break-system-packages \
        --no-index \
        --find-links="$WHEELS" \
        jax jaxlib >/tmp/jax_install.log 2>&1; then
    echo "FAIL: pip install from vendored wheels errored; see /tmp/jax_install.log"
    tail -n 20 /tmp/jax_install.log >&2
    exit 1
fi

if ! python3 -c "import jax" >/dev/null 2>&1; then
    echo "FAIL: jax installed but not importable"
    exit 1
fi

ver="$(python3 -c 'import jax; print(jax.__version__)')"
echo "ok: jax installed from vendored wheels ($ver)"
exit 0
