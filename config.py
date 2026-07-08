"""Configuration for the Numbers discipline agent."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()

_ROOT = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(_ROOT, "state")
LEDGER_PATH = os.path.join(STATE_DIR, "ledger.db")
STATE_PATH = os.path.join(STATE_DIR, "state.json")


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _f(name: str, default: float) -> float:
    try:
        return float(_get(name) or default)
    except ValueError:
        return default


def _i(name: str, default: int) -> int:
    try:
        return int(float(_get(name) or default))
    except ValueError:
        return default


@dataclass
class Settings:
    mt5_host: str = "localhost"
    mt5_port: int = 8001
    symbols: List[str] = field(default_factory=lambda: ["XAUUSD", "BTCUSD"])

    start_capital: float = 1000.0
    target_capital: float = 40000.0
    working_days: int = 13
    start_date: str = ""

    exposure_min_pct: float = 5.0
    exposure_max_pct: float = 7.5

    pushover_token: str = ""
    pushover_user: str = ""

    state_dir: str = STATE_DIR
    ledger_path: str = LEDGER_PATH
    state_path: str = STATE_PATH

    @classmethod
    def load(cls) -> "Settings":
        syms = [s.strip().upper() for s in _get("SYMBOLS", "XAUUSD,BTCUSD").split(",") if s.strip()]
        os.makedirs(STATE_DIR, exist_ok=True)
        return cls(
            mt5_host=_get("MT5_HOST", "localhost"),
            mt5_port=_i("MT5_PORT", 8001),
            symbols=syms or ["XAUUSD"],
            start_capital=_f("START_CAPITAL", 1000.0),
            target_capital=_f("TARGET_CAPITAL", 40000.0),
            working_days=_i("WORKING_DAYS", 13),
            start_date=_get("START_DATE"),
            exposure_min_pct=_f("EXPOSURE_MIN_PCT", 5.0),
            exposure_max_pct=_f("EXPOSURE_MAX_PCT", 7.5),
            pushover_token=_get("PUSHOVER_TOKEN"),
            pushover_user=_get("PUSHOVER_USER"),
        )
