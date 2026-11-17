# SPDX-License-Identifier: MIT
"""V-bounce dip catcher — btc-race-24h-20261117-0603, agent-fun/bars-replay/v1.

A long-only bot that buys the bounce after a slide instead of catching
the falling knife. It runs on 1-minute cbBTC bars through the kit's own
vendor/makefun_bars.py shim, Python 3.13 stdlib only.

Why this shape: the dev window is flat and choppy (BTC $64,461 -> $64,776,
+0.49%; buy-and-hold only +$1.07) but carries two sharp V-bounces off
intraday lows. Momentum tops out at +$0.29 here and blind dip-buying at
+$12.13, so the bot waits for BOTH a genuine slide and a bounce that has
already begun, then rides it to a fixed target or a trailing stop.

The trade, in plain words:
  * BUY everything when the price has slid at least 90 bps over 60 bars
    and already bounced at least 15 bps over the last 5 bars.
  * SELL everything on the first of: +170 bps from the entry close,
    -100 bps from the best close since entry, -200 bps from entry
    (safety net), or 480 bars held (safety net).
  * After any exit the bot stays flat until the 60-bar return sinks below
    -50 bps again, so it never re-buys the same fading bounce.

Dev-window grade (1,440 bars, protocol driver, real main.py, run twice,
byte-identical action logs): net PnL +$30.00, 5 trades, max drawdown
0.72%, fees $2.45. Buys at bars 392, 579, 1106; sells at 513, 961.

Deterministic by construction: integer arithmetic throughout, no clock,
no files, no environment reads, no randomness (hello.seed is accepted
and ignored).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

ASSET = "CBBTC"
MAX_SLIP = 100  # max_slippage_bps on every order

# Thresholds, in basis points (1 bp = 0.01%).
SLIDE_BARS = 60
SLIDE_MIN = 90        # entry needs a 60-bar slide at least this deep
BOUNCE_BARS = 5
BOUNCE_MIN = 15       # entry needs a 5-bar bounce at least this strong
REARM_DROP = 50       # 60-bar return must fall below -50 bps to re-arm
TARGET_BPS = 170      # exit: gain from the entry close
TRAIL_BPS = 100       # exit: fall from the peak close since entry
STOP_BPS = 200        # exit: fall from the entry close (safety net)
HOLD_LIMIT = 480      # exit: bars held (safety net only)

MIN_CASH = 1_000_000  # 1 USDC, in quote units


def bps_change(new, old):
    """Basis-point move from `old` to `new`, integer math only."""
    return (new - old) * 10000 // old


class DipBounce:
    """Keeps the close history and the position state between batches."""

    def __init__(self):
        self.closes = []
        self.armed = True
        self.entry = None
        self.peak = None
        self.held = 0

    def note_close(self, close):
        self.closes.append(close)
        return len(self.closes)

    def slide(self):
        """60-bar return in bps, or None while the window is not full."""
        if len(self.closes) <= SLIDE_BARS:
            return None
        return bps_change(self.closes[-1], self.closes[-SLIDE_BARS - 1])

    def bounce(self):
        """5-bar return in bps, or None while the window is not full."""
        if len(self.closes) <= BOUNCE_BARS:
            return None
        return bps_change(self.closes[-1], self.closes[-BOUNCE_BARS - 1])

    def flatten(self, state):
        """Reset the position trackers; called whenever we hold nothing."""
        self.entry = None
        self.peak = None
        self.held = 0

    def try_enter(self, state):
        """Buy signal, or None. Only called while flat."""
        self.flatten(state)
        slide = self.slide()
        if slide is None:
            return None
        if slide < -REARM_DROP:
            self.armed = True
        if not self.armed:
            return None
        bounce = self.bounce()
        if bounce is None:
            return None
        if slide <= -SLIDE_MIN and bounce >= BOUNCE_MIN and state.cash >= MIN_CASH:
            return {
                "side": "buy",
                "symbol": ASSET,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIP,
            }
        return None

    def exit_reason(self, close):
        """Why to sell now, or None: target, trailing stop, hard stop, time."""
        gain = bps_change(close, self.entry)
        giveback = bps_change(close, self.peak)
        if gain >= TARGET_BPS:
            return "target"
        if giveback <= -TRAIL_BPS:
            return "trailing"
        if gain <= -STOP_BPS:
            return "stop"
        if self.held >= HOLD_LIMIT:
            return "max-hold"
        return None

    def try_exit(self, state, close, qty):
        """Sell signal, or None. Only called while holding."""
        if self.entry is None:
            self.entry = close
        self.peak = close if self.peak is None else max(self.peak, close)
        self.held += 1
        if self.exit_reason(close) is None:
            return None
        self.armed = False
        return {
            "side": "sell",
            "symbol": ASSET,
            "qty": qty,
            "max_slippage_bps": MAX_SLIP,
        }


BOT = DipBounce()


def on_batch(state, batch):
    if state.warming_up:
        return []
    bars = batch.get("bars", [])
    if not any(bar.get("symbol") == ASSET for bar in bars):
        return []
    close = state.close(ASSET)
    if close is None:
        return []
    BOT.note_close(close)

    position = state.positions.get(ASSET)
    if position is None or position.qty == 0:
        order = BOT.try_enter(state)
        return [] if order is None else [order]

    order = BOT.try_exit(state, close, position.qty)
    return [] if order is None else [order]


makefun_bars.run(on_batch)
