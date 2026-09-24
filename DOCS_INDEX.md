# 📚 Documentation Index

**Read in this order:**

## 1. 🚀 **START_HERE.md** (You are here)
   - What the ledger is
   - 5-minute quick start
   - Common questions
   - **→ Read this first**

## 2. 📖 **RUN_LEDGER.txt**
   - Copy-paste command boxes
   - Typical day flow
   - ASCII quick reference
   - **→ Print or bookmark this**

## 3. ⚡ **LEDGER_CHEATSHEET.md**
   - One-liners for each command
   - Control keys for UI tools
   - Common mistakes
   - CSV column reference
   - **→ Tab this for quick lookup**

## 4. 📝 **LEDGER_QUICK_START.md**
   - Simple explanation of each command
   - Setup instructions
   - Troubleshooting
   - **→ Read when stuck**

## 5. 🔍 **LEDGER_COMMANDS.md**
   - Full reference for every command
   - Example workflows
   - Complete CSV structure
   - **→ Full manual, read as needed**

## 6. 🔄 **LEDGER_WORKFLOW.md**
   - Detailed trading workflow
   - How trailing works
   - Historical context
   - **→ Deep dive/reference**

## 7. 💻 **AGENTS.md**
   - Trading discipline charter
   - Agent responsibilities
   - Mission targets
   - **→ Overall context/strategy**

---

## Quick Command Reference

```bash
./ledger view              # See trades
./ledger update            # Pull from MT5
./ledger close S B "..." # Log close
./ledger edit              # Edit CSV (CLI)
./ledger sl 4100           # Set SL
./ledger trail 2.0         # Trailing monitor
./ledger help              # Full help
```

---

## By Use Case

### "I just opened positions"
→ `./ledger trail 2.0` (start monitoring)

### "I just closed everything"
→ `./ledger close XAUUSD BUY "reason" "source"`

### "I want to check my trades"
→ `./ledger view`

### "I want to update WHY I entered"
→ `./ledger edit` (↑↓ move, E edit, W save)

### "I want to set SL on all positions"
→ `./ledger sl 4100`

### "I want to set SL and trail it"
→ `./ledger trail 2.0` (press S to lock)

### "I want to see current positions from MT5"
→ `./ledger update`

---

## Files

| File | Purpose |
|------|---------|
| `ledger` | Main command (bash wrapper) |
| `ledger.csv` | Trade database |
| `scripts/update_ledger.py` | Pull positions from MT5 |
| `scripts/on_close_group.py` | Log closed trades |
| `scripts/edit_ledger.py` | CLI editor |
| `scripts/set_sl.py` | Set SL on all positions |
| `scripts/trail.py` | Trailing stop monitor |

---

## Other Context

- **AGENTS.md** — Your trading charter
- **config.py** — Settings (MT5 host, port, capital)
- **mt5_bridge.py** — MT5 connection

---

**Start with START_HERE.md, then use RUN_LEDGER.txt for daily commands.**
