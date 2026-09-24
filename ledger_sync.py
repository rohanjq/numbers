"""Sync SQLite ledger to CSV, grouped by position (symbol+side), with live P/L."""
from __future__ import annotations

import csv
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import Settings
from ledger import _conn, init as ledger_init
from mt5_bridge import Bridge
from riskreward import LEVERAGE


def get_open_positions(s: Settings) -> Dict[tuple, Dict]:
    """Group open trades by (symbol, side) -> aggregated position data."""
    ledger_init(s)
    bridge = Bridge(s)

    with _conn(s) as c:
        # Get all open trades grouped by symbol+side
        rows = c.execute("""
            SELECT symbol, side,
                   GROUP_CONCAT(id) as trade_ids,
                   COUNT(*) as num_trades,
                   MIN(ts) as first_ts,
                   AVG(entry) as avg_entry,
                   SUM(volume) as total_volume,
                   SUM(pnl) as realized_pnl,
                   MAX(equity_at_trade) as equity_at_trade
            FROM trades
            WHERE status='open'
            GROUP BY symbol, side
            ORDER BY first_ts
        """).fetchall()

    positions = {}
    for row in rows:
        key = (row["symbol"], row["side"])

        # Fetch live position from MT5 for unrealized P/L
        try:
            live_pos = bridge.positions(row["symbol"], row["side"])
            if live_pos:
                live_pnl = live_pos.get("pnl", 0)
                current_price = live_pos.get("price", row["avg_entry"])
            else:
                live_pnl = 0
                current_price = row["avg_entry"]
        except Exception:
            live_pnl = 0
            current_price = row["avg_entry"]

        # Calculate risk:reward
        equity_at_entry = row["equity_at_trade"] or 1.0
        rr = (row["realized_pnl"] + live_pnl) / equity_at_entry if equity_at_entry else 0

        positions[key] = {
            "symbol": row["symbol"],
            "side": row["side"],
            "num_trades": row["num_trades"],
            "first_ts": row["first_ts"],
            "avg_entry": round(row["avg_entry"], 2) if row["avg_entry"] else 0,
            "total_volume": round(row["total_volume"], 4) if row["total_volume"] else 0,
            "current_price": round(current_price, 2),
            "realized_pnl": round(row["realized_pnl"], 2) if row["realized_pnl"] else 0,
            "unrealized_pnl": round(live_pnl, 2),
            "total_pnl": round((row["realized_pnl"] or 0) + live_pnl, 2),
            "risk_reward": round(rr, 4),
            "equity_at_entry": round(equity_at_entry, 2),
            "rationale": "",  # Will be filled from notes of first trade
            "trade_ids": row["trade_ids"],
        }

    # Fetch rationale from first trade in each position
    with _conn(s) as c:
        for key, pos in positions.items():
            trade_ids = pos["trade_ids"].split(",")
            first_id = int(trade_ids[0])
            trade = c.execute(
                "SELECT confirmation, rejection_1m, trend, confidence, notes, entry, exit_price "
                "FROM trades WHERE id=?", (first_id,)
            ).fetchone()
            if trade:
                rej = "Yes" if trade["rejection_1m"] else "No"
                pos["rationale"] = (
                    f"Conf:{trade['confirmation']} | 1mRej:{rej} | Trend:{trade['trend']} | "
                    f"Conf:{trade['confidence']} | {trade['notes'] or ''}"
                )

    return positions


def export_csv(s: Settings, output_csv: str = "ledger.csv") -> str:
    """Export open positions to CSV, auto-updated with live P/L."""
    positions = get_open_positions(s)

    csv_path = os.path.join(s.project_root, output_csv)

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "symbol", "side", "num_trades", "first_ts", "avg_entry", "current_price",
            "total_volume", "realized_pnl", "unrealized_pnl", "total_pnl",
            "risk_reward", "equity_at_entry", "rationale", "trade_ids"
        ])
        writer.writeheader()
        for pos in positions.values():
            writer.writerow(pos)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Exported {len(positions)} open positions to {csv_path}")
    return csv_path


if __name__ == "__main__":
    import sys
    s = Settings()
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "ledger.csv"
    export_csv(s, csv_file)
