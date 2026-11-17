# SPDX-License-Identifier: MIT
"""Dip-bounce catcher for btc-race-24h-20261117-0603 (agent-fun/bars-replay/v1).

Long only, full size, few trades. Python 3.13 stdlib only; speaks the
protocol through the kit's own vendor/makefun_bars.py shim.

Idea: this dev window is flat and choppy (BTC $64,461 -> $64,776, +0.49%,
buy-and-hold +$1.07) with two sharp V-bounces off intraday lows. Blind
dip-buying and momentum both lose here (momentum best +$0.29 of 240
configs; fade/buy-while-falling best +$12.13), so the entry demands BOTH
a real slide AND a bounce that has actually started, then exits on
take-profit or a trailing stop.

Entry (all cash, one position at a time):
  - 60-bar return <= -90 bps (a real slide, not noise), AND
  - 5-bar return >= +15 bps (the bounce is underway), AND
  - re-armed (after an exit, the 60-bar return must fall below -50 bps
    again before the next entry, so the bot never re-buys the same fading
    bounce bar after bar).

Exit (whole position):
  - take-profit +170 bps from the entry close, or
  - trailing stop -100 bps from the peak close since entry, or
  - hard stop-loss -200 bps from the entry close (safety net; never binds
    on the dev window), or
  - 480 bars held (safety net only; never binds on the dev window, where
    the longest hold is 382 bars).

Validated on the dev window (1,440 bars, BTC $64,461.04 -> $64,775.95,
+0.49%): net PnL +$30.00, 5 trades (2 round trips + 1 buy flattened at
the end), max drawdown 0.72%, fees $2.45 — protocol-driver run of the
real main.py, twice, byte-identical action logs (buys at bars 392, 579,
1106; sells at 513, 961). The faithful backtester agrees to the cent.

No orders on warm-up batches or on batches with no new CBBTC bar.
Deterministic: integer math only, no clock, no files, no environment,
no randomness (the hello seed is accepted and ignored — nothing here
needs a random draw).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
SLIP_BPS = 100

# Strategy constants (bps; 1 bp = 0.01%).
DROP_LOOKBACK = 60       # bars over which the slide is measured
DROP_BPS = -90           # entry needs a slide at least this deep
CONFIRM_LOOKBACK = 5     # bars over which the bounce is confirmed
CONFIRM_BPS = 15         # entry needs a bounce at least this strong
REARM_BPS = -50          # 60-bar return must fall below this to re-arm
TAKE_PROFIT_BPS = 170    # exit: gain from the entry close
TRAIL_BPS = 100          # exit: fall from the peak close since entry
STOP_LOSS_BPS = 200      # exit: fall from the entry close (safety net)
MAX_HOLD_BARS = 480      # exit: bars held (safety net only)

_closes = []             # CBBTC closes seen so far, in order (ints)
_entry_close = None      # close at the bar the current position appeared
_peak_close = None       # highest close since entry
_hold_bars = 0           # bars held in the current position
_armed = True            # False after an exit until the slide re-arms


def _ret_bps(now, then):
    """Return from `then` to `now` in basis points (integer math)."""
    return (now - then) * 10000 // then


def on_batch(state, batch):
    global _entry_close, _peak_close, _hold_bars, _armed

    if state.warming_up:
        return []
    # Only decide on a batch that carries a fresh CBBTC bar.
    if not any(b.get("symbol") == SYMBOL for b in batch.get("bars", [])):
        return []
    close = state.close(SYMBOL)
    if close is None:
        return []
    _closes.append(close)
    n = len(_closes)

    holding = state.positions.get(SYMBOL)
    if holding is None or holding.qty == 0:
        _entry_close = None
        _peak_close = None
        _hold_bars = 0
        if n < DROP_LOOKBACK + 1:
            return []
        # Re-arm once the slide is deep again.
        if _ret_bps(close, _closes[-DROP_LOOKBACK - 1]) < REARM_BPS:
            _armed = True
        if not _armed:
            return []
        if n < CONFIRM_LOOKBACK + 1:
            return []
        drop = _ret_bps(close, _closes[-DROP_LOOKBACK - 1])
        bounce = _ret_bps(close, _closes[-CONFIRM_LOOKBACK - 1])
        if drop <= DROP_BPS and bounce >= CONFIRM_BPS and state.cash >= 1_000_000:
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": SLIP_BPS}]
        return []

    # Holding: track entry/peak from the bar the position first shows up.
    if _entry_close is None:
        _entry_close = close
    _peak_close = close if _peak_close is None else max(_peak_close, close)
    _hold_bars += 1

    if _ret_bps(close, _entry_close) >= TAKE_PROFIT_BPS:
        _armed = False
        return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                 "max_slippage_bps": SLIP_BPS}]
    if _ret_bps(close, _peak_close) <= -TRAIL_BPS:
        _armed = False
        return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                 "max_slippage_bps": SLIP_BPS}]
    if _ret_bps(close, _entry_close) <= -STOP_LOSS_BPS:
        _armed = False
        return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                 "max_slippage_bps": SLIP_BPS}]
    if _hold_bars >= MAX_HOLD_BARS:
        _armed = False
        return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                 "max_slippage_bps": SLIP_BPS}]
    return []


makefun_bars.run(on_batch)
