#!/usr/bin/env bash
# Operational fact (cycle 1+): the in-repo `.venv/bin/python` is a
# Mac-Homebrew binary that points into a path that does not exist on
# the Linux sandbox. Use system `python3` directly.
#
# This check passes if:
#   - system python3 (3.10.x) is on $PATH, AND
#   - `.venv/bin/python` either does not run, or shadows a missing path.
#
# It fails (i.e. flipped) if `.venv/bin/python` now works in the sandbox —
# which would mean we no longer need to bypass the venv.
set -u
if ! command -v python3 >/dev/null 2>&1; then
    echo "FAIL: system python3 not on PATH"
    exit 1
fi
sysver="$(python3 -c 'import sys; print(sys.version_info[0:2])')"
case "$sysver" in
    "(3, 10)"|"(3, 11)"|"(3, 12)") ;;
    *) echo "WARN: system python3 is $sysver (expected 3.10/3.11/3.12)";;
esac
if [[ -x ".venv/bin/python" ]]; then
    if ./.venv/bin/python -c 'print("ok")' >/dev/null 2>&1; then
        echo "FAIL: .venv/bin/python now runs — workaround retired? retire this check."
        exit 1
    fi
fi
echo "ok: using system python3 ($sysver); .venv shim is broken on this host as expected"
