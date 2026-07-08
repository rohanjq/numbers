#!/usr/bin/env python3
"""set_sl.py — set the stop loss (and optionally TP) on ALL open positions of a symbol.

Examples:
    python scripts/set_sl.py --symbol XAUUSD --sl 2345.0
    python scripts/set_sl.py --symbol BTCUSD --sl 67000 --tp 69000
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings          # noqa: E402
from mt5_bridge import Bridge        # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--sl", type=float, required=True)
    ap.add_argument("--tp", type=float, default=None)
    args = ap.parse_args()

    s = Settings.load()
    br = Bridge(s)
    ok, msg = br.connect()
    print(("[MOCK] " if br.is_mock else "[LIVE] ") + msg)
    if not ok:
        return 1

    positions = br.positions(args.symbol.upper())
    if not positions:
        print(f"No open positions for {args.symbol.upper()}.")
        return 0

    for p in positions:
        done, note = br.set_sl(p, args.sl, args.tp)
        print(("OK  " if done else "ERR ") + note)

    br.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
