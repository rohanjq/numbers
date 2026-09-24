#!/usr/bin/env python3
"""Place a quick scalp on XAUUSD or BTCUSD with SL adjusted for spread.

Punches a market order immediately — no confirmation.

  --asset  : XAUUSD or BTCUSD (default XAUUSD)
  --risk   : max dollar amount you are willing to risk
  --side   : BUY or SELL
  --tp     : target price delta (default: 2.00 for gold, 100 for BTC)
  --be     : spawn daemon BE monitor, moves SL to breakeven+spread at 60% of TP
  --symbol : override symbol (default: XAUUSDp for gold, BTCUSD for BTC)

Point values: XAU = $100/lot, BTC = $1/lot
Spreads (live): gold ~$0.28, BTC ~$25

  TP  = entry +/- tp_delta
  SL  = entry -/+ (tp_delta - spread)   # spread cost absorbed into SL
  Volume = risk_dollars / [(tp_delta - spread) * point_value]

  Be-even SL = entry + spread (BUY) or entry - spread (SELL)

Usage:
  .venv/bin/python scripts/quick_scalp.py --side BUY --risk 4
  .venv/bin/python scripts/quick_scalp.py --side SELL --risk 15 --tp 1.5 --be
  .venv/bin/python scripts/quick_scalp.py --asset BTC --side SELL --risk 5 --tp 100 --be
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings
from mt5_bridge import Bridge

ASSETS = {
    "XAUUSD": {"default_symbol": "XAUUSDp", "default_tp": 2.0, "point_value": 100.0},
    "BTCUSD": {"default_symbol": "BTCUSDTp", "default_tp": 100,  "point_value": 1.0},
}

BE_THRESHOLD = 0.60
_monitor_stop = threading.Event()


def _compute(tick, tp_delta: float, risk_dollars: float, side: str,
            point_value: float):
    spread = round(tick.ask - tick.bid, 2)
    sl_delta = round(tp_delta - spread, 2)
    if sl_delta <= 0:
        return spread, sl_delta, None, None, None, None

    vol = risk_dollars / (sl_delta * point_value)
    if point_value == 100.0:   # gold: round to 0.01 lots
        vol = round(vol, 2)
        if vol < 0.01:
            vol = 0.01
    else:                      # BTC: round to 0.01 lots
        vol = round(vol, 2)
        if vol < 0.01:
            vol = 0.01

    if side == "BUY":
        entry = tick.ask
        tp_price = round(entry + tp_delta, 2)
        sl_price = round(entry - sl_delta, 2)
    else:
        entry = tick.bid
        tp_price = round(entry - tp_delta, 2)
        sl_price = round(entry + sl_delta, 2)

    return spread, sl_delta, vol, entry, sl_price, tp_price


def _be_price(entry: float, spread: float, side: str) -> float:
    return round(entry + spread, 2) if side == "BUY" else round(entry - spread, 2)


def _price_in_favor(current: float, entry: float, side: str) -> float:
    return current - entry if side == "BUY" else entry - current


def _monitor_be(s, host, port, symbol: str, side: str, entry: float,
                tp_delta: float, spread: float, ticket: int):
    threshold = round(tp_delta * BE_THRESHOLD, 2)
    be_sl = _be_price(entry, spread, side)
    be_set = False
    first_print = True

    while not _monitor_stop.is_set():
        try:
            br2 = Bridge(Settings(
                mt5_host=host, mt5_port=port, symbols=[symbol]
            ))
            ok, _ = br2.connect()
            if not ok:
                time.sleep(1)
                br2.disconnect()
                continue
        except Exception:
            time.sleep(1)
            continue

        try:
            tick = br2.tick(symbol)
            if tick is None:
                time.sleep(0.5)
                continue

            price = tick.bid if side == "BUY" else tick.ask
            moved = _price_in_favor(price, entry, side)

            if first_print:
                print(f"[BE] Watching #{ticket} "
                      f"| entry={entry:.2f} threshold=+${threshold:.2f} "
                      f"move SL->{be_sl:.2f} | price={price:.2f} "
                      f"moved=+${moved:.2f}")
                first_print = False

            if not be_set and moved >= threshold:
                pos = br2.positions(symbol)
                match = next((p for p in pos if p.ticket == ticket), None)
                if match is None:
                    print(f"[BE] #{ticket} no longer open (may have TP/SLed). "
                          f"Stopping monitor.")
                    _monitor_stop.set()
                    return
                ok, msg = br2.set_sl(match, sl=be_sl)
                if ok:
                    print(f"[BE] SL MOVED -> {be_sl:.2f} "
                          f"at +${moved:.2f} ({moved/tp_delta*100:.0f}% to TP) "
                          f"[breakeven+spread]")
                    be_set = True
                    _monitor_stop.set()
                    return
                else:
                    print(f"[BE] FAILED: {msg}")
                    time.sleep(0.5)
                    continue

            time.sleep(0.5)
        finally:
            br2.disconnect()
    return be_set


def main() -> int:
    ap = argparse.ArgumentParser(description="Quick scalp — gold or BTC")
    ap.add_argument("--side", required=True, choices=["BUY", "SELL"])
    ap.add_argument("--risk", type=float, required=True,
                    help="Max dollar amount you're willing to risk")
    ap.add_argument("--asset", default="XAUUSD", choices=["XAUUSD", "BTCUSD"],
                    help="Instrument (default XAUUSD)")
    ap.add_argument("--tp", type=float, default=None,
                    help="TP distance in points (default: 2.00 gold / 100 BTC)")
    ap.add_argument("--be", action="store_true",
                    help="Spawn BE monitor daemon (moves SL at 60% of TP)")
    ap.add_argument("--symbol", default=None,
                    help="Override MT5 symbol (default auto-detected)")
    args = ap.parse_args()

    side = args.side.upper()
    risk_dollars = args.risk
    use_be = args.be
    asset_key = args.asset.upper()

    cfg = ASSETS[asset_key]
    point_value = cfg["point_value"]
    symbol = args.symbol or cfg["default_symbol"]
    tp_delta = args.tp if args.tp is not None else cfg["default_tp"]

    s = Settings.load()
    br = Bridge(s)
    ok, msg = br.connect()
    if br.is_mock:
        print("[ERROR] Refusing to trade in MOCK mode.")
        return 1
    if not ok:
        print(f"[ERROR] {msg}")
        return 1
    print(f"[LIVE] {msg}")

    tick1 = br.tick(symbol)
    if tick1 is None:
        print(f"[ERROR] No tick for {symbol}")
        br.disconnect()
        return 1

    spread, sl_delta, vol, entry, sl_price, tp_price = _compute(
        tick1, tp_delta, risk_dollars, side, point_value
    )
    if vol is None:
        print(f"[ERROR] Spread ({spread:.2f}) >= TP ({tp_delta:.2f})")
        br.disconnect()
        return 1

    actual_risk = round(sl_delta * point_value * vol, 2)
    acct = br.account()
    equity = round(acct.equity, 2)

    print("")
    print(f"  Asset:       {asset_key}")
    print(f"  Side:        {side}")
    print(f"  Spread:      ${spread:.2f}")
    print(f"  TP delta:    ${tp_delta:.2f}   SL delta:  ${sl_delta:.2f}")
    print(f"  Entry:       {entry:.2f}  (ask={tick1.ask:.2f} / bid={tick1.bid:.2f})")
    print(f"  TP:          {tp_price:.2f}  (+${tp_delta:.2f})")
    print(f"  SL:          {sl_price:.2f}  (-${sl_delta:.2f})")
    print(f"  Volume:      {vol}")
    print(f"  Risk:        ${actual_risk:.2f}")
    print(f"  Account eq:  ${equity:.2f}")
    if use_be:
        print(f"  Breakeven:   YES -> SL moves to {_be_price(entry, spread, side):.2f}")
    print("")

    # ---- Fire immediately (re-fetch tick) ----
    tick2 = br.tick(symbol)
    if tick2 is None:
        print("[ERROR] Lost tick. Aborting.")
        br.disconnect()
        return 1

    spread2, sl_delta2, vol2, entry2, sl2, tp2 = _compute(
        tick2, tp_delta, risk_dollars, side, point_value
    )
    if vol2 is None:
        print(f"[ERROR] Spread widened to {spread2:.2f} (>= {tp_delta:.2f}). Aborting.")
        br.disconnect()
        return 1

    print(f"[FIRING] entry: {entry2:.2f}, SL: {sl2:.2f}, TP: {tp2:.2f}")

    ok, ticket, note = br.open_order(
        symbol, side, vol2, sl=sl2, tp=tp2,
        comment=f"{side} {asset_key} ({tp_delta})"
    )

    if not ok:
        print(f"[FAIL] {note}")
        br.disconnect()
        return 1

    print(f"[OK] #{ticket} {side} {vol2} {symbol} | Entry={entry2:.2f} SL={sl2:.2f} TP={tp2:.2f}")

    if use_be and ticket is not None:
        print("")
        t = threading.Thread(
            target=_monitor_be,
            args=(s, s.mt5_host, s.mt5_port, symbol, side,
                  entry2, tp_delta, spread2, ticket),
            daemon=True,
        )
        t.start()
        print("[BE] Monitor started (Ctrl-C to stop)")
        print("")

        try:
            while t.is_alive():
                t.join(1)
        except KeyboardInterrupt:
            _monitor_stop.set()
            print("\n[BE] Shutting down...")
            t.join(timeout=3)

    br.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
