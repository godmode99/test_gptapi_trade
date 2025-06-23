import importlib
from types import ModuleType
import json
import logging
import sys
from unittest.mock import patch

import pandas as pd
import pytest



def test_fetch_multi_tf_tz_shift_and_latest_bar() -> None:
    """Ensure timestamps shift and latest bar is included."""
    sample_times = pd.date_range("2024-01-01", periods=5, freq="min")[::-1]
    sample_rates = [
        {
            "time": int(ts.timestamp()),
            "open": i,
            "high": i,
            "low": i,
            "close": i,
            "tick_volume": i,
            "spread": 0,
            "real_volume": 0,
        }
        for i, ts in enumerate(sample_times)
    ]

    mt5 = ModuleType("MetaTrader5")
    mt5.TIMEFRAME_M1 = 1
    mt5.TIMEFRAME_M5 = 2
    mt5.TIMEFRAME_M15 = 3
    mt5.TIMEFRAME_M30 = 4
    mt5.TIMEFRAME_H1 = 5
    mt5.TIMEFRAME_H4 = 6
    mt5.TIMEFRAME_D1 = 7
    mt5.copy_rates_from_pos = lambda *args, **kwargs: sample_rates

    with importlib.import_module("unittest.mock").patch.dict(
        sys.modules, {"MetaTrader5": mt5}
    ):
        fetch_mt5_data = importlib.import_module("gpt_trader.fetch.fetch_mt5_data")
        importlib.reload(fetch_mt5_data)

        config = {"fetch_bars": 5, "timeframes": [{"tf": "M1", "keep": 5}]}
        df = fetch_mt5_data.fetch_multi_tf("TEST", config, tz_shift=2)

    expected_times = pd.date_range("2024-01-01", periods=5, freq="min") + pd.Timedelta(hours=2)
    assert list(df["timestamp"]) == list(expected_times)
    assert df["timestamp"].iloc[-1] == expected_times[-1]
    expected_sessions = [fetch_mt5_data.get_session(ts) for ts in expected_times]
    assert list(df["session"]) == expected_sessions


def test_fetch_multi_tf_with_time_fetch() -> None:
    """Data should end at the configured time_fetch value."""
    sample_times = pd.date_range("2024-01-01", periods=5, freq="min")
    sample_rates = [
        {
            "time": int(ts.timestamp()),
            "open": 0,
            "high": 0,
            "low": 0,
            "close": 0,
            "tick_volume": 0,
            "spread": 0,
            "real_volume": 0,
        }
        for ts in sample_times
    ]
    called: dict = {}

    mt5 = ModuleType("MetaTrader5")
    mt5.TIMEFRAME_M1 = 1
    mt5.TIMEFRAME_M5 = 2
    mt5.TIMEFRAME_M15 = 3
    mt5.TIMEFRAME_M30 = 4
    mt5.TIMEFRAME_H1 = 5
    mt5.TIMEFRAME_H4 = 6
    mt5.TIMEFRAME_D1 = 7

    def _range(symbol: str, tf: int, start, end):
        called["start"] = start
        called["end"] = end
        return sample_rates

    mt5.copy_rates_range = _range

    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        fetch_mt5_data = importlib.import_module("gpt_trader.fetch.fetch_mt5_data")
        importlib.reload(fetch_mt5_data)

        config = {
            "fetch_bars": 5,
            "time_fetch": "2024-01-01 00:04:00",
            "timeframes": [{"tf": "M1", "keep": 5}],
        }
        df = fetch_mt5_data.fetch_multi_tf("TEST", config, tz_shift=0)

    assert list(df["timestamp"]) == list(sample_times)
    assert called["start"].strftime("%Y-%m-%d %H:%M:%S") == "2024-01-01 00:00:00"
    assert called["end"].strftime("%Y-%m-%d %H:%M:%S") == "2024-01-01 00:04:00"
    expected_sessions = [fetch_mt5_data.get_session(ts) for ts in sample_times]
    assert list(df["session"]) == expected_sessions


