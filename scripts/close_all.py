#!/usr/bin/env python3
"""close_all.py — close ALL open positions of a symbol (records P/L to the ledger).

Example:
    python scripts/close_all.py --symbol XAUUSD
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings          # noqa: E402
from mt5_bridge import Bridge        # noqa: E402
import ledger                        # noqa: E402
import riskreward                    # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--yes", action="store_true", help="skip confirmation")
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

    if not args.yes:
        ans = input(f"Close {len(positions)} {args.symbol.upper()} position(s)? [y/N] ")
        if ans.strip().lower() != "y":
            print("Aborted.")
            return 0

    for p in positions:
        profit = getattr(p, "profit", 0.0)
        tick = br.tick(p.symbol)
        exit_price = tick.bid if p.type == br.mt5.ORDER_TYPE_BUY else tick.ask

        logged = ledger.get_open_trade(s, p.ticket)
        equity_at_trade = logged.get("equity_at_trade") if logged else None
        if equity_at_trade:
            rr = riskreward.risk_reward_vs_equity(profit, equity_at_trade)
        else:
            rr = riskreward.risk_reward(p.symbol, p.volume, p.price_open, profit)

        done, note = br.close(p)
        print(("OK  " if done else "ERR ") + f"{note} (P/L ${profit:+.2f}, R:R {rr:+.2f})")
        if done:
            ledger.close_trade(s, p.ticket, profit, risk_reward=rr, exit_price=exit_price)

    br.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
