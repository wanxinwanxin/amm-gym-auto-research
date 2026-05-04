#!/usr/bin/env bash
# Run every executable script in bin/checks/. Each check exits 0 if its
# assumption still holds, nonzero if reality has changed. Print a one-line
# pass/fail summary per check, and exit nonzero overall if any flipped.
#
# Conventions
#   - A check is a small, fast script (≤2s ideally). It must be idempotent
#     and read-only.
#   - The check's stdout/stderr is captured; only the last line is shown
#     in the summary unless verbose mode is set.
#   - Set CHECKS_VERBOSE=1 to dump full stdout for failing checks.
#   - Cap: ~12 active checks total. Retire (delete) any whose result has
#     flipped — the workaround is no longer needed.

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECKS_DIR="$ROOT/bin/checks"

# Step 0: clear stale .git/*.lock files BEFORE running any check or git
# operation. This sandbox's FUSE mount refuses unlink but allows rename,
# so leftover locks from a killed prior run jam every git command until
# they're moved aside. Centralising this in one place means the cycle
# agent never needs to improvise ad-hoc `mv .git/index.lock ...` commands
# (which produced one approval-prompt per variation under the old setup).
if [[ -x "$ROOT/scripts/git_unstick.sh" ]]; then
    (cd "$ROOT" && bash scripts/git_unstick.sh) || true
fi

if [[ ! -d "$CHECKS_DIR" ]]; then
    echo "no $CHECKS_DIR — nothing to run"
    exit 0
fi

n_pass=0
n_fail=0
n_skip=0
failed_names=()

shopt -s nullglob
for check in "$CHECKS_DIR"/*.sh "$CHECKS_DIR"/*.py; do
    name="$(basename "$check")"
    if [[ ! -x "$check" ]]; then
        printf '  SKIP %-50s (not executable)\n' "$name"
        n_skip=$((n_skip + 1))
        continue
    fi
    out="$("$check" 2>&1)"
    code=$?
    last_line="$(printf '%s\n' "$out" | tail -n 1)"
    if [[ "$code" -eq 0 ]]; then
        printf '  PASS %-50s %s\n' "$name" "$last_line"
        n_pass=$((n_pass + 1))
    else
        printf '  FAIL %-50s (exit %d) %s\n' "$name" "$code" "$last_line"
        n_fail=$((n_fail + 1))
        failed_names+=("$name")
        if [[ "${CHECKS_VERBOSE:-0}" == "1" ]]; then
            printf '%s\n' "$out" | sed 's/^/      /'
        fi
    fi
done

printf '\n%d pass, %d fail, %d skip\n' "$n_pass" "$n_fail" "$n_skip"
if [[ "$n_fail" -gt 0 ]]; then
    printf 'Failed: %s\n' "${failed_names[*]}"
    exit 1
fi
exit 0
