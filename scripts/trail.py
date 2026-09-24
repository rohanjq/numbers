#!/usr/bin/env python3
"""Trailing stop TUI — auto-update SL based on profit movement in USD, with pause/resume + manual SL."""
from __future__ import annotations

import curses
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings
from mt5_bridge import Bridge


class TrailUI:
    def __init__(self, trail_step: float = 2.0):
        """
        trail_step: How many USD to trail. E.g., 2 means SL moves up by 2 for each 2 USD profit.
        """
        self.trail_step = trail_step
        self.s = Settings()
        self.bridge = Bridge(self.s)
        self.running = True
        self.paused = False
        self.positions = {}
        self.current_sls = {}  # (symbol, side, ticket) -> current_sl_from_mt5
        self.fixed_sl = None  # If set, use this instead of trailing
        self.message = ""

    def connect(self) -> bool:
        ok, msg = self.bridge.connect()
        return ok

    def refresh_positions(self):
        """Fetch fresh positions from MT5."""
        positions_list = self.bridge.positions()
        self.positions = {}
        self.current_sls = {}

        for pos in positions_list:
            side = "BUY" if pos.type == self.bridge.mt5.ORDER_TYPE_BUY else "SELL"
            key = (pos.symbol, side, pos.ticket)
            self.positions[key] = pos
            self.current_sls[key] = pos.sl

    def get_position_averages(self) -> dict:
        """Group positions by symbol+side."""
        grouped = {}
        for (sym, side, ticket), pos in self.positions.items():
            key = (sym, side)
            if key not in grouped:
                grouped[key] = {
                    "symbol": sym,
                    "side": side,
                    "tickets": [],
                    "avg_entry": 0,
                    "total_vol": 0,
                    "pnl": 0,
                    "current_price": 0,
                    "avg_sl": 0,
                }

            g = grouped[key]
            g["tickets"].append(ticket)
            g["total_vol"] += pos.volume
            g["pnl"] += pos.profit
            g["avg_sl"] += self.current_sls[(sym, side, ticket)] * pos.volume

        # Calculate weighted averages
        for key, g in grouped.items():
            if g["total_vol"] > 0:
                g["avg_entry"] = sum(
                    p.price_open * p.volume for (s, side, _), p in self.positions.items() if (s, side) == key
                ) / g["total_vol"]
                g["avg_sl"] /= g["total_vol"]

            # Get current tick
            try:
                tick = self.bridge.tick(g["symbol"])
                g["current_price"] = tick.last if tick else g["avg_entry"]
            except Exception:
                g["current_price"] = g["avg_entry"]

        return grouped

    def calculate_trail_sl(self, side: str, pnl: float, avg_entry: float) -> float:
        """Calculate trailed SL based on current P/L."""
        if pnl <= 0:
            return 0  # No trail until profitable

        trail_levels = int(pnl / self.trail_step)
        if trail_levels == 0:
            return 0

        if side == "BUY":
            return round(avg_entry + (trail_levels * 0.01), 2)
        else:
            return round(avg_entry - (trail_levels * 0.01), 2)

    def update_sl_for_group(self, sym: str, side: str, new_sl: float) -> int:
        """Update SL for all open positions of sym+side."""
        if self.paused or (new_sl == 0 and self.fixed_sl is None):
            return 0

        updated = 0
        for (s, sd, ticket), pos in self.positions.items():
            if s == sym and sd == side:
                target_sl = self.fixed_sl if self.fixed_sl is not None else new_sl
                if target_sl != 0 and target_sl != self.current_sls[(s, sd, ticket)]:
                    ok, _ = self.bridge.set_sl(pos, target_sl)
                    if ok:
                        self.current_sls[(s, sd, ticket)] = target_sl
                        updated += 1

        return updated

    def prompt_fixed_sl(self, stdscr):
        """Prompt user to enter a fixed SL price."""
        curses.curs_set(1)
        curses.echo()
        curses.nocbreak()

        h, w = stdscr.getmaxyx()
        stdscr.addstr(h - 1, 0, " " * w)
        stdscr.addstr(h - 1, 0, "Enter SL price (empty to cancel): ", curses.A_BOLD)
        stdscr.refresh()

        try:
            response = stdscr.getstr(h - 1, 34, 10).decode("utf-8").strip()
            if response:
                self.fixed_sl = float(response)
                self.message = f"✅ Fixed SL set to {self.fixed_sl}"
            else:
                self.message = "Cancelled"
        except ValueError:
            self.message = "❌ Invalid price"

        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)

    def run(self, stdscr):
        """Main TUI loop."""
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Header
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Positive
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # Negative
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Status / Warning
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Paused

        if not self.connect():
            stdscr.addstr(0, 0, "❌ Failed to connect to MT5")
            stdscr.refresh()
            stdscr.getch()
            return

        last_update = 0
        while self.running:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            now = time.time()
            if now - last_update >= 1.0:
                self.refresh_positions()
                last_update = now

            # Draw header
            if self.fixed_sl is not None:
                state = f" [🔒 FIXED SL={self.fixed_sl}]"
            elif self.paused:
                state = " [⏸ PAUSED]"
            else:
                state = f" [▶ TRAILING ${self.trail_step}]"

            header = f"🚀 Trailing Stop Monitor{state}"
            stdscr.addstr(0, 0, header[:w], curses.color_pair(1))

            # Check if any positions exist
            if not self.positions:
                stdscr.addstr(2, 0, "No open positions", curses.color_pair(5))
                footer_y = h - 3
                if self.message:
                    stdscr.addstr(footer_y + 1, 0, self.message[:w], curses.color_pair(4))
                footer = "P: Pause/Resume | S: Set SL | Q: Quit"
                stdscr.addstr(footer_y, 0, footer[:w], curses.color_pair(4))
                stdscr.refresh()
                stdscr.timeout(500)
                key = stdscr.getch()
                self._handle_key(key, stdscr)
                continue

            # Draw column headers
            col_header = "SYMBOL    SIDE  VOL      ENTRY      PRICE      P/L       CURRENT_SL  TRAIL_SL  UPDATED"
            stdscr.addstr(1, 0, col_header[:w], curses.color_pair(1))

            # Draw positions grouped
            row_idx = 2
            grouped = self.get_position_averages()

            for (sym, side), data in sorted(grouped.items()):
                pnl = data["pnl"]
                avg_entry = data["avg_entry"]
                current_sl = data["avg_sl"]

                # Determine SL to use
                if self.fixed_sl is not None:
                    new_sl = self.fixed_sl
                    new_sl_str = f"{new_sl:.2f}"
                elif not self.paused:
                    new_sl = self.calculate_trail_sl(side, pnl, avg_entry)
                    new_sl_str = f"{new_sl:.2f}" if new_sl > 0 else "—"
                else:
                    new_sl = 0
                    new_sl_str = "—"

                # Update in MT5
                updated = self.update_sl_for_group(sym, side, new_sl)

                pnl_color = curses.color_pair(2) if pnl >= 0 else curses.color_pair(3)

                status = f"✅ {updated}" if updated > 0 else "—"

                line = (
                    f"{sym:<10} {side:<6} "
                    f"{data['total_vol']:.4f}  {avg_entry:>10.2f}  "
                    f"{data['current_price']:>10.2f}  "
                    f"${pnl:>8.2f}  "
                    f"{current_sl:>11.2f}  {new_sl_str:>8}  {status}"
                )
                stdscr.addstr(row_idx, 0, line[:w], pnl_color)
                row_idx += 1

            # Draw footer
            footer_y = h - 3
            if self.message:
                stdscr.addstr(footer_y + 1, 0, self.message[:w], curses.color_pair(4))
                self.message = ""  # Clear after display

            mode_text = (
                "🔒 FIXED SL (S to change)" if self.fixed_sl is not None
                else ("⏸ PAUSED (P to resume)" if self.paused else "▶ ACTIVE (P to pause)")
            )
            footer = f"{mode_text} | S: Set SL | Q: Quit | R: Refresh"
            stdscr.addstr(footer_y, 0, footer[:w], curses.color_pair(4))

            time_til_next = 1.0 - (now - last_update)
            status_line = f"Next update in {time_til_next:.1f}s | {datetime.now().strftime('%H:%M:%S')}"
            stdscr.addstr(footer_y + 2, 0, status_line[:w], curses.color_pair(5))

            stdscr.refresh()

            # Non-blocking input
            stdscr.timeout(100)
            key = stdscr.getch()
            self._handle_key(key, stdscr)

    def _handle_key(self, key, stdscr):
        """Handle keyboard input."""
        if key == ord("q") or key == ord("Q"):
            self.running = False
        elif key == ord("p") or key == ord("P"):
            if self.fixed_sl is None:
                self.paused = not self.paused
                self.message = "⏸ Paused" if self.paused else "▶ Resumed"
        elif key == ord("s") or key == ord("S"):
            self.prompt_fixed_sl(stdscr)
            if self.fixed_sl is not None:
                self.paused = False  # Resume with fixed SL
        elif key == ord("r") or key == ord("R"):
            self.refresh_positions()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Trailing stop monitor")
    parser.add_argument("--trail", type=float, default=2.0, help="Trail step in USD (default: 2.0)")
    args = parser.parse_args()

    ui = TrailUI(trail_step=args.trail)

    try:
        curses.wrapper(ui.run)
    except KeyboardInterrupt:
        pass
    finally:
        ui.bridge.disconnect()
        print("✅ Trailing stop monitor stopped.")


if __name__ == "__main__":
    main()
