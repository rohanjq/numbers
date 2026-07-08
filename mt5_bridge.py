"""MT5 access over the mt5linux rpyc bridge, with a mock fallback for dev.

    from mt5linux import MetaTrader5
    mt5 = MetaTrader5(host="localhost", port=8001)
    mt5.initialize()

Read positions / P/L, compute position averages, set SL/TP, close positions.
Uses ORDER_FILLING_FOK (no autodetect, no retries).
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from config import Settings


# ------------------------------------------------------------------ mock
class _MockMT5:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6
    ORDER_TIME_GTC = 0
    ORDER_FILLING_FOK = 2
    TRADE_RETCODE_DONE = 10009

    def __init__(self):
        self._prices = {"XAUUSD": 2350.0, "BTCUSD": 68000.0}
        self._balance = 65.0  # ~6.5% of a 1000 capital sits in MT5
        self._ticket = 70000
        self._positions: List[SimpleNamespace] = [
            SimpleNamespace(ticket=70001, symbol="XAUUSD", type=0, volume=0.02,
                            price_open=2348.5, sl=0.0, tp=0.0, profit=3.0),
            SimpleNamespace(ticket=70002, symbol="XAUUSD", type=0, volume=0.01,
                            price_open=2351.0, sl=0.0, tp=0.0, profit=-1.0),
        ]

    def initialize(self, *a, **k): return True
    def login(self, *a, **k): return True
    def last_error(self): return (0, "ok (mock)")
    def symbol_select(self, *a, **k): return True

    def _px(self, symbol):
        self._prices[symbol] = self._prices.get(symbol, 100.0) + 0.1
        return self._prices[symbol]

    def account_info(self):
        eq = self._balance + sum(p.profit for p in self._positions)
        return SimpleNamespace(login=99999999, balance=round(self._balance, 2),
                               equity=round(eq, 2), margin=0.0,
                               margin_free=round(eq, 2), leverage=800,
                               currency="USD", profit=round(eq - self._balance, 2))

    def symbol_info_tick(self, symbol):
        p = self._px(symbol)
        return SimpleNamespace(bid=round(p - 0.1, 2), ask=round(p + 0.1, 2),
                               last=p, time=int(time.time()))

    def positions_get(self, symbol=None):
        return [p for p in self._positions if symbol is None or p.symbol == symbol]

    def order_send(self, request):
        act = request.get("action")
        if act == self.TRADE_ACTION_SLTP:
            for p in self._positions:
                if p.ticket == request.get("position"):
                    p.sl = request.get("sl", p.sl)
                    p.tp = request.get("tp", p.tp)
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE,
                                   order=request.get("position"),
                                   comment="sltp (mock)")
        if request.get("position"):
            for p in list(self._positions):
                if p.ticket == request["position"]:
                    self._balance += p.profit
                    self._positions.remove(p)
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE,
                                   order=request["position"], comment="close (mock)")
        self._ticket += 1
        return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE,
                               order=self._ticket, comment="deal (mock)")

    def shutdown(self): return True


# ------------------------------------------------------------------ bridge
class Bridge:
    def __init__(self, settings: Settings):
        self.s = settings
        self.mt5: Any = None
        self.is_mock = False
        self.connected = False
        self._lock = threading.RLock()

    def connect(self) -> tuple[bool, str]:
        try:
            from mt5linux import MetaTrader5  # type: ignore
        except Exception:
            self.mt5 = _MockMT5()
            self.is_mock = True
            self.connected = self.mt5.initialize()
            return True, "Connected in MOCK mode (mt5linux not installed)."
        try:
            self.mt5 = MetaTrader5(host=self.s.mt5_host, port=self.s.mt5_port)
            if not self.mt5.initialize():
                code, msg = self.mt5.last_error()
                return False, f"initialize() failed: {code} {msg}"
            for sym in self.s.symbols:
                self.mt5.symbol_select(sym, True)
            self.connected = True
            return True, f"Connected to MT5 {self.s.mt5_host}:{self.s.mt5_port}."
        except Exception as exc:  # noqa: BLE001
            return False, f"MT5 connection error: {exc}"

    # ---- reads ----
    def account(self):
        with self._lock:
            return self.mt5.account_info()

    def tick(self, symbol: str):
        with self._lock:
            return self.mt5.symbol_info_tick(symbol)

    def positions(self, symbol: Optional[str] = None) -> List[Any]:
        try:
            with self._lock:
                return list(self.mt5.positions_get(symbol=symbol) or [])
        except Exception:
            return []

    def running_pnl(self, symbol: Optional[str] = None) -> float:
        return round(sum(getattr(p, "profit", 0.0) for p in self.positions(symbol)), 2)

    def position_averages(self, symbol: Optional[str] = None) -> Dict[str, dict]:
        """Volume-weighted average entry per symbol+side across open positions."""
        groups: Dict[tuple, list] = defaultdict(list)
        for p in self.positions(symbol):
            side = "BUY" if p.type == self.mt5.ORDER_TYPE_BUY else "SELL"
            groups[(p.symbol, side)].append(p)
        out: Dict[str, dict] = {}
        for (sym, side), items in groups.items():
            vol = sum(i.volume for i in items)
            avg = sum(i.price_open * i.volume for i in items) / vol if vol else 0.0
            out[f"{sym}:{side}"] = {
                "symbol": sym, "side": side, "positions": len(items),
                "total_volume": round(vol, 3), "avg_entry": round(avg, 2),
                "pnl": round(sum(i.profit for i in items), 2),
                "tickets": [i.ticket for i in items],
            }
        return out

    # ---- writes ----
    def set_sl(self, position, sl: float, tp: Optional[float] = None) -> tuple[bool, str]:
        req = {
            "action": self.mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": int(position.ticket),
            "sl": float(sl),
            "tp": float(tp) if tp is not None else float(getattr(position, "tp", 0.0)),
        }
        with self._lock:
            r = self.mt5.order_send(req)
        ok = r is not None and r.retcode == self.mt5.TRADE_RETCODE_DONE
        return ok, (f"SL set on #{position.ticket}" if ok
                    else f"failed on #{position.ticket}: {getattr(r, 'comment', r)}")

    def close(self, position) -> tuple[bool, str]:
        is_buy = position.type == self.mt5.ORDER_TYPE_BUY
        tick = self.tick(position.symbol)
        req = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": float(position.volume),
            "type": self.mt5.ORDER_TYPE_SELL if is_buy else self.mt5.ORDER_TYPE_BUY,
            "position": int(position.ticket),
            "price": tick.bid if is_buy else tick.ask,
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_FOK,
        }
        with self._lock:
            r = self.mt5.order_send(req)
        ok = r is not None and r.retcode == self.mt5.TRADE_RETCODE_DONE
        return ok, (f"closed #{position.ticket}" if ok
                    else f"close failed #{position.ticket}: {getattr(r, 'comment', r)}")

    def disconnect(self):
        try:
            if self.mt5:
                self.mt5.shutdown()
        except Exception:
            pass
