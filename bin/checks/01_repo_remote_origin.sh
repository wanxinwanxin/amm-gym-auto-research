#!/usr/bin/env bash
# Assumption: this clone has a single `origin` remote pointing at
# wanxinwanxin/amm-gym-auto-research. If a future cycle accidentally
# clones into a fork or adds a second remote, we want to notice before
# we attempt to push.
set -eu
remotes="$(git remote -v 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ',' | sed 's/,$//')"
if [[ "$remotes" != "origin" ]]; then
    echo "FAIL: expected exactly remote 'origin', got '$remotes'"
    exit 1
fi
url="$(git remote get-url origin)"
case "$url" in
    *wanxinwanxin/amm-gym-auto-research*) ;;
    *)
        echo "FAIL: origin url is '$url' (not amm-gym-auto-research)"
        exit 1
        ;;
esac
echo "ok: origin -> $url"
