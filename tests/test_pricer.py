import math

import pytest

from montecarlo.market_data import known_tickers, lookup
from montecarlo.pricer import MonteCarloParams, black_scholes_price, price_european_option


def test_params_validate_positive_spot():
    with pytest.raises(ValueError):
        MonteCarloParams(spot=-1, strike=100, rate=0.04, volatility=0.2, maturity_years=1.0)


def test_params_validate_option_type():
    with pytest.raises(ValueError):
        MonteCarloParams(spot=100, strike=100, rate=0.04, volatility=0.2, maturity_years=1.0, option_type="straddle")  # type: ignore[arg-type]


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_monte_carlo_matches_black_scholes(option_type):
    """The core correctness check: with enough paths, the Monte Carlo price
    should land within a few standard errors of the closed-form price."""
    params = MonteCarloParams(
        spot=100.0,
        strike=105.0,
        rate=0.03,
        volatility=0.25,
        maturity_years=0.75,
        option_type=option_type,
        n_paths=500_000,
        seed=7,
    )
    result = price_european_option(params)
    bs_price = black_scholes_price(params)

    # Allow a generous 5-standard-error band so this isn't a flaky test,
    # while still catching a genuinely broken pricer (wrong drift, wrong
    # discounting, payoff swapped, etc).
    assert abs(result.price - bs_price) < 5 * result.std_error


def test_zero_volatility_is_deterministic_and_matches_intrinsic():
    """With zero vol, S_T is deterministic; MC and Black-Scholes should
    both collapse to the discounted forward intrinsic value."""
    params = MonteCarloParams(
        spot=100.0, strike=90.0, rate=0.05, volatility=0.0, maturity_years=1.0, option_type="call", n_paths=1000
    )
    result = price_european_option(params)
    bs_price = black_scholes_price(params)
    assert result.std_error == pytest.approx(0.0, abs=1e-9)
    assert result.price == pytest.approx(bs_price, abs=1e-6)


def test_deep_itm_put_is_worth_near_intrinsic():
    params = MonteCarloParams(
        spot=50.0, strike=200.0, rate=0.02, volatility=0.2, maturity_years=0.25, option_type="put", n_paths=200_000, seed=1
    )
    result = price_european_option(params)
    intrinsic = math.exp(-params.rate * params.maturity_years) * (params.strike - params.spot)
    assert result.price == pytest.approx(intrinsic, rel=0.02)


def test_reproducible_with_fixed_seed():
    params = MonteCarloParams(spot=100.0, strike=100.0, rate=0.04, volatility=0.2, maturity_years=1.0, seed=123, n_paths=10_000)
    r1 = price_european_option(params)
    r2 = price_european_option(params)
    assert r1.price == r2.price


def test_known_tickers_lookup():
    for ticker in known_tickers():
        snap = lookup(ticker)
        assert snap.spot > 0
        assert snap.volatility > 0


def test_unknown_ticker_raises():
    with pytest.raises(KeyError):
        lookup("NOT_A_REAL_TICKER")
