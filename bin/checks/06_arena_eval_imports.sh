#!/usr/bin/env bash
# Cheap import smoke test: ensures arena_eval, arena_search, arena_policies
# import cleanly with no breakage from inherited working-tree changes
# (working tree includes uncommitted edits across these packages per
# STATE.md cycle-8 notes).
set -u
out="$(python3 - <<'PY' 2>&1
import sys
sys.path.insert(0, ".")
try:
    import arena_eval.exact_simple_amm  # noqa: F401
    import arena_search.simple_amm_search  # noqa: F401
    import arena_policies  # noqa: F401
except Exception as exc:
    print(f"FAIL: {exc.__class__.__name__}: {exc}")
    sys.exit(1)
print("ok: arena_eval/arena_search/arena_policies import")
PY
)"
echo "$out"
echo "$out" | grep -q "^ok:" || exit 1
