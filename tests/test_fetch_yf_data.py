from unittest.mock import patch
import json
import logging
import importlib
import sys

import pandas as pd
import pytest

from gpt_trader.fetch.fetch_yf_data import fetch_multi_tf, get_session


def _fake_download(
    symbol: str, interval: str, period: str, progress: bool
) -> pd.DataFrame:
    """Return a small DataFrame for testing."""
    index = pd.date_range("2024-01-01", periods=5, freq="min")
    return pd.DataFrame(
        {
            "Open": range(5),
            "High": range(5),
            "Low": range(5),
            "Close": range(5),
            "Volume": range(5),
        },
        index=index,
    )


def test_fetch_multi_tf_returns_dataframe() -> None:
    config = {"fetch_bars": 5, "timeframes": [{"tf": "M1", "keep": 5}]}
    with patch("gpt_trader.fetch.fetch_yf_data.yf.download", side_effect=_fake_download):
        df = fetch_multi_tf("TEST", config, tz_shift=0)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    expected_sessions = [
        get_session(ts) for ts in pd.date_range("2024-01-01", periods=5, freq="min")
    ]
    assert list(df["session"]) == expected_sessions


def test_tz_shift_applied() -> None:
    """Timestamps should shift by the tz_shift value."""
    config = {"fetch_bars": 5, "timeframes": [{"tf": "M1", "keep": 5}]}
    with patch("gpt_trader.fetch.fetch_yf_data.yf.download", side_effect=_fake_download):
        df = fetch_multi_tf("TEST", config, tz_shift=3)

    expected = pd.date_range("2024-01-01", periods=5, freq="min") + pd.Timedelta(
        hours=3
    )
    assert list(df["timestamp"]) == list(expected)
    expected_sessions = [get_session(ts) for ts in expected]
    assert list(df["session"]) == expected_sessions


def test_fetch_multi_tf_excludes_disabled_indicators() -> None:
    config = {
        "fetch_bars": 3,
        "timeframes": [{"tf": "M1", "keep": 3}],
        "indicators": {"rsi14": False, "atr14": False},
    }
    with patch("gpt_trader.fetch.fetch_yf_data.yf.download", side_effect=_fake_download):
        df = fetch_multi_tf("TEST", config, tz_shift=0)

    assert "rsi14" not in df.columns
    assert "atr14" not in df.columns


def test_main_error_on_empty_df(tmp_path, caplog) -> None:
    """main() should exit when fetch_multi_tf returns no rows."""
    cfg = {
        "symbol": "TEST",
        "fetch_bars": 1,
        "timeframes": [{"tf": "M1", "keep": 1}],
        "save_as_path": str(tmp_path),
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    with patch.object(sys, "argv", ["fetch_yf_data.py", "--config", str(cfg_path)]), patch(
        "gpt_trader.fetch.fetch_yf_data.fetch_multi_tf", return_value=pd.DataFrame()
    ):
        with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
            importlib.import_module("gpt_trader.fetch.fetch_yf_data").main()
        assert exc.value.code == 1
        assert "No data available" in caplog.text
