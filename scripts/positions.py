#!/usr/bin/env python3
"""positions.py — show open positions, running P/L, and position averages.

Usage:
    python scripts/positions.py [--symbol XAUUSD]
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
    ap.add_argument("--symbol", default=None)
    args = ap.parse_args()

    s = Settings.load()
    br = Bridge(s)
    ok, msg = br.connect()
    print(("[MOCK] " if br.is_mock else "[LIVE] ") + msg)
    if not ok:
        return 1

    positions = br.positions(args.symbol)
    if not positions:
        print("No open positions.")
        return 0

    print(f"\n{'TICKET':>8} {'SYMBOL':<8} {'SIDE':<4} {'VOL':>6} "
          f"{'ENTRY':>10} {'SL':>10} {'TP':>10} {'P/L':>9}")
    for p in positions:
        side = "BUY" if p.type == br.mt5.ORDER_TYPE_BUY else "SELL"
        print(f"{p.ticket:>8} {p.symbol:<8} {side:<4} {p.volume:>6} "
              f"{p.price_open:>10} {p.sl:>10} {p.tp:>10} {p.profit:>9.2f}")

    print("\n== POSITION AVERAGES ==")
    for key, a in br.position_averages(args.symbol).items():
        print(f"{key}: {a['positions']} pos, vol {a['total_volume']}, "
              f"avg entry {a['avg_entry']}, P/L ${a['pnl']:+.2f}")

    print(f"\nTotal running P/L: ${br.running_pnl(args.symbol):+.2f}")
    br.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
