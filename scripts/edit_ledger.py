#!/usr/bin/env python3
"""CLI-based CSV editor — navigate with arrow keys, edit with Enter."""
from __future__ import annotations

import csv
import curses
import os
import sys

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings


class CSVEditor:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.rows = []
        self.fieldnames = []
        self.selected_row = 0
        self.selected_col = 0
        self.editable_cols = {"rationale", "followed_from"}
        self.load()

    def load(self):
        """Load CSV into memory."""
        if os.path.exists(self.csv_path):
            with open(self.csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.fieldnames = reader.fieldnames or []
                self.rows = list(reader) if reader else []
        else:
            self.rows = []
            self.fieldnames = []

    def save(self):
        """Save CSV back to disk."""
        if not self.rows or not self.fieldnames:
            return
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)

    def is_editable(self, col_name: str) -> bool:
        return col_name in self.editable_cols

    def run(self, stdscr):
        """Main TUI loop."""
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)

        # Color pairs
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Header
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Selected
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Editable field
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Help text

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            # Draw header
            if self.fieldnames:
                header = " | ".join(self.fieldnames[:8])  # Show first 8 columns
                stdscr.addstr(0, 0, header[:w], curses.color_pair(1))

            # Draw rows
            for i, row in enumerate(self.rows[:h - 4]):
                is_selected = i == self.selected_row
                values = [str(row.get(col, ""))[:15] for col in self.fieldnames[:8]]
                line = " | ".join(values)
                color = curses.color_pair(3) if is_selected else curses.color_pair(2)
                stdscr.addstr(i + 1, 0, line[:w], color)

            # Draw footer
            footer_y = h - 2
            footer = "↑↓: Move | L/R: Scroll | E: Edit | W: Write | Q: Quit"
            stdscr.addstr(footer_y, 0, footer[:w], curses.color_pair(5))

            status = f"Row {self.selected_row + 1}/{len(self.rows)} | Col {self.selected_col + 1}/{len(self.fieldnames)}"
            stdscr.addstr(footer_y + 1, 0, status[:w], curses.color_pair(2))

            stdscr.refresh()

            # Handle input
            key = stdscr.getch()

            if key == ord("q") or key == ord("Q"):
                break
            elif key == ord("w") or key == ord("W"):
                self.save()
                stdscr.addstr(footer_y - 1, 0, "✅ Saved!", curses.color_pair(5))
                stdscr.refresh()
                curses.napms(500)
            elif key == ord("e") or key == ord("E"):
                if self.selected_row < len(self.rows):
                    self.edit_cell(stdscr)
            elif key == curses.KEY_UP:
                self.selected_row = max(0, self.selected_row - 1)
            elif key == curses.KEY_DOWN:
                self.selected_row = min(len(self.rows) - 1, self.selected_row + 1)
            elif key == curses.KEY_LEFT:
                self.selected_col = max(0, self.selected_col - 1)
            elif key == curses.KEY_RIGHT:
                self.selected_col = min(len(self.fieldnames) - 1, self.selected_col + 1)

    def edit_cell(self, stdscr):
        """Edit the selected cell."""
        if self.selected_row >= len(self.rows):
            return

        col = self.fieldnames[self.selected_col]
        if not self.is_editable(col):
            return

        row = self.rows[self.selected_row]
        old_val = row.get(col, "")

        curses.curs_set(1)  # Show cursor
        h, w = stdscr.getmaxyx()
        edit_y = h - 3

        stdscr.addstr(edit_y, 0, " " * w)
        stdscr.addstr(edit_y, 0, f"Edit {col}: ", curses.color_pair(4))
        stdscr.refresh()

        curses.echo()
        curses.nocbreak()
        new_val = stdscr.getstr(edit_y, len(f"Edit {col}: "), w - len(f"Edit {col}: ") - 1).decode("utf-8")
        curses.noecho()
        curses.cbreak()

        if new_val or new_val == "":  # Allow empty string
            row[col] = new_val
            self.save()

        curses.curs_set(0)  # Hide cursor


def main():
    s = Settings()
    csv_path = os.path.join(s.project_root, "ledger.csv")

    if not os.path.exists(csv_path):
        print(f"❌ No ledger found at {csv_path}")
        print("   First run: ./ledger update")
        sys.exit(1)

    editor = CSVEditor(csv_path)

    if not editor.rows:
        print("❌ CSV is empty.")
        sys.exit(1)

    print(f"📝 Editing {csv_path}")
    print("   Editable columns: rationale, followed_from")
    print("   Controls: ↑↓ move rows | L/R move columns | E edit | W write | Q quit")
    print("")

    try:
        curses.wrapper(editor.run)
        print("✅ Done!")
    except KeyboardInterrupt:
        print("\n⚠️  Cancelled without saving.")
        sys.exit(0)


if __name__ == "__main__":
    main()
