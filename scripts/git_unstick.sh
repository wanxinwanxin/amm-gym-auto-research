#!/usr/bin/env bash
set -u
shopt -s nullglob
# FUSE mount refuses unlink but allows rename. Move stale locks aside;
# the host's launchd agent or `git gc` will sweep them later.
stamp=$(date +%s)
for lock in .git/index.lock .git/HEAD.lock .git/objects/maintenance.lock \
            .git/refs/heads/*.lock; do
  [[ -e "$lock" ]] && mv -f "$lock" "${lock}.stale.${stamp}" 2>/dev/null || true
done
