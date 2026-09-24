#!/usr/bin/env python3
"""Update CSV ledger from MT5 closed trades (grouped by symbol+side), plus current open positions."""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings
from mt5_bridge import Bridge


def get_wallet_at_time(s: Settings) -> float:
    """Get wallet balance (outer capital, not MT5 equity)."""
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


def get_closed_trades_from_api(bridge: Bridge, s: Settings) -> List[Dict]:
    """Query MT5 API for closed trades (history)."""
    rows = []
    try:
        # MT5's deal_get returns closed trades / deal history
        from mt5linux import DEAL_REASON_EXPERT  # May not exist, use fallback
    except Exception:
        pass

    # Fallback: query all deals from bridge (if available)
    # Note: mt5linux may not expose history easily; we'll use what's available
    # For now, return empty — user can manually enter closed trades or extend this
    return rows


def get_open_trades_from_api(bridge: Bridge, s: Settings) -> List[Dict]:
    """Query MT5 API for currently open positions, grouped by symbol+side."""
    rows = []
    wallet = get_wallet_at_time(s)
    acct = bridge.account()
    total_capital = wallet + acct.equity

    # Get position averages (grouped by symbol+side)
    averages = bridge.position_averages()

    for key, data in averages.items():
        # Current price from tick
        try:
            tick = bridge.tick(data["symbol"])
            current_price = tick.last
        except Exception:
            current_price = data["avg_entry"]

        rows.append({
            "symbol": data["symbol"],
            "side": data["side"],
            "num_trades": data["positions"],
            "open_time": datetime.now().isoformat(timespec="seconds"),
            "first_trade": datetime.now().isoformat(timespec="seconds"),
            "avg_entry_price": round(data["avg_entry"], 2),
            "current_price": round(current_price, 2),
            "avg_xir_price": round(data["avg_entry"], 2),
            "total_volume": round(data["total_volume"], 4),
            "pnl": round(data["pnl"], 2),
            "risk_reward_ratio": round(data["pnl"] / acct.equity if acct.equity > 0 else 0, 4),
            "wallet_at_entry": round(wallet, 2),
            "total_capital": round(total_capital, 2),
            "status": "OPEN",
            "rationale": "",  # User fills manually
            "followed_from": "",  # User fills (e.g., "my_signal", "TradingView", "tip: @Bob")
            "ticket_ids": ",".join(str(t) for t in data["tickets"]),
        })

    return rows


def update_ledger(output_csv: str = "ledger.csv") -> None:
    """Sync CSV ledger: merge closed trades from history + current open positions."""
    s = Settings()
    bridge = Bridge(s)

    ok, msg = bridge.connect()
    if not ok:
        print(f"[ERROR] {msg}")
        sys.exit(1)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    # Load existing CSV (preserve closed trades + manual edits)
    csv_path = os.path.join(s.project_root, output_csv)
    existing_rows = {}
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get("status") == "CLOSED" and row.get("symbol") and row.get("side"):
                    key = (row.get("symbol"), row.get("side"))
                    existing_rows[key] = row

    # Get current open positions
    open_rows = get_open_trades_from_api(bridge, s)

    # Get closed trades from history (if available)
    closed_rows = get_closed_trades_from_api(bridge, s)

    # Merge: keep existing closed trades + add any new ones + refresh open positions
    all_rows = list(existing_rows.values()) + closed_rows + open_rows
    # Remove any None keys that may have crept in from CSV reads
    all_rows = [{k: v for k, v in row.items() if k is not None} for row in all_rows]

    # Write CSV
    fieldnames = [
        "symbol", "side", "num_trades", "open_time", "first_trade",
        "avg_entry_price", "current_price", "avg_xir_price", "total_volume",
        "pnl", "risk_reward_ratio", "wallet_at_entry", "total_capital",
        "status", "rationale", "followed_from", "ticket_ids"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    acct = bridge.account()
    wallet = get_wallet_at_time(s)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Exported {len(all_rows)} trades (open+closed) to {csv_path}")
    print(f"  Open: {len(open_rows)} | Closed: {len(closed_rows)} | Wallet: ${wallet:.2f} | MT5: ${acct.equity:.2f}")

    bridge.disconnect()


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "ledger.csv"
    update_ledger(csv_file)