def test_fetch_multi_tf_invalid_time_fetch() -> None:
    """Invalid timestamps should raise a ValueError."""
    config = {
        "fetch_bars": 5,
        "time_fetch": "not a date",
        "timeframes": [{"tf": "M1", "keep": 5}],
    }
    fetch_mt5_data = importlib.import_module("gpt_trader.fetch.fetch_mt5_data")
    with pytest.raises(ValueError):
        fetch_mt5_data.fetch_multi_tf("TEST", config)


def test_fetch_multi_tf_time_fetch_no_data() -> None:
    """Missing bars for time_fetch should raise a ValueError."""
    mt5 = ModuleType("MetaTrader5")
    mt5.TIMEFRAME_M1 = 1
    mt5.TIMEFRAME_M5 = 2
    mt5.TIMEFRAME_M15 = 3
    mt5.TIMEFRAME_M30 = 4
    mt5.TIMEFRAME_H1 = 5
    mt5.TIMEFRAME_H4 = 6
    mt5.TIMEFRAME_D1 = 7

    def _range(symbol: str, tf: int, start, end):
        return []

    mt5.copy_rates_range = _range

    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        fetch_mt5_data = importlib.import_module("gpt_trader.fetch.fetch_mt5_data")
        importlib.reload(fetch_mt5_data)

        config = {
            "fetch_bars": 5,
            "time_fetch": "2024-01-01 00:00:00",
            "timeframes": [{"tf": "M1", "keep": 5}],
        }
        with pytest.raises(ValueError):
            fetch_mt5_data.fetch_multi_tf("TEST", config, tz_shift=0)


def test_main_error_on_empty_df(tmp_path, caplog) -> None:
    """main() should exit with SystemExit when no data is fetched."""
    cfg = {
        "symbol": "TEST",
        "fetch_bars": 1,
        "timeframes": [{"tf": "M1", "keep": 1}],
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    with patch.object(sys, "argv", ["fetch_mt5_data.py", "--config", str(cfg_path)]), patch(
        "gpt_trader.fetch.fetch_mt5_data.fetch_multi_tf", return_value=pd.DataFrame()
    ), patch("gpt_trader.fetch.fetch_mt5_data._init_mt5"), patch(
        "gpt_trader.fetch.fetch_mt5_data._shutdown_mt5"
    ):
        with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
            importlib.import_module("gpt_trader.fetch.fetch_mt5_data").main()
        assert exc.value.code == 1
        assert "No data available" in caplog.text


def test_main_writes_to_save_as_path(tmp_path) -> None:
    """main() should write CSV to the save_as_path directory."""
    cfg = {
        "symbol": "TEST",
        "fetch_bars": 1,
        "timeframes": [{"tf": "M1", "keep": 1}],
        "save_as_path": str(tmp_path),
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    df = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2024-01-01")],
            "open": [1],
            "high": [1],
            "low": [1],
            "close": [1],
            "tick_volume": [1],
            "atr14": [0],
            "rsi14": [0],
            "sma20": [0],
            "timeframe": ["1m"],
            "session": ["asia"],
        }
    )

    with patch.object(sys, "argv", ["fetch_mt5_data.py", "--config", str(cfg_path)]), patch(
        "gpt_trader.fetch.fetch_mt5_data.fetch_multi_tf",
        return_value=df,
    ), patch("gpt_trader.fetch.fetch_mt5_data._init_mt5"), patch(
        "gpt_trader.fetch.fetch_mt5_data._shutdown_mt5"
    ):
        importlib.import_module("gpt_trader.fetch.fetch_mt5_data").main()

    csv_files = list(tmp_path.glob("*.csv"))
    json_files = list(tmp_path.glob("*.json"))
    assert len(csv_files) == 1
    assert len(json_files) == 1
    assert csv_files[0].is_file()
    assert json_files[0].is_file()

