from montecarlo.cli import main


def test_cli_runs_with_ticker(capsys):
    rc = main(["--ticker", "AAPL", "--strike", "230", "--paths", "5000", "--compare-black-scholes"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "symbol:          AAPL" in out
    assert "MC price:" in out
    assert "Black-Scholes:" in out


def test_cli_runs_with_custom_spot(capsys):
    rc = main(["--spot", "80", "--volatility", "0.3", "--strike", "85", "--paths", "5000"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "symbol:          custom" in out


def test_cli_rejects_unknown_ticker(capsys):
    rc = main(["--ticker", "NOPE", "--strike", "100"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "unknown ticker" in err


def test_cli_requires_volatility_with_spot(capsys):
    rc = main(["--spot", "80", "--strike", "85"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "--volatility is required" in err
