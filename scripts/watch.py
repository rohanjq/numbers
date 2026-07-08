#!/usr/bin/env python3
"""watch.py — run the status check on a loop every 1-2 minutes.

Usage:
    python scripts/watch.py [--interval 90] [--notify]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=90, help="seconds between checks")
    ap.add_argument("--notify", action="store_true")
    args = ap.parse_args()

    check = os.path.join(_HERE, "check_status.py")
    cmd = [sys.executable, check]
    if args.notify:
        cmd.append("--notify")

    print(f"Watching every {args.interval}s. Ctrl-C to stop.")
    try:
        while True:
            print("\n" + "=" * 60)
            subprocess.run(cmd, check=False)
            time.sleep(max(30, args.interval))
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
