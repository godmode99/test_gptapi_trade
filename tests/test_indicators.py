import pandas as pd
from gpt_trader.utils.indicators import compute_indicators


def test_disable_single_indicator():
    df = pd.DataFrame(
        {
            "open": [1, 2, 3],
            "high": [1, 2, 3],
            "low": [1, 2, 3],
            "close": [1, 2, 3],
        }
    )
    out = compute_indicators(df, {"rsi14": False})
    assert "rsi14" not in out.columns
    assert "atr14" in out.columns
    assert "sma20" in out.columns


def test_disable_all_indicators():
    df = pd.DataFrame(
        {
            "open": [1, 2, 3],
            "high": [1, 2, 3],
            "low": [1, 2, 3],
            "close": [1, 2, 3],
        }
    )
    out = compute_indicators(
        df,
        {
            "atr14": False,
            "rsi14": False,
            "sma20": False,
            "ema50": False,
            "sma200": False,
        },
    )
    for col in ["atr14", "rsi14", "sma20", "ema50", "sma200"]:
        assert col not in out.columns


def test_ema50_and_sma200_present():
    df = pd.DataFrame(
        {
            "open": [1, 2, 3, 4, 5],
            "high": [1, 2, 3, 4, 5],
            "low": [1, 2, 3, 4, 5],
            "close": [1, 2, 3, 4, 5],
        }
    )
    out = compute_indicators(df, {"ema50": True, "sma200": True})
    assert "ema50" in out.columns
    assert "sma200" in out.columns

