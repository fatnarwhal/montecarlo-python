"""A tiny built-in market-data stand-in, so `--ticker AAPL` works offline
(no network calls, nothing to mock in CI). This is deliberately a static
snapshot, not a live feed — swap `lookup()` for a real data source (the
FatNarwhal `/data` market-data API, yfinance, whatever you have) when you
run this for real. That's the intended extension point: everything else in
this repo (the Monte Carlo engine, the CLI) is agnostic to where spot/vol
come from.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TickerSnapshot:
    symbol: str
    spot: float
    volatility: float  # annualized
    dividend_yield: float = 0.0


# Illustrative snapshot values, not live quotes.
_SNAPSHOTS = {
    "AAPL": TickerSnapshot("AAPL", spot=225.00, volatility=0.28, dividend_yield=0.005),
    "TSLA": TickerSnapshot("TSLA", spot=250.00, volatility=0.55, dividend_yield=0.0),
    "MSFT": TickerSnapshot("MSFT", spot=420.00, volatility=0.24, dividend_yield=0.007),
    "SPY": TickerSnapshot("SPY", spot=560.00, volatility=0.16, dividend_yield=0.013),
}


def lookup(ticker: str) -> TickerSnapshot:
    """Look up a built-in snapshot by ticker (case-insensitive).

    Raises KeyError with the list of known tickers if not found — callers
    (the CLI) turn that into a friendly error message.
    """
    key = ticker.upper()
    if key not in _SNAPSHOTS:
        known = ", ".join(sorted(_SNAPSHOTS))
        raise KeyError(f"unknown ticker {ticker!r}; built-in snapshots: {known}")
    return _SNAPSHOTS[key]


def known_tickers() -> list[str]:
    return sorted(_SNAPSHOTS)
