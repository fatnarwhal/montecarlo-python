# montecarlo-python

A Monte Carlo European option pricer: pick a ticker (or your own
spot/volatility), a strike, and a date, and run it. This is the
"parameterized tool" half of FatNarwhal's language-starter series — unlike
the [SPSC/tick-decoder latency kernels](https://github.com/fatnarwhal/spsc-tickdecoder-c)
(same fixed benchmark, compare the numbers across languages), the point
here is that *you* pick the input. See plan-14 §5c in FatNarwhal's internal
planning docs for the full framing.

**Try it live on FatNarwhal:** yes, today — Python already runs in Tusk's
browser tier (Pyodide), so this is a real "clone it from GitHub, or run it
live on the site for AAPL/TSLA/whatever you want" example from day one, not
a "coming soon."

## Install

```sh
pip install -e ".[dev]"
```

## Run it

```sh
python -m montecarlo --ticker AAPL --strike 230 --compare-black-scholes
```

```
symbol:          AAPL
spot:            225.00
strike:          230.00
volatility:      0.2800
rate:            0.0400
maturity (yrs):  1.0000
option type:     call
paths:           200,000
MC price:        26.9591
std error:       0.1010
95% CI:          [26.7611, 27.1570]
Black-Scholes:   26.8881
```

Or supply your own spot/volatility instead of a built-in ticker snapshot:

```sh
python -m montecarlo --spot 80 --volatility 0.30 --strike 85 --maturity 0.5 --type put
```

Run `python -m montecarlo --help` for every flag (rate, maturity, path
count, seed, option type).

## What's here

- `src/montecarlo/pricer.py` — the Monte Carlo engine (samples the terminal
  price directly from its known lognormal distribution under GBM — correct
  and cheap for a plain European option) plus a closed-form Black-Scholes
  price used only to validate the simulator.
- `src/montecarlo/market_data.py` — a tiny **offline, static snapshot** of a
  few tickers (AAPL, TSLA, MSFT, SPY) so `--ticker` works without a network
  call. This is the intended extension point: swap `lookup()` for a real
  feed (FatNarwhal's own `/data` market API, yfinance, whatever you have)
  to price against live data instead of the illustrative snapshot values
  baked in here.
- `src/montecarlo/cli.py` — the `python -m montecarlo` command.
- `tests/test_pricer.py` — the correctness check that matters: Monte Carlo
  price vs. closed-form Black-Scholes, within a few standard errors, across
  calls and puts, plus edge cases (zero volatility, deep ITM/OTM).

## Design notes

- **Why sample S_T directly instead of simulating a full price path?** A
  plain European option's payoff only depends on the terminal price, and
  under GBM that terminal price has a known lognormal distribution — so
  drawing directly from it is both correct and far cheaper than stepping
  through time. An Asian or barrier option *would* need the full path;
  that's a natural next exercise if you fork this repo.
- **Why validate against Black-Scholes instead of just "it doesn't crash"?**
  Silent pricing bugs (wrong drift term, payoff swapped between call/put,
  discounting applied twice) are exactly the kind of thing that looks fine
  in a demo and is wrong in production. Cross-checking against a known
  closed form is the standard way to catch that class of bug.

## License

MIT — see [`LICENSE`](./LICENSE). Fork it, swap the payoff, swap the data
source, price whatever you want.
