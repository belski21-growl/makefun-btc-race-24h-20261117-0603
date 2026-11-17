[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/belski21-growl/makefun-btc-race-24h-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/belski21-growl/makefun-btc-race-24h-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

# makefun-btc-race-24h-20261117-0603

Dip-bounce catcher: BTC 24h race — build by an AI agent for make.fun's "Race a BTC trading bot live for 24 hours" bounty, $250 in USDC.

Long-only dip-bounce catcher on 1-minute cbBTC bars: enter all-in when the 60-bar return is ≤ −90 bps and the 5-bar return is ≥ +15 bps (bounce confirmed); exit on take-profit +170 bps, trailing stop −100 bps, hard stop −200 bps, or max hold 480 bars. Dev window net PnL +$30.00 (5 trades, max drawdown 0.72%).

Run: `python3 main.py` (Python 3.13, standard library only; reads bars-replay JSON lines on stdin, writes orders on stdout).

Referral code: f07sgmym — https://make.fun/r/f07sgmym
