# Numbers

A discipline + ledger agent for a **$1,000 → $40,000 in 13 working days** run
(x**1.328**/day). It keeps **you in full control**: it reviews your MT5 trades
over the `mt5linux` rpyc bridge, enforces a **5%–7.5% exposure** cap, keeps a
SQLite **ledger** of every trade and its rationale, tells you today's goal, and
pings you on **Pushover** when you drift out of control.

**It never trades for you.** It advises, tracks, warns, and motivates.

See **[AGENTS.md](AGENTS.md)** for the full operating charter — that is the file
an agent (opencode / code CLI) should read first.

## Quick start (uv)

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env          # bridge, capital, exposure %, pushover
python scripts/daily_goal.py
python scripts/check_status.py --notify
```

On the Linux box next to MT5, also `uv pip install mt5linux`. Without it, the
scripts run in **MOCK** mode for local testing.

## Scripts

| Script | What it does |
|--------|--------------|
| `scripts/check_status.py` | One-shot: mission + exposure + P/L, optional Pushover alert |
| `scripts/watch.py` | Runs check_status every 1–2 min |
| `scripts/positions.py` | Open positions, running P/L, volume-weighted averages |
| `scripts/set_sl.py` | Set SL/TP on all positions of a symbol |
| `scripts/close_all.py` | Close all positions of a symbol (logs P/L) |
| `scripts/log_trade.py` | Record a trade + rationale into the ledger |
| `scripts/daily_goal.py` | Today's target on the 1.328×/day ladder |

## Exposure policy

MT5 must hold **5%–7.5% of total capital** (wallet + MT5). 5% is the target,
7.5% the hard cap. Between the two, the agent asks if it was a high-confidence
trade; above it, it warns you're not in control.
