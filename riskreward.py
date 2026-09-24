"""Risk:reward calculations.

Two regimes, because this account trades with NO stop loss:

1. Past/backfilled trades (no equity-at-risk on record): R:R = pnl / margin
   required at FULL leverage per instrument — the smallest capital slice
   that could have taken the trade. Per-instrument full leverage:
     gold (XAUUSD/XAUUSDp)  1000x, contract 100 oz
     BTC  (BTCUSD/BTCUSDp)   400x, contract 1
     ETH  (ETHUSD/ETHUSDp)   200x, contract 1

2. Future trades (this account never sets SL): since there's no stop-distance
   to measure risk from, "risk" = the account EQUITY at the moment the trade
   was taken (the capital actually exposed, since a no-SL position can in
   principle draw down the full equity). R:R = pnl / equity_at_trade.
"""
from __future__ import annotations

FULL_LEVERAGE = {
    "XAUUSD": 1000.0, "XAUUSDP": 1000.0,
    "BTCUSD": 400.0, "BTCUSDP": 400.0,
    "ETHUSD": 200.0, "ETHUSDP": 200.0,
}
CONTRACT_SIZE = {
    "XAUUSD": 100.0, "XAUUSDP": 100.0,
    "BTCUSD": 1.0, "BTCUSDP": 1.0,
    "ETHUSD": 1.0, "ETHUSDP": 1.0,
}


def margin_at_full_leverage(symbol: str, volume: float, price: float) -> float:
    sym = symbol.upper()
    contract = CONTRACT_SIZE.get(sym, 100.0)
    leverage = FULL_LEVERAGE.get(sym, 1000.0)
    return round(volume * contract * price / leverage, 2)


def risk_reward(symbol: str, volume: float, entry: float, pnl: float) -> float:
    """Backfilled/past trades: pnl vs margin at full per-instrument leverage."""
    margin = margin_at_full_leverage(symbol, volume, entry)
    return round(pnl / margin, 2) if margin else 0.0


def risk_reward_vs_equity(pnl: float, equity_at_trade: float) -> float:
    """Future trades (no SL set): pnl vs the account equity exposed at entry."""
    return round(pnl / equity_at_trade, 2) if equity_at_trade else 0.0
