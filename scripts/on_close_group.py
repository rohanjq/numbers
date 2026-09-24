#!/usr/bin/env python3
"""Call this BEFORE closing positions: queries MT5 for open positions of symbol+side
and writes a grouped CLOSED row to ledger.csv. If positions are already closed,
accept --manual flags to enter values manually."""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings
from mt5_bridge import Bridge


def get_wallet_snapshot(s: Settings) -> float:
    try:
        import json
        state_path = os.path.join(s.state_dir, "state.json")
        if os.path.exists(state_path):
            with open(state_path) as f:
                state = json.load(f)
                return state.get("wallet", s.start_capital)
    except Exception:
        pass
    return s.start_capital


def group_and_log_close(
    symbol: str,
    side: str,
    rationale: str = "",
    followed_from: str = "",
    manual_pnl: float | None = None,
    manual_avg_entry: float | None = None,
    manual_vol: float | None = None,
    manual_tickets: str = "",
) -> None:
    s = Settings.load()
    bridge = Bridge(s)

    ok, msg = bridge.connect()
    if not ok:
        print(f"[ERROR] {msg}")
        sys.exit(1)

    acct = bridge.account()
    wallet_snapshot = get_wallet_snapshot(s)
    equity_at_entry = acct.equity  # snapshot before close

    sym = symbol.upper()
    sd = side.upper()

    # --- Try to find open positions matching this symbol+side ---
    positions = bridge.positions(sym)
    if not positions:
        for suffix in ("p", "r", "m", ".pro", ".raw"):
            alt = sym + suffix
            positions = bridge.positions(alt)
            if positions:
                print(f"💡 No positions for {sym}, found {len(positions)} under {alt}")
                break
    if not positions:
        positions = bridge.positions()

    matched = []
    for p in positions:
        psym = p.symbol.upper()
        # match any variant of the symbol (XAUUSDp, XAUUSD, BTCUSDT, etc.)
        if psym.startswith(sym) or sym.startswith(psym):
            pside = "BUY" if p.type == bridge.mt5.ORDER_TYPE_BUY else "SELL"
            if pside == sd:
                matched.append(p)

    if matched:
        vol = sum(p.volume for p in matched)
        avg_entry = sum(p.price_open * p.volume for p in matched) / vol if vol else 0
        pnl = sum(p.profit for p in matched)
        tickets = ",".join(str(p.ticket) for p in matched)
    else:
        if manual_pnl is not None:
            pnl = manual_pnl
            avg_entry = manual_avg_entry or 0
            vol = manual_vol or 0
            tickets = manual_tickets
            print(f"⚠️  No open positions found for {sym} {sd} — using manual values")
        else:
            print(f"❌ No open positions found for {sym} {sd}.")
            print(f"   Use --pnl <value> --avg-entry <value> --vol <value> --tickets <ticket_ids> to log manually.")
            bridge.disconnect()
            sys.exit(1)

    csv_path = os.path.join(s.project_root, "ledger.csv")

    # Ensure CSV exists with headers
    fieldnames = [
        "symbol", "side", "num_trades", "open_time", "first_trade",
        "avg_entry_price", "current_price", "avg_xir_price", "total_volume",
        "pnl", "risk_reward_ratio", "wallet_at_entry", "total_capital",
        "status", "rationale", "followed_from", "ticket_ids"
    ]
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    # Read existing rows
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r]

    # Remove any open rows for this symbol+side
    sym_variants = [sym, sym + "p", sym + "P"]
    rows = [r for r in rows if not (
        r.get("symbol", "").upper() in {v.upper() for v in sym_variants}
        and r.get("side", "").upper() == sd
    )]

    # Risk:reward
    rr = round(pnl / equity_at_entry, 4) if equity_at_entry > 0 else 0

    closed_row = {
        "symbol": sym,
        "side": sd,
        "num_trades": str(len(matched)) if matched else "?",
        "open_time": datetime.now().isoformat(timespec="seconds"),
        "first_trade": datetime.now().isoformat(timespec="seconds"),
        "avg_entry_price": str(round(avg_entry, 2)),
        "current_price": "",       # closed trade — no current price
        "avg_xir_price": str(round(avg_entry, 2)),
        "total_volume": str(round(vol, 4)),
        "pnl": str(round(pnl, 2)),
        "risk_reward_ratio": str(rr),
        "wallet_at_entry": str(round(wallet_snapshot, 2)),
        "total_capital": str(round(wallet_snapshot + acct.equity, 2)),
        "status": "CLOSED",
        "rationale": rationale,
        "followed_from": followed_from,
        "ticket_ids": tickets,
    }
    rows.append(closed_row)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Logged CLOSED: {sym} {sd}")
    print(f"   Positions: {len(matched)} | Volume: {round(vol,4)} | Avg Entry: {round(avg_entry,2)} | P/L: ${round(pnl,2)} | R:R: {rr}")
    print(f"   Wallet: ${wallet_snapshot:.2f} | MT5: ${acct.equity:.2f}")
    print(f"   CSV: {csv_path}")

    bridge.disconnect()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Log a closed position group to ledger.csv")
    ap.add_argument("symbol", nargs="?", default=None)
    ap.add_argument("side", nargs="?", default=None)
    ap.add_argument("rationale", nargs="?", default="")
    ap.add_argument("followed_from", nargs="?", default="")
    ap.add_argument("--pnl", type=float, default=None, help="Manual P/L (for already-closed trades)")
    ap.add_argument("--avg-entry", type=float, default=None, help="Manual avg entry price")
    ap.add_argument("--vol", type=float, default=None, help="Manual total volume")
    ap.add_argument("--tickets", type=str, default="", help="Manual ticket IDs (comma-separated)")
    args = ap.parse_args()

    if not args.symbol or not args.side:
        print("Usage: on_close_group.py <SYMBOL> <BUY|SELL> [rationale] [followed_from] [--pnl X --avg-entry X --vol X --tickets IDs]")
        print("Examples:")
        print("  on_close_group.py XAUUSD BUY 'hit TP at 4125' 'my_signal'")
        print("  on_close_group.py BTCUSDT SELL --pnl 89.0 --avg-entry 62070 --vol 0.78 --tickets 48701162,48701169,... 'SL hit at 62180' 'my_signal'")
        sys.exit(1)

    group_and_log_close(
        args.symbol,
        args.side,
        args.rationale,
        args.followed_from,
        manual_pnl=args.pnl,
        manual_avg_entry=args.avg_entry,
        manual_vol=args.vol,
        manual_tickets=args.tickets,
    )