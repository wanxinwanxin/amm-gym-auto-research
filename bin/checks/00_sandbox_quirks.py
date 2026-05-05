#!/usr/bin/env python3
"""
Operational handbook (cycle 26+) — collapsed sandbox-quirks check.

Replaces former checks 04_no_outbound_dns.sh (cycle 4) and
05_results_dir_unlink_blocked.py (cycle 8). Both encoded the same
class of fact: this sandbox has restricted POSIX/network capabilities
that drivers must work around. Rather than carry one check per quirk
forever, cycle 26 collapses them into one combined check (still
runnable, still falsifiable on each individual sub-quirk).

Sub-checks:
  (A) DNS to github.com is unresolvable. The cycle protocol skips
      `git pull --ff-only origin main` because of this; commits are
      pushed by host-side tooling. Pass = unresolvable. Flip = lift
      the no-pull workaround.
  (B) Files created in research/experiments/.../results/ cannot be
      unlinked by their creator. Drivers therefore truncate progress
      logs via `open("w")` instead of `Path.unlink()`. Pass = unlink
      raises. Flip = drivers can use Path.unlink() again.

Falsification rule: this script exits nonzero if EITHER quirk has
flipped. The error message identifies which one. The cycle 26 LOG
notes the consolidation; ifsea  retire-and-replace (rather than rewrite-
in-place) was chosen because both pieces of state still pass and
combining them is purely organizational, not behavioural.
"""
from __future__ import annotations

import os
import socket
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check_dns_unresolvable() -> tuple[bool, str]:
    try:
        socket.gethostbyname("github.com")
    except socket.gaierror:
        return True, "github.com unresolvable (sandbox push blocker still active)"
    except Exception as exc:  # noqa: BLE001
        # Anything other than a clean resolution counts as still-blocked.
        return True, f"github.com unresolved ({exc.__class__.__name__})"
    return False, "github.com NOW RESOLVES — DNS restriction lifted; consider re-enabling git pull"


def check_unlink_blocked() -> tuple[bool, str]:
    target_dir = ROOT / "research" / "experiments" / ".checks_tmp"
    target_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=target_dir)
    os.write(fd, b"hello\n")
    os.close(fd)
    try:
        Path(tmp_path).unlink()
    except PermissionError:
        try:
            target_dir.rmdir()
        except OSError:
            pass
        return True, "PermissionError on unlink (workaround still needed)"
    except OSError as exc:
        return True, f"OSError on unlink ({exc.__class__.__name__}: {exc})"
    # Unlink succeeded — workaround obsolete.
    try:
        target_dir.rmdir()
    except OSError:
        pass
    return False, "unlink SUCCEEDED — sandbox restriction lifted; drivers can use Path.unlink"


def main() -> int:
    failures: list[str] = []
    msgs: list[str] = []

    ok, msg = check_dns_unresolvable()
    msgs.append(f"  (A) DNS:    {msg}")
    if not ok:
        failures.append(f"DNS quirk flipped: {msg}")

    ok, msg = check_unlink_blocked()
    msgs.append(f"  (B) unlink: {msg}")
    if not ok:
        failures.append(f"unlink quirk flipped: {msg}")

    if failures:
        print("FAIL: " + "; ".join(failures))
        for line in msgs:
            print(line)
        return 1

    # All sub-quirks still hold — the consolidated workaround stack is
    # still required.
    print("ok: sandbox quirks (DNS+unlink) both still hold")
    for line in msgs:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
