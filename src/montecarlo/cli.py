"""Command-line entry point: `python -m montecarlo --ticker AAPL --strike 230`."""

from __future__ import annotations

import argparse
import sys

from .market_data import known_tickers, lookup
from .pricer import MonteCarloParams, black_scholes_price, price_european_option


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="montecarlo",
        description="Monte Carlo European option pricer — run it for whatever ticker/strike/date you want.",
    )
    ticker_group = parser.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument(
        "--ticker",
        help=f"Built-in snapshot ticker (offline demo data): {', '.join(known_tickers())}",
    )
    ticker_group.add_argument(
        "--spot",
        type=float,
        help="Spot price, if not using --ticker. Requires --volatility too.",
    )
    parser.add_argument("--volatility", type=float, help="Annualized volatility (required with --spot)")
    parser.add_argument("--strike", type=float, required=True, help="Strike price")
    parser.add_argument("--rate", type=float, default=0.04, help="Risk-free rate, annualized (default 0.04)")
    parser.add_argument(
        "--maturity", type=float, default=1.0, dest="maturity_years", help="Time to expiry in years (default 1.0)"
    )
    parser.add_argument("--type", choices=["call", "put"], default="call", dest="option_type")
    parser.add_argument("--paths", type=int, default=200_000, dest="n_paths", help="Number of Monte Carlo paths")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed, for reproducible runs")
    parser.add_argument(
        "--compare-black-scholes",
        action="store_true",
        help="Also print the closed-form Black-Scholes price, for a sanity check against the simulation",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.ticker:
        try:
            snap = lookup(args.ticker)
        except KeyError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        spot, volatility, label = snap.spot, snap.volatility, snap.symbol
    else:
        if args.volatility is None:
            print("error: --volatility is required when using --spot", file=sys.stderr)
            return 1
        spot, volatility, label = args.spot, args.volatility, "custom"

    params = MonteCarloParams(
        spot=spot,
        strike=args.strike,
        rate=args.rate,
        volatility=volatility,
        maturity_years=args.maturity_years,
        option_type=args.option_type,
        n_paths=args.n_paths,
        seed=args.seed,
    )

    result = price_european_option(params)

    print(f"symbol:          {label}")
    print(f"spot:            {spot:.2f}")
    print(f"strike:          {params.strike:.2f}")
    print(f"volatility:      {volatility:.4f}")
    print(f"rate:            {params.rate:.4f}")
    print(f"maturity (yrs):  {params.maturity_years:.4f}")
    print(f"option type:     {params.option_type}")
    print(f"paths:           {params.n_paths:,}")
    print(f"MC price:        {result.price:.4f}")
    print(f"std error:       {result.std_error:.4f}")
    print(f"95% CI:          [{result.ci95_low:.4f}, {result.ci95_high:.4f}]")

    if args.compare_black_scholes:
        bs_price = black_scholes_price(params)
        print(f"Black-Scholes:   {bs_price:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
