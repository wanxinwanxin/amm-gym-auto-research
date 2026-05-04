#!/usr/bin/env bash
# Centralised git-lock cleanup for the autoresearch sandbox.
#
# Why this exists: the sandbox's FUSE mount refuses `unlink` on .git/*
# files but allows `rename`. When a prior run is killed mid-git, its
# .git/index.lock / .git/HEAD.lock / etc. survive into the next cycle
# and jam every git command. Renaming the lock aside lets git acquire
# a fresh one; the host's launchd agent or `git gc` sweeps the stale
# names later.
#
# Cycle protocol: this script is called automatically as step 0 of
# `bin/run_checks.sh`, which the cycle's orient phase runs first thing.
# Cycle agents should NEVER improvise ad-hoc `mv .git/*.lock ...`
# commands — the only sanctioned path is to call this script.
#
# Idempotent and silent on success. Exits 0 even if there's nothing
# to clean.
set -u
shopt -s nullglob

stamp=$(date +%s)
moved=0
for lock in \
    .git/index.lock \
    .git/HEAD.lock \
    .git/config.lock \
    .git/packed-refs.lock \
    .git/objects/maintenance.lock \
    .git/refs/heads/*.lock \
    .git/refs/tags/*.lock \
    .git/refs/remotes/*/*.lock; do
  if [[ -e "$lock" ]]; then
    mv -f "$lock" "${lock}.stale.${stamp}" 2>/dev/null || true
    moved=$((moved + 1))
  fi
done

if [[ "$moved" -gt 0 ]]; then
  echo "git_unstick: moved $moved stale lock(s) aside (stamp=$stamp)"
fi
exit 0
