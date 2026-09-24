#!/usr/bin/env python3
"""Set stop loss and/or take profit on all open positions of a symbol (default: XAUUSDp)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings
from mt5_bridge import Bridge


def set_sl_tp_for_symbol(symbol: str = "XAUUSDp", sl: float = None, tp: float = None):
    """Set SL and/or TP on all open positions of a symbol."""
    if sl is None and tp is None:
        print("❌ Must specify at least one of --sl, --tp, or --tp-only.")
        sys.exit(1)

    s = Settings()
    bridge = Bridge(s)

    ok, msg = bridge.connect()
    if not ok:
        print(f"[ERROR] {msg}")
        sys.exit(1)

    print(f"🔗 {msg}")

    positions = bridge.positions(symbol)
    if not positions:
        for suffix in ("p", "r", "m", ".pro", ".raw"):
            alt = symbol + suffix
            positions = bridge.positions(alt)
            if positions:
                print(f"💡 No positions for {symbol}, but found {len(positions)} under {alt}")
                break

    if not positions:
        print(f"❌ No open positions for {symbol}")
        bridge.disconnect()
        sys.exit(1)

    parts = []
    if sl is not None:
        parts.append(f"SL to {sl}")
    if tp is not None:
        parts.append(f"TP to {tp}")

    print(f"📍 Found {len(positions)} position(s) for {symbol}")
    print(f"   Setting {' / '.join(parts)}")
    print("")

    updated = 0
    for pos in positions:
        ok, msg = bridge.set_sl(pos, sl, tp)
        status = "✅" if ok else "❌"
        print(f"{status} Ticket #{pos.ticket}: {msg}")
        if ok:
            updated += 1

    print(f"\n✅ Updated {updated} position(s)")
    bridge.disconnect()


def parse_legacy(argv: list[str]) -> tuple[str, float | None, float | None] | None:
    """Try legacy positional mode: set_sl.py <SL> [SYMBOL] [TP]."""
    if len(argv) < 2:
        return None
    try:
        sl = float(argv[1])
    except ValueError:
        return None

    symbol = "XAUUSDp"
    tp = None

    if len(argv) > 2:
        # If argv[2] is a number, it's TP (no symbol given)
        try:
            tp = float(argv[2])
        except ValueError:
            symbol = argv[2]
            if len(argv) > 3:
                tp = float(argv[3])

    return symbol, sl, tp


def _try_float(s: str) -> float | None:
    try:
        return float(s)
    except ValueError:
        return None


def parse_flags(argv: list[str]) -> tuple[str, float | None, float | None] | None:
    """Parse --sl X --tp Y --tp-only Z [SYMBOL]."""
    symbol = "XAUUSDp"
    sl = None
    tp = None
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in ("--sl", "--tp", "--tp-only"):
            flag = arg
            i += 1
            if i >= len(argv):
                break
            v = _try_float(argv[i])
            if v is not None:
                if flag == "--sl":
                    sl = v
                elif flag == "--tp":
                    tp = v
                elif flag == "--tp-only":
                    tp = v
                    sl = None
                i += 1
            else:
                symbol = argv[i]
                i += 1
                if i < len(argv):
                    v2 = _try_float(argv[i])
                    if v2 is not None:
                        if flag == "--sl":
                            sl = v2
                        elif flag == "--tp":
                            tp = v2
                        elif flag == "--tp-only":
                            tp = v2
                            sl = None
                        i += 1
            continue
        if not arg.startswith("-"):
            v = _try_float(arg)
            if v is not None:
                if sl is None:
                    sl = v
                elif tp is None:
                    tp = v
            else:
                symbol = arg
            i += 1
            continue
        return None

    if sl is None and tp is None:
        return None
    return symbol, sl, tp


def main():
    if len(sys.argv) < 2:
        print("Usage: set_sl.py <SL> [SYMBOL] [TP]")
        print("       set_sl.py --sl <PRICE> [--tp <PRICE>] [--tp-only <PRICE>] [SYMBOL]")
        print("")
        print("Examples:")
        print("  set_sl.py 4050                       # Set SL=4050 on all XAUUSDp")
        print("  set_sl.py 4050 XAUUSDp 4100          # Set SL=4050, TP=4100")
        print("  set_sl.py --sl 4050                  # Set SL=4050")
        print("  set_sl.py --tp-only 4100             # Set only TP=4100")
        print("  set_sl.py --sl 4050 --tp 4100        # Set SL=4050, TP=4100")
        sys.exit(1)

    # Try legacy mode first, then flag mode
    result = parse_legacy(sys.argv) or parse_flags(sys.argv)

    if result is None:
        print("❌ Invalid arguments. Run without args for help.")
        sys.exit(1)

    symbol, sl, tp = result
    set_sl_tp_for_symbol(symbol, sl, tp)


if __name__ == "__main__":
    main()