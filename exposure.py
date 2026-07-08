"""Exposure policy: the MT5 account must hold 5%-7.5% of TOTAL capital."""
from __future__ import annotations

from config import Settings


def evaluate(mt5_equity: float, total_capital: float, s: Settings) -> dict:
    """Return exposure status vs the 5%/7.5% policy.

    Bands:
      pct <= min      -> OK
      min < pct <= max -> ELEVATED (ask: was this a high-confidence trade?)
      pct > max        -> OVER (you are NOT in control — reduce now)
    """
    total = total_capital or s.start_capital
    min_amt = round(total * s.exposure_min_pct / 100.0, 2)
    max_amt = round(total * s.exposure_max_pct / 100.0, 2)
    pct = round((mt5_equity / total) * 100.0, 2) if total else 0.0

    if mt5_equity <= min_amt:
        status = "OK"
        msg = (f"Exposure {pct}% (${mt5_equity:.2f}) within the {s.exposure_min_pct}% "
               f"target (${min_amt}). In control.")
    elif mt5_equity <= max_amt:
        status = "ELEVATED"
        msg = (f"Exposure {pct}% (${mt5_equity:.2f}) is ABOVE the {s.exposure_min_pct}% "
               f"target and up to the {s.exposure_max_pct}% cap (${max_amt}). "
               f"Was this a HIGH-CONFIDENCE trade? If not, trim back to ${min_amt}.")
    else:
        status = "OVER"
        msg = (f"Exposure {pct}% (${mt5_equity:.2f}) EXCEEDS the {s.exposure_max_pct}% cap "
               f"(${max_amt}). You are NOT in control — pull ${round(mt5_equity - max_amt, 2)} "
               f"out or reduce size now. This is life-changing; protect it.")
    return {
        "status": status, "message": msg, "pct": pct,
        "mt5_equity": round(mt5_equity, 2), "total_capital": round(total, 2),
        "min_amount": min_amt, "max_amount": max_amt,
    }
