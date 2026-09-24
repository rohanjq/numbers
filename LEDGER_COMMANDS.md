# Ledger Command — Complete Guide

**TL;DR:** Run `./ledger help` or pick from the commands below.

## Commands

### `ledger view`
View all trades (open + closed) in your terminal.

```bash
./ledger view
```

Shows:
```
📊 Current ledger:
symbol  side  num_trades  ... pnl      ... rationale                  followed_from
XAUUSD  BUY   2           ... +150.00  ... 1m wick rejection + HMA     my_signal
BTCUSD  BUY   1           ... +5.00    ...                            TradingView breakout
```

---

### `ledger update`
Refresh ALL open positions from MT5. Pulls live prices, P/L, and merges with existing closed trades.

```bash
./ledger update
```

Output:
```
[14:47:22] 🔗 Connected to MT5 localhost:8001
[14:47:23] Exported 2 trades (open+closed) to ledger.csv
  Open: 1 | Closed: 1 | Wallet: $750.00 | MT5: $65.25
```

---

### `ledger close <SYMBOL> <SIDE> [rationale] [source]`
Log a closed position group to CSV after manually closing all legs in MT5.

```bash
# Minimal (just symbol + side)
./ledger close XAUUSD BUY

# With details
./ledger close XAUUSD BUY "Hit TP at 4125" "my_signal"

# Another example
./ledger close BTCUSD SELL "Broke support" "tip: @Bob"
```

Creates a new CLOSED row in `ledger.csv` with:
- Timestamp
- Your wallet snapshot at that moment
- Total capital
- Status: CLOSED
- Rationale & followed_from (from your inputs)

---

### `ledger edit`
**CLI-based CSV editor** — edit rationale and followed_from fields for any trade.

```bash
./ledger edit
```

**Controls:**
- `↑` / `↓` — move between rows (trades)
- `←` / `→` — scroll left/right through columns
- `E` — edit the selected cell (only `rationale` and `followed_from` are editable)
- `W` — write/save changes to CSV
- `Q` — quit without saving (changes from E+Enter are auto-saved)

**Example workflow:**
```
1. Run: ./ledger edit
2. Press ↓ to scroll to the XAUUSD BUY row
3. Press → to scroll to the "rationale" column
4. Press E
5. Type: "HMA cross + 1m wick rejection"
6. Press Enter
7. Press W to save
8. Press Q to quit
```

---

### `ledger sl <PRICE> [SYMBOL] [TP_PRICE]`
**One-time SL setter** — set stop loss on ALL open positions of a symbol.

```bash
# Set SL on all XAUUSD
./ledger sl 4100

# Set SL on all BTCUSD
./ledger sl 62000 BTCUSD

# Set SL + TP on all XAUUSD
./ledger sl 4100 XAUUSD 4120
```

Output:
```
📍 Found 3 position(s) for XAUUSD
   Setting SL to 4100 | TP to 4120

✅ Ticket #70001: SL set on #70001
✅ Ticket #70002: SL set on #70002
✅ Ticket #70003: SL set on #70003

✅ Updated 3 position(s)
```

---

### `ledger trail [USD]`
**Live trailing stop monitor** — auto-updates SL every second based on profit movement.

```bash
# Trail with $2 per step (default)
./ledger trail

# Trail with $2.50 per step
./ledger trail 2.50

# Trail with $5 per step (more aggressive)
./ledger trail 5.0
```

**Live display:**
```
🚀 Trailing Stop Monitor [▶ TRAILING $2.0]
SYMBOL    SIDE  VOL      ENTRY      PRICE      P/L       CURRENT_SL  TRAIL_SL  UPDATED
XAUUSD    BUY   0.1000   4120.50    4125.30    +150.00   4120.00     4120.50   ✅ 1
BTCUSD    BUY   0.0050   62850.0    62900.0    +5.00     0.00        —         —

▶ ACTIVE (P to pause) | S: Set SL | Q: Quit | R: Refresh
Next update in 0.8s | 14:47:22
```

**Controls:**
- `P` = Pause/resume trailing (SL freezes at current value)
- `S` = Set a fixed SL (switches to lockdown mode, stops trailing)
- `R` = Refresh position data from MT5
- `Q` = Quit

**Modes:**
1. **▶ ACTIVE** — Trailing auto-updates SL (press P to pause)
2. **⏸ PAUSED** — SL frozen at current value (press P to resume)
3. **🔒 FIXED SL** — Use a manual price you entered (press S to enter new price)

**Example workflow:**
```
1. Run: ./ledger trail 2.5
2. Monitor updates every second
3. Profit grows: +$100 → SL trails up to protect gains
4. Want to lock in? Press S → Enter 4120 → SL is now fixed at 4120
5. Change mind? Press S again → Enter new price
6. Or press P to pause trailing temporarily
7. Press Q to exit
```

---

## CSV Structure

