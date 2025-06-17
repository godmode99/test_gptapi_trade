import sys
import importlib
from types import ModuleType
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


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
        fetch_mt5_data = importlib.import_module("scripts.fetch.fetch_mt5_data")
        importlib.reload(fetch_mt5_data)

        config = {"fetch_bars": 5, "timeframes": [{"tf": "M1", "keep": 5}]}
        df = fetch_mt5_data.fetch_multi_tf("TEST", config, tz_shift=2)

    expected_times = sample_times + pd.Timedelta(hours=2)
    assert list(df["timestamp"]) == list(expected_times)
    assert df["timestamp"].iloc[0] == expected_times[0]
