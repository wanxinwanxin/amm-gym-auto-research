#!/usr/bin/env bash
# Operational fact (cycles 4+): the sandbox cannot resolve github.com,
# so `git pull --ff-only origin main` always fails inside the sandbox.
# A host-side launchd agent ships local commits to origin every 15 min.
#
# This check is "passes if DNS to github.com still fails" — i.e. the
# workaround is still required. If DNS suddenly works, retire this check
# (and consider re-enabling `git pull` in the cycle protocol).
set -u
if getent hosts github.com >/dev/null 2>&1; then
    echo "FAIL: DNS to github.com now resolves — sandbox push restriction lifted?"
    exit 1
fi
echo "ok: github.com unresolvable (sandbox push blocker still active)"
