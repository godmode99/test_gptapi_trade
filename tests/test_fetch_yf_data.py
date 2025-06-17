import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch.fetch_yf_data import fetch_multi_tf


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
    with patch("scripts.fetch.fetch_yf_data.yf.download", side_effect=_fake_download):
        df = fetch_multi_tf("TEST", config, tz_shift=0)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_tz_shift_applied() -> None:
    """Timestamps should shift by the tz_shift value."""
    config = {"fetch_bars": 5, "timeframes": [{"tf": "M1", "keep": 5}]}
    with patch("scripts.fetch.fetch_yf_data.yf.download", side_effect=_fake_download):
        df = fetch_multi_tf("TEST", config, tz_shift=3)

    expected = pd.date_range("2024-01-01", periods=5, freq="min") + pd.Timedelta(
        hours=3
    )
    assert list(df["timestamp"]) == list(expected)
