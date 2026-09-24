# Ledger & CSV Workflow

## Installation

Make the command globally accessible in your project:

```bash
cd /root/numbers
chmod +x ./ledger
# Then use: ./ledger <command>
# Or add to PATH: export PATH="/root/numbers:$PATH"
```

Once added to PATH, you can run `ledger` from anywhere in the project.

## Quick Start

After you trade and close positions, here's the flow:

### 1. Close All Positions for a Symbol+Side

When you're done trading XAUUSD BUY (you've closed all 3 legs manually in MT5):

```bash
.venv/bin/python scripts/on_close_group.py XAUUSD BUY "hit TP at 4125" "my_signal"
```

This logs a **CLOSED** row to `ledger.csv` with:
- Your wallet snapshot at that moment
- Total capital (wallet + MT5 equity)
- Status: CLOSED
- Rationale & followed_from (your inputs above)

### 2. Edit CSV Manually (Web UI)

Want to refine the rationale, add notes, or update followed_from for ANY trade?

```bash
.venv/bin/python scripts/edit_ledger.py 5000
```

Then open http://localhost:5000 in your browser. You can:
- Edit **rationale** (why you entered, e.g., "1m wick rejection")
- Edit **followed_from** (who/what signal, e.g., "tip: @Bob", "my_signal", "TradingView chart pattern")
- Auto-saves to CSV (Ctrl+S or click 💾 Save)
- All other columns are read-only (computed from API)

### 3. Refresh Open Positions

To see current **OPEN** positions pulled fresh from MT5:

```bash
.venv/bin/python scripts/update_ledger.py
```

This merges:
- Any existing **CLOSED** rows (preserved)
- Fresh **OPEN** positions from MT5 (live P/L updated)

---

## CSV Columns

| Column | Type | Who sets | Notes |
|--------|------|----------|-------|
| **symbol** | Text | API | XAUUSD, BTCUSD, etc. |
| **side** | Text | API | BUY or SELL |
| **num_trades** | Number | API | How many legs merged |
| **open_time** | ISO timestamp | Script | When group opened |
| **first_trade** | ISO timestamp | Script | First leg timestamp |
| **avg_entry_price** | Price | API | Volume-weighted avg entry |
| **current_price** | Price | API | Live market (if open) |
| **avg_xir_price** | Price | API | Same as avg_entry for now |
| **total_volume** | Float | API | Sum of all volumes |
| **pnl** | USD | API | P/L realized (closed) or unrealized (open) |
| **risk_reward_ratio** | Ratio | API | P/L ÷ account equity at entry |
| **wallet_at_entry** | USD | Script | Your outer wallet balance at entry |
| **total_capital** | USD | Script | wallet + MT5 equity at entry |
| **status** | Text | Script | OPEN or CLOSED |
| **rationale** | Text | You 🖊️ | WHY you entered (editable in UI) |
| **followed_from** | Text | You 🖊️ | WHO/WHAT signal (editable in UI) |
| **ticket_ids** | IDs | API | Comma-separated MT5 ticket #s |

---

## Example Workflow (Day 1 Real Trade)

**14:32 UTC** — Enter XAUUSD BUY (2 legs: 0.05 + 0.05 vol)
- MT5 shows 2 open positions, avg entry 4120.50

**14:47 UTC** — Hit TP, close both legs in MT5
```bash
.venv/bin/python scripts/on_close_group.py XAUUSD BUY "HMA cross + 1m wick rej" "my_signal"
```
Output:
```
[14:47:22] ✅ Logged close: XAUUSD BUY
   Wallet: $750.00 | MT5: $65.25
   CSV: /root/numbers/ledger.csv
```

**14:50 UTC** — View & edit in web UI
```bash
.venv/bin/python scripts/edit_ledger.py 5000
# → Open http://localhost:5000
# → See XAUUSD BUY as CLOSED with your rationale
# → Refine "followed_from" to "my_signal + TradingView confluence"
# → Ctrl+S to save
```

**14:55 UTC** — Check for new open positions (you entered BTCUSD BUY while editing)
```bash
.venv/bin/python scripts/update_ledger.py
```
Output:
```
[14:55:33] Export 2 trades (open+closed) to ledger.csv
  Open: 1 | Closed: 1 | Wallet: $750.00 | MT5: $65.25
```

Now CSV has:
- Row 1: XAUUSD BUY, CLOSED, +$150, rationale filled, followed_from filled
- Row 2: BTCUSD BUY, OPEN, +$5 unrealized, rationale empty (you'll fill later)

---

## Tips

- **Order matters?** No, CSV rows can be in any order. Cols are what matter.
- **Can I manually add rows?** Yes, but keep the same column names. The editor UI shows all rows.
- **Backup?** Git-ignore the CSV for now (state/), but if you want to track it: manually commit after trading days.
- **Timestamp precision?** ISO strings (2026-07-08T14:47:22) for sorting, but you can edit them in the UI.

---

## Commands Reference

**Shorthand (using the `ledger` command):**

```bash
ledger update              # Refresh open positions
ledger close <S> <B> ...  # Log a close
ledger edit [port]        # Open web UI
ledger view               # Show CSV in terminal
ledger help               # Show help
```

**Full form (direct Python):**

```bash
# After closing all legs of a position
.venv/bin/python scripts/on_close_group.py <SYMBOL> <SIDE> [rationale] [followed_from]

# Web UI to edit rationale & followed_from
.venv/bin/python scripts/edit_ledger.py [port]  # default 5000

# Refresh open positions from MT5
.venv/bin/python scripts/update_ledger.py [csv_filename]  # default ledger.csv

# Examples
ledger close XAUUSD BUY "1m wick + HMA" "my_signal"
ledger edit 5000
ledger update
ledger view
```
