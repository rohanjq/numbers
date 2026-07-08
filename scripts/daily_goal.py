#!/usr/bin/env python3
"""daily_goal.py — today's target on the 1000 -> 40000 in 13 days path.

Usage:
    python scripts/daily_goal.py [--capital 1000]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings          # noqa: E402
import mission                       # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capital", type=float, default=None,
                    help="set your current TOTAL capital (wallet + MT5)")
    args = ap.parse_args()

    s = Settings.load()
    if args.capital is not None:
        mission.set_current_capital(s, args.capital)

    snap = mission.mission_snapshot(s)
    mult = snap["daily_multiple"]
    print(f"Mission: ${snap['start_capital']:.0f} -> ${snap['target_capital']:.0f} "
          f"in {snap['working_days']} working days  (x{mult} per day)")
    print(f"Today is day {snap['day_index']}/{snap['working_days']}.")
    print(f"Current capital: ${snap['current_capital']:.2f}")
    print(f"Goal by end of today: ${snap['goal_by_end_of_today']:.2f} "
          f"(need +${snap['needed_gain_today']:.2f})")
    print("On track." if snap["on_track"]
          else "Behind — prioritise catching up, but stay disciplined.")

    print("\nFull ladder:")
    for d in range(1, snap["working_days"] + 1):
        tgt = mission.target_capital_for_day(snap["start_capital"], mult, d)
        mark = "  <-- today" if d == snap["day_index"] else ""
        print(f"  Day {d:>2}: ${tgt:,.2f}{mark}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
