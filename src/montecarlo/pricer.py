"""Monte Carlo pricer for a European call/put under geometric Brownian
motion (Black-Scholes dynamics), plus the closed-form Black-Scholes price
used to validate the simulation. This is the parameterized-tool half of
FatNarwhal's language-starter series (see SPEC.md's §5 note, and plan-14
§5c): unlike the SPSC latency kernels, the point here isn't a fixed
benchmark — it's "run this for whatever company/strike/date you want."
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np

OptionType = Literal["call", "put"]


@dataclass(frozen=True)
class MonteCarloParams:
    spot: float
    strike: float
    rate: float  # annualized risk-free rate, continuously compounded
    volatility: float  # annualized
    maturity_years: float
    option_type: OptionType = "call"
    dividend_yield: float = 0.0
    n_paths: int = 200_000
    seed: int | None = 42

    def __post_init__(self) -> None:
        if self.spot <= 0:
            raise ValueError("spot must be positive")
        if self.strike <= 0:
            raise ValueError("strike must be positive")
        if self.volatility < 0:
            raise ValueError("volatility must be non-negative")
        if self.maturity_years <= 0:
            raise ValueError("maturity_years must be positive")
        if self.n_paths <= 0:
            raise ValueError("n_paths must be positive")
        if self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'")


@dataclass(frozen=True)
class PriceResult:
    price: float
    std_error: float
    ci95_low: float
    ci95_high: float
    n_paths: int


def price_european_option(params: MonteCarloParams) -> PriceResult:
    """Single-step terminal-value Monte Carlo: since the payoff only depends
    on the terminal price under GBM, we can sample S_T directly from its
    known lognormal distribution rather than simulating a full path — this
    is both correct and much cheaper than a step-by-step simulation for a
    plain European option (an Asian or barrier option would need the full
    path; that's a natural next exercise if you fork this).
    """
    rng = np.random.default_rng(params.seed)

    drift = (params.rate - params.dividend_yield - 0.5 * params.volatility**2) * params.maturity_years
    diffusion = params.volatility * math.sqrt(params.maturity_years)

    z = rng.standard_normal(params.n_paths)
    s_t = params.spot * np.exp(drift + diffusion * z)

    if params.option_type == "call":
        payoffs = np.maximum(s_t - params.strike, 0.0)
    else:
        payoffs = np.maximum(params.strike - s_t, 0.0)

    discount = math.exp(-params.rate * params.maturity_years)
    discounted = discount * payoffs

    price = float(np.mean(discounted))
    std_error = float(np.std(discounted, ddof=1) / math.sqrt(params.n_paths))
    ci_half_width = 1.96 * std_error

    return PriceResult(
        price=price,
        std_error=std_error,
        ci95_low=price - ci_half_width,
        ci95_high=price + ci_half_width,
        n_paths=params.n_paths,
    )


def black_scholes_price(params: MonteCarloParams) -> float:
    """Closed-form Black-Scholes price, used only to validate the Monte
    Carlo engine (see tests/test_pricer.py) — not something you'd need in
    production once you trust the simulator, but it's the standard sanity
    check for any option Monte Carlo, and it's what lets this repo assert
    correctness rather than just "it ran without crashing."
    """
    s, k, r, sigma, t = (
        params.spot,
        params.strike,
        params.rate,
        params.volatility,
        params.maturity_years,
    )
    q = params.dividend_yield

    if sigma == 0:
        forward = s * math.exp((r - q) * t)
        intrinsic = max(forward - k, 0.0) if params.option_type == "call" else max(k - forward, 0.0)
        return math.exp(-r * t) * intrinsic

    d1 = (math.log(s / k) + (r - q + 0.5 * sigma**2) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)

    def _norm_cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    if params.option_type == "call":
        return s * math.exp(-q * t) * _norm_cdf(d1) - k * math.exp(-r * t) * _norm_cdf(d2)
    else:
        return k * math.exp(-r * t) * _norm_cdf(-d2) - s * math.exp(-q * t) * _norm_cdf(-d1)
