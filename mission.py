"""Mission math + persistent state so restarts pick up where we left off.

Everything is anchored to TOTAL capital (wallet + MT5), not the MT5 balance.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Optional

from config import Settings


# ---------------------------------------------------------------- mission math
def daily_multiple(start: float, target: float, days: int) -> float:
    """Required per-working-day growth multiple, e.g. 40x over 13 days ~= 1.328."""
    if start <= 0 or target <= 0 or days <= 0:
        return 1.0
    return (target / start) ** (1.0 / days)


def working_days_between(start_iso: str, today: Optional[date] = None) -> int:
    """1-based index of today counting only Mon-Fri from START_DATE (inclusive)."""
    if not start_iso:
        return 1
    try:
        start = datetime.strptime(start_iso, "%Y-%m-%d").date()
    except ValueError:
        return 1
    today = today or date.today()
    if today < start:
        return 0
    n = 0
    d = start
    while d <= today:
        if d.weekday() < 5:  # Mon-Fri
            n += 1
        d += timedelta(days=1)
    return n


def target_capital_for_day(start: float, mult: float, day_index: int) -> float:
    """Capital you should hold by the END of working day `day_index`."""
    if day_index <= 0:
        return start
    return round(start * (mult ** day_index), 2)


# ---------------------------------------------------------------- persistence
def _default_state(s: Settings) -> dict:
    return {
        "start_date": s.start_date,
        "start_capital": s.start_capital,
        "current_capital": s.start_capital,
        "target_capital": s.target_capital,
        "working_days": s.working_days,
        "updated": datetime.now().isoformat(timespec="seconds"),
        "notes": [],
    }


def load_state(s: Settings) -> dict:
    os.makedirs(s.state_dir, exist_ok=True)
    if os.path.exists(s.state_path):
        try:
            with open(s.state_path) as fh:
                return json.load(fh)
        except Exception:
            pass
    st = _default_state(s)
    save_state(s, st)
    return st


def save_state(s: Settings, st: dict) -> None:
    st["updated"] = datetime.now().isoformat(timespec="seconds")
    os.makedirs(s.state_dir, exist_ok=True)
    tmp = s.state_path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(st, fh, indent=2)
    os.replace(tmp, s.state_path)


def set_current_capital(s: Settings, amount: float) -> dict:
    st = load_state(s)
    st["current_capital"] = round(float(amount), 2)
    save_state(s, st)
    return st


def mission_snapshot(s: Settings) -> dict:
    """Everything the agent needs to keep you on track today."""
    st = load_state(s)
    mult = daily_multiple(st["start_capital"], st["target_capital"], st["working_days"])
    day = working_days_between(st.get("start_date") or s.start_date)
    day = max(1, min(day, st["working_days"]))
    goal_today = target_capital_for_day(st["start_capital"], mult, day)
    goal_yesterday = target_capital_for_day(st["start_capital"], mult, day - 1)
    current = st["current_capital"]
    on_track = current >= goal_yesterday
    return {
        "day_index": day,
        "working_days": st["working_days"],
        "daily_multiple": round(mult, 4),
        "start_capital": st["start_capital"],
        "current_capital": current,
        "target_capital": st["target_capital"],
        "goal_by_end_of_today": goal_today,
        "goal_by_end_of_yesterday": goal_yesterday,
        "needed_gain_today": round(goal_today - current, 2),
        "on_track": on_track,
    }
