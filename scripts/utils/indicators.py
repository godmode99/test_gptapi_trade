"""Common financial indicator calculations."""
from __future__ import annotations

import pandas as pd


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with ATR14, RSI14 and SMA20 columns added."""
    df = df.copy()

    # Average True Range (ATR14)
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    df["atr14"] = tr.rolling(window=14).mean()

    # Relative Strength Index (RSI14)
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["rsi14"] = 100 - 100 / (1 + rs)

    # Simple Moving Average (SMA20)
    df["sma20"] = df["close"].rolling(window=20).mean()

    return df
