"""Common financial indicator calculations."""
from __future__ import annotations

import pandas as pd


def compute_indicators(
    df: pd.DataFrame,
    indicators: dict[str, bool] | None = None,
) -> pd.DataFrame:
    """Return a copy of *df* with indicator columns added.

    Parameters
    ----------
    df:
        Input OHLCV DataFrame.
    indicators:
        Optional mapping controlling which indicators to compute. Supported keys
        are ``"atr14"``, ``"rsi14"``, ``"sma20"``, ``"ema50"`` and ``"sma200"``.
        Missing keys default to ``True``.
    """

    if indicators is None:
        indicators = {}

    df = df.copy()

    if indicators.get("atr14", True):
        prev_close = df["close"].shift(1)
        tr = pd.concat(
            [
                df["high"] - df["low"],
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        df["atr14"] = tr.rolling(window=14).mean()

    if indicators.get("rsi14", True):
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df["rsi14"] = 100 - 100 / (1 + rs)

    if indicators.get("sma20", True):
        df["sma20"] = df["close"].rolling(window=20).mean()

    if indicators.get("ema50", False):
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    if indicators.get("sma200", False):
        df["sma200"] = df["close"].rolling(window=200).mean()

    return df

