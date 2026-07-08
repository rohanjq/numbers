#!/usr/bin/env python3
"""check_status.py — one-shot health check the agent runs every 1-2 minutes.

Reconciles the MT5 bridge against the mission and exposure policy, prints a
compact status, and (optionally) sends a Pushover alert when exposure is over
the cap or you have drifted off track.

Usage:
    python scripts/check_status.py [--notify] [--capital 1000]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings          # noqa: E402
from mt5_bridge import Bridge        # noqa: E402
import exposure                      # noqa: E402
import mission                       # noqa: E402
import notify                        # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--notify", action="store_true", help="send Pushover on problems")
    ap.add_argument("--capital", type=float, default=None,
                    help="override TOTAL capital (wallet + MT5) for this check")
    args = ap.parse_args()

    s = Settings.load()
    if args.capital is not None:
        mission.set_current_capital(s, args.capital)

    br = Bridge(s)
    ok, msg = br.connect()
    print(("[MOCK] " if br.is_mock else "[LIVE] ") + msg)
    if not ok:
        return 1

    acc = br.account()
    snap = mission.mission_snapshot(s)
    exp = exposure.evaluate(acc.equity, snap["current_capital"], s)
    pnl = br.running_pnl()
    positions = br.positions()

    print("\n== MISSION ==")
    print(f"Day {snap['day_index']}/{snap['working_days']}  "
          f"(x{snap['daily_multiple']} per day)")
    print(f"Total capital: ${snap['current_capital']}  "
          f"Goal by tonight: ${snap['goal_by_end_of_today']}  "
          f"Need +${snap['needed_gain_today']}")
    print(f"On track: {'YES' if snap['on_track'] else 'NO — catch up'}")

    print("\n== MT5 ==")
    print(f"Balance ${acc.balance:.2f}  Equity ${acc.equity:.2f}  "
          f"Open positions {len(positions)}  Running P/L ${pnl:+.2f}")

    print("\n== EXPOSURE ==")
    print(f"[{exp['status']}] {exp['message']}")

    problem = exp["status"] == "OVER" or not snap["on_track"]
    if args.notify and problem:
        parts = []
        if exp["status"] == "OVER":
            parts.append("NOT IN CONTROL: " + exp["message"])
        if not snap["on_track"]:
            parts.append(f"Behind schedule: need ${snap['goal_by_end_of_today']} tonight.")
        parts.append("This is life-changing. Take control.")
        sent, note = notify.send(s, " ".join(parts),
                                 title="Numbers — take control",
                                 priority=1 if exp["status"] == "OVER" else 0)
        print(f"\nPushover: {note}")

    br.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
