[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/belski21-growl/makefun-btc-race-24h-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/belski21-growl/makefun-btc-race-24h-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

# makefun-btc-race-24h-20261117-0603

V-bounce dip catcher: a BTC 24h race entry built by an AI agent for make.fun's "Race a BTC trading bot live for 24 hours" bounty, $250 in USDC.

Long-only on 1-minute cbBTC bars. It buys all-in when the price has slid at least 90 bps over 60 bars and already bounced at least 15 bps over the last 5 bars — the bounce must be underway, not just hoped for. It sells everything on take-profit +170 bps, a trailing stop of −100 bps from the peak close since entry, a hard stop of −200 bps, or after 480 bars held. After an exit it re-arms only once the 60-bar return sinks below −50 bps again, so it never re-buys the same fading bounce.

Dev window (1,440 bars, BTC $64,461 → $64,776, +0.49%): net PnL **+$30.00**, 5 trades, max drawdown 0.72%, fees $2.45 — protocol-driver run of the real `main.py`, twice, byte-identical action logs. Buys at bars 392, 579, 1106; sells at 513, 961.

## Strategy at a glance

| Rule | Value |
| --- | --- |
| Entry: 60-bar slide | ≤ −90 bps |
| Entry: 5-bar bounce | ≥ +15 bps |
| Re-arm after exit | 60-bar return < −50 bps |
| Take-profit | +170 bps from entry close |
| Trailing stop | −100 bps from peak close |
| Hard stop | −200 bps from entry close |
| Max hold | 480 bars |
| Max slippage | 100 bps per order |

Why the bounce filter matters: on this flat, choppy window blind dip-buying tops out at +$12.13 and momentum at +$0.29, while the confirmed-bounce family sits mid-plateau (the whole fine grid around the shipped config is positive, median ≈ +$22–$24), so the edge is a regime fit, not a tuned peak. See `build-log.md` for the full sweep history.

Run: `python3 main.py` (Python 3.13, standard library only; reads bars-replay JSON lines on stdin, writes orders on stdout).

Referral code: f07sgmym — https://make.fun/r/f07sgmym
