# 🚀 Ledger — Start Here

## What Is It?

A **CLI-based trade tracking system** for MT5 that:
- Groups your multi-leg positions by symbol+side (e.g., 3 XAUUSD BUY legs = 1 row)
- Tracks live P/L, prices, and wallet snapshots
- Lets you edit WHY you entered (rationale) and WHO gave the signal (followed_from)
- **Trails your stop loss** in real-time as profit grows
- Logs closed trades to a simple CSV file

## Quick Start (5 minutes)

### 1. View Your Trades
```bash
cd /root/numbers
./ledger view
```

### 2. After Closing Positions in MT5
```bash
./ledger close XAUUSD BUY "TP hit at 4125" "my_signal"
```

### 3. Edit Details Later
```bash
./ledger edit
```
- Press ↑↓ to move rows
- Press E to edit `rationale` or `followed_from`
- Press W to save

### 4. Live Trailing Stop
```bash
./ledger trail 2.0
```
- TUI shows all positions + current SL + trailing SL
- Press P to pause, S to lock SL, Q to quit

### 5. Set Fixed SL
```bash
./ledger sl 4100
```
Sets SL on all XAUUSD positions to 4100.

---

## The CSV

**File:** `ledger.csv`

**Key columns:**
- `symbol`, `side` — XAUUSD BUY
- `avg_entry_price`, `current_price` — Live prices
- `pnl` — Profit/loss in USD
- `rationale` — 🖊️ Why you entered (you edit this)
- `followed_from` — 🖊️ Who/what signal (you edit this)
- `status` — OPEN or CLOSED
- `ticket_ids` — MT5 order numbers

---

## Typical Trading Day

```
1. Trade in MT5 (enter 3 legs XAUUSD BUY)
   ↓
2. ./ledger trail 2.0
   Monitor screen shows: avg entry 4120.50, current 4125 (+$150)
   SL auto-trails as profit grows
   ↓
3. Press P to pause if you want control
   Press S to lock SL at 4121.00 (stops trailing)
   ↓
4. Close all 3 legs in MT5
   ↓
5. ./ledger close XAUUSD BUY "Trailed $2, locked at 4121" "my_signal"
   → Adds CLOSED row to CSV with wallet snapshot
   ↓
6. ./ledger edit
   → Fine-tune rationale: "HMA cross + 1m wick rejection"
   ↓
7. ./ledger view
   → See your trades: XAUUSD BUY (CLOSED, +$150) + any new opens
```

---

## Commands (Copy & Paste)

| Command | What It Does |
|---------|-------------|
| `./ledger view` | Show all trades |
| `./ledger update` | Pull fresh positions from MT5 |
| `./ledger close SYMBOL SIDE "why" "source"` | Log a closed trade |
| `./ledger edit` | CLI editor: ↑↓ move, E edit, W save |
| `./ledger sl PRICE [SYM]` | Set SL on all positions |
| `./ledger trail [USD]` | Live trailing stop monitor |
| `./ledger help` | Full reference |

---

## In The Trailing Monitor

```
🚀 Trailing Stop Monitor [▶ TRAILING $2.0]

SYMBOL    SIDE  VOL      ENTRY      PRICE      P/L       CURRENT_SL  TRAIL_SL  UPDATED
XAUUSD    BUY   0.10     4120.50    4125.30    +150.00   4120.00     4120.50   ✅ 1
BTCUSD    BUY   0.005    62850.0    62900.0    +5.00     0.00        —         —

▶ ACTIVE (P to pause) | S: Set SL | Q: Quit | R: Refresh
```

- **P** = Pause/resume (SL freezes)
- **S** = Lock SL to a price (stops trailing)
- **Q** = Quit
- **R** = Refresh

---

## Documentation

- **RUN_LEDGER.txt** — Quick commands (copy/paste)
- **LEDGER_CHEATSHEET.md** — One-liners + controls
- **LEDGER_COMMANDS.md** — Full reference with examples
- **LEDGER_QUICK_START.md** — Each command explained
- **RUN_LEDGER.txt** — ASCII boxes (print-friendly)

---

## Key Features

✅ **Multi-leg grouping** — 3 separate trades → 1 CSV row
✅ **Live P/L** — Updated every second from MT5
✅ **Trailing SL** — Auto-moves SL based on profit ($2 per step, customizable)
✅ **Pause/resume** — Press P to freeze SL, edit manually if needed
✅ **Lock SL** — Press S to set fixed SL (stops trailing)
✅ **Wallet snapshot** — Records your capital state at entry
✅ **Editable fields** — Fill in WHY and WHO for every trade
✅ **CLI-only** — No web server, pure terminal UI

---

## First Time?

1. **Read this file** (you are here ✓)
2. **Try it:** `./ledger view`
3. **See help:** `./ledger help`
4. **Read cheatsheet:** `cat LEDGER_CHEATSHEET.md`

---

## File Locations

- **Command:** `/root/numbers/ledger`
- **CSV:** `/root/numbers/ledger.csv`
- **Scripts:** `/root/numbers/scripts/`
- **Docs:** All `.md` files in `/root/numbers/`

---

## Common First Questions

**Q: Do I run this IN MT5?**
A: No, run in a terminal next to MT5. Both can be open side-by-side.

**Q: How do I edit the CSV manually?**
A: Use `./ledger edit` (CLI) or open `ledger.csv` in a text editor or Excel.

**Q: Can I use this for swing trades?**
A: Yes, just log closes manually: `./ledger close SYMBOL SIDE "reason" "source"`

**Q: What if MT5 crashes?**
A: `./ledger view` and `./ledger edit` work without MT5. Other commands fail gracefully.

**Q: Can I track multiple symbols at once?**
A: Yes, `./ledger trail 2.0` monitors ALL open symbols simultaneously.

---

## Next Steps

1. Trade in MT5 normally
2. When ready to protect gains: `./ledger trail 2.0`
3. After closing: `./ledger close SYMBOL SIDE "reason" "source"`
4. Edit later: `./ledger edit`
5. View anytime: `./ledger view`

---

**Questions?** See `LEDGER_COMMANDS.md` for full reference or run `./ledger help`.
