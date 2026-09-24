#!/usr/bin/env python3
"""log_trade.py — record a trade + the rationale behind it into the SQLite ledger.

The agent should ask these BEFORE/at entry: what confirmation did you see, was
there at least a 1m rejection, is this with or against the trend, confidence?

This account trades with NO stop loss, so there's no stop-distance to size
risk from. Instead we snapshot the live MT5 equity at entry (equity_at_trade)
and use that as the risk basis: R:R on close = pnl / equity_at_trade.

Example:
    python scripts/log_trade.py --ticket 70001 --symbol XAUUSD --side BUY \
        --volume 0.02 --entry 2348.5 --confirmation "1m rejection wick" \
        --rejection --trend with --confidence high --notes "London open"
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings          # noqa: E402
from mt5_bridge import Bridge        # noqa: E402
import ledger                        # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticket", type=int)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"])
    ap.add_argument("--volume", type=float)
    ap.add_argument("--entry", type=float)
    ap.add_argument("--sl", type=float)
    ap.add_argument("--tp", type=float)
    ap.add_argument("--confirmation", default="")
    ap.add_argument("--rejection", action="store_true",
                    help="a 1m rejection was present")
    ap.add_argument("--trend", choices=["with", "against"], default=None)
    ap.add_argument("--confidence", choices=["high", "normal", "low"], default="normal")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    s = Settings.load()

    equity_at_trade = None
    br = Bridge(s)
    ok, _ = br.connect()
    if ok:
        try:
            equity_at_trade = round(br.account().equity, 2)
        except Exception:
            pass
        br.disconnect()

    rid = ledger.add_trade(
        s, ticket=args.ticket, symbol=args.symbol, side=args.side,
        volume=args.volume, entry=args.entry, sl=args.sl, tp=args.tp,
        confirmation=args.confirmation, rejection_1m=args.rejection,
        trend=args.trend, confidence=args.confidence, notes=args.notes,
        equity_at_trade=equity_at_trade,
    )
    eq_note = f" (equity at entry: ${equity_at_trade:.2f})" if equity_at_trade else ""
    print(f"Logged trade #{rid} ({args.symbol.upper()} {args.side.upper()}){eq_note}.")
    print("Ledger summary:", ledger.summary(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
