#!/usr/bin/env bash
# Operational fact (cycles 1-8): a fresh sandbox needs these deps
# installed via `pip install --break-system-packages`. This check
# verifies the *essential* deps used by exact_simple_amm + arena_search
# import. (jax is needed by diff_simple_amm only and intermittently
# OOMs on this sandbox — checked separately in 03b.)
set -u
missing=()
for mod in numpy gymnasium pyarrow pytest; do
    if ! python3 -c "import $mod" >/dev/null 2>&1; then
        missing+=("$mod")
    fi
done
if [[ "${#missing[@]}" -gt 0 ]]; then
    echo "FAIL: missing essential modules: ${missing[*]}"
    echo "Fix: pip install --break-system-packages --no-cache-dir ${missing[*]}"
    exit 1
fi
echo "ok: numpy/gymnasium/pyarrow/pytest importable"