| Column | Type | Auto? | Editable? | Example |
|--------|------|-------|-----------|---------|
| **symbol** | Text | ✅ | — | XAUUSD, BTCUSD |
| **side** | Text | ✅ | — | BUY, SELL |
| **num_trades** | Number | ✅ | — | 3 (legs merged) |
| **open_time** | ISO timestamp | ✅ | — | 2026-07-08T14:47:22 |
| **first_trade** | ISO timestamp | ✅ | — | 2026-07-08T14:32:15 |
| **avg_entry_price** | Price | ✅ | — | 4120.50 |
| **current_price** | Price | ✅ | — | 4125.30 |
| **avg_xir_price** | Price | ✅ | — | 4120.50 |
| **total_volume** | Float | ✅ | — | 0.10 |
| **pnl** | USD | ✅ | — | +150.00 |
| **risk_reward_ratio** | Ratio | ✅ | — | 2.31 |
| **wallet_at_entry** | USD | ✅ | — | 750.00 |
| **total_capital** | USD | ✅ | — | 815.25 |
| **status** | Text | ✅ | — | OPEN or CLOSED |
| **rationale** | Text | — | 🖊️ Edit | "HMA cross + 1m wick" |
| **followed_from** | Text | — | 🖊️ Edit | "my_signal", "TradingView", "tip: @Bob" |
| **ticket_ids** | IDs | ✅ | — | 70001,70002,70003 |

---

## Complete Workflow Example

**Scenario:** You're day trading XAUUSD.

**14:30 UTC** – Enter position (3 legs)
- You manually enter 3 separate BUY orders in MT5 (0.05 + 0.05 + 0.04 vol)
- They fill over ~30 sec

**14:32 UTC** – Start trailing SL
```bash
./ledger trail 2.0
```
- TUI shows average entry ~4120.50
- Profit starts at ~$0 (fresh entry)
- Trailing SL shows no movement yet (need profit first)

**14:38 UTC** – Profit grows to +$150
- Trail display updates: "TRAIL_SL: 4120.50" (SL has moved up by $150 of profit)
- Every second, SL adjusts as profit changes

**14:42 UTC** – You want to lock in gains
- Press `S` in TUI
- Enter: `4121.00`
- TUI switches to 🔒 FIXED SL mode
- SL is now frozen at 4121.00, won't trail anymore

**14:45 UTC** – Market moves against you, hits your SL
- You manually close all 3 legs in MT5 (or SL triggers)
- You're out with realized +$150 P/L

**14:47 UTC** – Log the close
```bash
./ledger close XAUUSD BUY "Trailed SL, locked at 4121" "my_signal"
```
- New CLOSED row added to `ledger.csv`
- Shows wallet snapshot, total capital, P/L

**14:50 UTC** – Review & refine (optional)
```bash
./ledger edit
```
- Navigate to the XAUUSD row
- Edit "rationale" to add more detail: "HMA cross + 1m wick rejection, trailed $2 steps"
- Save

**14:52 UTC** – Check for new open positions
```bash
./ledger update
```
- Pulls fresh positions from MT5
- You might have entered a new BTCUSD BUY while trailing
- CSV now shows: XAUUSD BUY (CLOSED) + BTCUSD BUY (OPEN)

---

## Tips & Tricks

### Keyboard Shortcuts

**In `ledger edit`:**
- Type quickly: the editor accepts standard terminal input
- No fancy regex; just type the text
- `W` saves immediately to disk

**In `ledger trail`:**
- `P` toggles pause without stopping the display
- `S` + number + Enter is fast: `S` → `4100` → Enter
- `R` refreshes without pausing

### Backups

```bash
# Backup your ledger before trading sessions
cp ledger.csv ledger_backup_$(date +%Y%m%d_%H%M%S).csv

# Or commit to git
git add ledger.csv && git commit -m "Day 1 trades"
```

### Multiple Symbols

- `ledger trail` works with ANY open symbols (XAUUSD, BTCUSD, ETHUSD simultaneously)
- `ledger sl 62000 BTCUSD` sets SL on just BTCUSD, leaving gold alone
- `ledger close` works one symbol+side at a time, then you can `close` another

### When MT5 Bridge is Down

- `ledger view` works (just shows CSV)
- `ledger edit` works (just edits CSV)
- `ledger update` will fail (needs live MT5)
- `ledger trail` will fail (needs live MT5)
- `ledger sl` will fail (needs live MT5)

---

## Troubleshooting

**Command not found?**
```bash
./ledger help  # Must run from /root/numbers
# Or add to PATH: export PATH="/root/numbers:$PATH"
```

**"No open positions" message?**
```bash
./ledger view                    # Check if there are any trades
./ledger close XAUUSD BUY        # Log a close to see new row
./ledger update                  # Refresh from MT5
```

**Edit mode won't let me type rationale?**
- Make sure you pressed `E` (not just ↑↓)
- Only `rationale` and `followed_from` columns are editable
- If the line is grayed out, you're in a read-only column

**Trail SL not updating?**
- Check if you pressed `P` (paused mode)
- Check if you pressed `S` (fixed SL mode)
- Make sure MT5 connection is active

---

## Quick Reference

```bash
# View
./ledger view

# Update
./ledger update

# Close (log off)
./ledger close XAUUSD BUY "why" "source"

# Edit (manual)
./ledger edit

# Set SL (one-time)
./ledger sl 4100

# Trail SL (live monitor)
./ledger trail 2.0

# Help
./ledger help
```

All commands must be run from `/root/numbers/` directory (or add to PATH).
