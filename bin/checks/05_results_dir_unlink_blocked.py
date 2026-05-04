#!/usr/bin/env python3
"""
Operational fact (cycle 8): the sandbox cannot unlink files that were
created in `research/experiments/.../results/` by an earlier process.
Drivers therefore truncate progress logs via `open("w")` instead of
`Path.unlink()`. This check writes a temp file and tries to unlink it.
- Pass: unlink raises (workaround still needed).
- Fail (retire): unlink succeeds (we can use Path.unlink again).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
target_dir = ROOT / "research" / "experiments" / ".checks_tmp"
target_dir.mkdir(parents=True, exist_ok=True)
fd, tmp_path = tempfile.mkstemp(dir=target_dir)
os.write(fd, b"hello\n")
os.close(fd)
try:
    Path(tmp_path).unlink()
except PermissionError:
    print("ok: PermissionError on unlink (workaround still needed)")
    # Try to clean directory if empty.
    try:
        target_dir.rmdir()
    except OSError:
        pass
    sys.exit(0)
except OSError as exc:
    print(f"ok: OSError on unlink ({exc.__class__.__name__}: {exc})")
    sys.exit(0)
print("FAIL: unlink succeeded — sandbox restriction lifted? retire this check.")
try:
    target_dir.rmdir()
except OSError:
    pass
sys.exit(1)
