# Ledger Command — Quick Start

## One-liner: What it does

Tracks **all your trades** (grouped by symbol+side) in a CSV you can edit. Each row = one position group (e.g., "XAUUSD BUY with 3 legs"). Columns include live P/L, wallet snapshot, and fields you fill in manually (rationale, who gave you the signal).

---

## How to use it

From `/root/numbers/`:

```bash
# View all trades
./ledger view

# After manually closing all legs of a position in MT5:
./ledger close XAUUSD BUY "1m wick rejection" "my_signal"

# Open CLI editor to fill in rationale/followed_from for any trade
./ledger edit
# Use ↑↓ to move rows, L/R to scroll, E to edit, W to save, Q to quit

# Refresh open positions from MT5
./ledger update

# See command help
./ledger help
```

---

## The Workflow

1. **Trade normally in MT5** (enter buy/sell, add/close legs)
2. **When you close ALL legs of a position:**
   ```bash
   ./ledger close XAUUSD BUY "HMA cross + 1m wick" "my_signal"
   ```
   ✅ Logs it to CSV with status=CLOSED, wallet snapshot, P/L.

3. **Edit details later in web UI:**
   ```bash
   ./ledger edit
   ```
   Change `rationale` or `followed_from`, then Ctrl+S.

4. **Check for new open positions:**
   ```bash
   ./ledger update
   ```
   Pulls fresh OPEN positions from MT5, adds them to CSV.

5. **View anytime:**
   ```bash
   ./ledger view
   ```

---

## What gets tracked

| Column | Auto | Manual | Example |
|--------|------|--------|---------|
| symbol, side | ✅ API | — | XAUUSD, BUY |
| num_trades | ✅ API | — | 3 (legs merged) |
| avg_entry_price, current_price | ✅ API | — | 4120.50, 4125.30 |
| total_volume, pnl, r:r | ✅ API | — | 0.10, +$150, +2.31 |
| wallet_at_entry, total_capital | ✅ Snapshot | — | $750, $815.25 |
| **rationale** | — | 🖊️ You | "1m wick rejection" |
| **followed_from** | — | 🖊️ You | "my_signal", "tip: @Bob" |
| ticket_ids | ✅ API | — | 70001,70002 |
| status | ✅ Script | — | OPEN or CLOSED |

---

## Examples

```bash
# Close a trade
./ledger close XAUUSD BUY "Hit TP at 4125" "my_signal"

# Close a trade (minimal)
./ledger close XAUUSD BUY

# View in terminal
./ledger view

# Edit in web UI (port 5000)
./ledger edit

# Edit in web UI (custom port 8080)
./ledger edit 8080

# Refresh open positions
./ledger update

# Get help
./ledger help
```

---

## Setup (one-time)

If you haven't run the scripts yet:

```bash
cd /root/numbers
chmod +x ./ledger

# On first use, Flask gets installed via uv
# Just run a command and it'll prompt or auto-install
./ledger view
```

---

## Under the hood

- `ledger update` → pulls live positions from MT5, exports to `ledger.csv`
- `ledger close` → appends a CLOSED row to `ledger.csv`
- `ledger edit` → starts a Flask web server (static IP editor, saves on Ctrl+S)
- `ledger view` → pretty-prints `ledger.csv` in your terminal

CSV lives at: `/root/numbers/ledger.csv`

---

## Troubleshooting

**No ledger.csv yet?**
```bash
./ledger update
```

**Can't connect to MT5?**
- Make sure the MT5 bridge is running (check AGENTS.md)
- Check `.env` for correct `MT5_HOST` and `MT5_PORT`

**Web UI won't start?**
```bash
# Install Flask if missing
uv pip install flask
./ledger edit 5000
```

**Want to backup your trades?**
```bash
cp ledger.csv ledger_backup.csv
# Or: git add ledger.csv && git commit -m "Day 1 trades"
```
