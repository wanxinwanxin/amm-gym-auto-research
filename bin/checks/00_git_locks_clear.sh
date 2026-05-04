#!/usr/bin/env bash
# Operational fact (cycles 1-9): the FUSE-mounted .git directory keeps
# stale .git/*.lock files around when prior runs are killed. The
# `bin/run_checks.sh` driver calls `scripts/git_unstick.sh` *before*
# any check runs, so by the time this check fires, all locks should
# already be moved aside.
#
# Pass: no live .git/*.lock files (only .stale.* renamed copies, if any).
# Fail: a live lock is still present — which means run_checks.sh either
#       skipped git_unstick.sh, or git_unstick.sh failed silently. Either
#       way, the cycle should NOT proceed to git operations until this
#       is resolved.
#
# Numbered 00 so it sorts before all other checks; if this fails, the
# git-touching checks (01, 06, 07) would also fail and the failure
# message would be misleading.
set -u

live_locks=()
shopt -s nullglob
for lock in .git/index.lock .git/HEAD.lock .git/config.lock \
            .git/packed-refs.lock .git/objects/maintenance.lock \
            .git/refs/heads/*.lock .git/refs/tags/*.lock \
            .git/refs/remotes/*/*.lock; do
    if [[ -e "$lock" ]]; then
        live_locks+=("$lock")
    fi
done

if [[ "${#live_locks[@]}" -gt 0 ]]; then
    echo "FAIL: live .git locks present: ${live_locks[*]}"
    echo "Fix: run \`bash scripts/git_unstick.sh\` to move them aside."
    exit 1
fi

echo "ok: no live .git/*.lock files"
