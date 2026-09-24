# Ledger Command Cheatsheet

## One-Liners

```bash
./ledger view                                    # See all trades
./ledger update                                  # Pull positions from MT5
./ledger edit                                    # Edit rationale/followed_from (CLI)
./ledger close XAUUSD BUY "reason" "source"     # Log a closed trade
./ledger sl 4100                                 # Set SL on all XAUUSD
./ledger trail 2.0                               # Live trailing stop monitor
./ledger help                                    # Full reference
```

## Trail Monitor Controls

| Key | Action |
|-----|--------|
| `P` | Pause/resume trailing |
| `S` | Set fixed SL (stops trailing) |
| `R` | Refresh positions |
| `Q` | Quit |

## CLI Editor Controls

| Key | Action |
|-----|--------|
| `↑`/`↓` | Move rows |
| `←`/`→` | Scroll columns |
| `E` | Edit cell (rationale, followed_from only) |
| `W` | Write/save |
| `Q` | Quit |

## CSV Columns (Read-only unless noted)

```
symbol              symbol of trade (XAUUSD, BTCUSD, etc)
side                BUY or SELL
num_trades          number of legs merged
open_time           ISO timestamp when opened
first_trade         ISO timestamp of first leg
avg_entry_price     volume-weighted entry price
current_price       live market price (if OPEN)
avg_xir_price       (same as avg_entry for now)
total_volume        sum of all volumes
pnl                 profit/loss in USD
risk_reward_ratio   P/L / account equity
wallet_at_entry     your wallet balance at entry
total_capital       wallet + MT5 equity
status              OPEN or CLOSED
rationale           🖊️ EDITABLE - why you entered
followed_from       🖊️ EDITABLE - who/what signal
ticket_ids          MT5 ticket numbers
```

## Usage Patterns

### Simple Day Trade
```bash
# 1. Trade normally in MT5
# 2. Set SL when ready
./ledger sl 4100 XAUUSD

# 3. Close all legs in MT5
# 4. Log the close
./ledger close XAUUSD BUY "hit TP" "my_signal"

# 5. View recap
./ledger view
```

### Trailing Stop Trade
```bash
# 1. Trade in MT5
# 2. Start trailing monitor
./ledger trail 2.5

# 3. In monitor: Press P if need to pause, S if want to lock
#    Press Q when done

# 4. After closing in MT5
./ledger close XAUUSD BUY "trailed SL" "my_signal"

# 5. Optionally edit
./ledger edit
```

### Multiple Symbols
```bash
# Trade XAUUSD and BTCUSD simultaneously
./ledger trail 2.0    # Monitors both

# Close XAUUSD first
./ledger close XAUUSD BUY "..." "..."

# Continue trailing BTCUSD, then close
./ledger close BTCUSD SELL "..." "..."

# View all
./ledger view
```

## Common Mistakes

❌ `./ledger sl 4100` when not in /root/numbers dir
→ Use: `./ledger sl 4100`

❌ Trying to edit columns that aren't rationale/followed_from
→ Only those 2 columns are editable in CLI editor

❌ Running trail while not connected to MT5
→ Check MT5 bridge is running first

## Tips

- **Backup before trading:**
  ```bash
  cp ledger.csv ledger_backup_$(date +%s).csv
  ```

- **View ledger in CSV viewer:**
  ```bash
  # Column-aligned display
  column -t -s',' ledger.csv | less
  
  # Or open directly
  vim ledger.csv
  libreoffice --calc ledger.csv
  ```

- **Git tracking:**
  ```bash
  git add ledger.csv
  git commit -m "Day 1: XAUUSD +$150, BTCUSD +$5"
  ```

- **Multi-monitor setup:** Run trail on one display, trade on another

## File Locations

- Command: `/root/numbers/ledger`
- CSV: `/root/numbers/ledger.csv`
- Scripts: `/root/numbers/scripts/update_ledger.py`, `edit_ledger.py`, `trail.py`, `set_sl.py`, `on_close_group.py`
- Docs: `LEDGER_COMMANDS.md`, `LEDGER_QUICK_START.md`, `LEDGER_WORKFLOW.md`

## Exit Codes

```
0 = success
1 = error or invalid input
```

Check stderr for error messages if something fails.
