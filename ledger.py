"""SQLite ledger of trades + the rationale behind each one."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import Settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    ticket      INTEGER,
    symbol      TEXT,
    side        TEXT,           -- BUY / SELL
    volume      REAL,
    entry       REAL,
    sl          REAL,
    tp          REAL,
    confirmation TEXT,          -- what confirmation you saw
    rejection_1m INTEGER,       -- 1 if a 1m rejection was present, else 0
    trend       TEXT,           -- 'with' / 'against'
    confidence  TEXT,           -- high / normal / low
    notes       TEXT,
    status      TEXT DEFAULT 'open',   -- open / closed
    pnl         REAL DEFAULT 0
);
"""


def _conn(s: Settings) -> sqlite3.Connection:
    os.makedirs(s.state_dir, exist_ok=True)
    c = sqlite3.connect(s.ledger_path)
    c.row_factory = sqlite3.Row
    return c


def init(s: Settings) -> None:
    with _conn(s) as c:
        c.executescript(_SCHEMA)


def add_trade(s: Settings, **kw: Any) -> int:
    init(s)
    fields = {
        "ts": kw.get("ts") or datetime.now().isoformat(timespec="seconds"),
        "ticket": kw.get("ticket"),
        "symbol": (kw.get("symbol") or "").upper(),
        "side": (kw.get("side") or "").upper(),
        "volume": kw.get("volume"),
        "entry": kw.get("entry"),
        "sl": kw.get("sl"),
        "tp": kw.get("tp"),
        "confirmation": kw.get("confirmation"),
        "rejection_1m": 1 if kw.get("rejection_1m") else 0,
        "trend": kw.get("trend"),
        "confidence": kw.get("confidence") or "normal",
        "notes": kw.get("notes"),
        "status": kw.get("status") or "open",
        "pnl": kw.get("pnl") or 0,
    }
    cols = ",".join(fields)
    ph = ",".join("?" for _ in fields)
    with _conn(s) as c:
        cur = c.execute(f"INSERT INTO trades ({cols}) VALUES ({ph})", tuple(fields.values()))
        return cur.lastrowid


def close_trade(s: Settings, ticket: int, pnl: float) -> int:
    with _conn(s) as c:
        cur = c.execute(
            "UPDATE trades SET status='closed', pnl=? WHERE ticket=? AND status='open'",
            (pnl, ticket))
        return cur.rowcount


def list_trades(s: Settings, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
    init(s)
    q = "SELECT * FROM trades"
    args: list = []
    if status:
        q += " WHERE status=?"
        args.append(status)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    with _conn(s) as c:
        return [dict(r) for r in c.execute(q, args).fetchall()]


def summary(s: Settings) -> Dict[str, Any]:
    init(s)
    with _conn(s) as c:
        row = c.execute(
            "SELECT COUNT(*) n, "
            "SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) closed, "
            "SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) open, "
            "SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END) wins, "
            "SUM(CASE WHEN pnl<0 THEN 1 ELSE 0 END) losses, "
            "COALESCE(SUM(pnl),0) realized FROM trades").fetchone()
    return {
        "total": row["n"] or 0, "open": row["open"] or 0, "closed": row["closed"] or 0,
        "wins": row["wins"] or 0, "losses": row["losses"] or 0,
        "realized_pnl": round(row["realized"] or 0, 2),
    }
