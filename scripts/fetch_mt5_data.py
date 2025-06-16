"""Fetch OHLCV data from MT5 and compute indicators.

This script connects to the MetaTrader5 terminal, retrieves multiple timeframes
of OHLC data for a given symbol, calculates ATR14, RSI14 and SMA20 for each
timeframe and saves the combined result as a CSV file.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

import pandas as pd
import MetaTrader5 as mt5


LOGGER = logging.getLogger(__name__)


def _init_mt5() -> None:
    """Initialize connection to MetaTrader5."""
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize() failed: {mt5.last_error()}")


def _shutdown_mt5() -> None:
    """Shutdown MetaTrader5 connection."""
    mt5.shutdown()


def _fetch_rates(symbol: str, timeframe: int, bars: int) -> pd.DataFrame:
    """Fetch OHLC data from MT5 for a given timeframe."""
    LOGGER.info("Fetching %s bars for %s timeframe", bars, timeframe)
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None:
        raise RuntimeError(f"Failed to fetch data for {symbol} timeframe {timeframe}")
    df = pd.DataFrame(rates)
    df["timestamp"] = pd.to_datetime(df["time"], unit="s")
    df = df.drop(columns=["time", "spread", "real_volume"], errors="ignore")
    return df


def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute ATR14, RSI14 and SMA20 for the dataframe."""
    df = df.copy()

    # ATR14
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

    # RSI14
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["rsi14"] = 100 - 100 / (1 + rs)

    # SMA20
    df["sma20"] = df["close"].rolling(window=20).mean()

    return df


def fetch_multi_tf(symbol: str) -> pd.DataFrame:
    """Fetch data for several timeframes and merge into one DataFrame."""
    # Bars to keep after indicators are calculated
    timeframes: List[tuple[int, int, str]] = [
        (mt5.TIMEFRAME_M5, 10, "5m"),
        (mt5.TIMEFRAME_M15, 6, "15m"),
        (mt5.TIMEFRAME_H1, 4, "1h"),
    ]
    # Always fetch enough bars to compute indicators (min 20)
    fetch_bars = 20

    frames = []
    for tf, keep, label in timeframes:
        df = _fetch_rates(symbol, tf, fetch_bars)
        df = _compute_indicators(df)
        df = df.tail(keep)
        df["timeframe"] = label
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    # Reorder columns
    cols = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "atr14",
        "rsi14",
        "sma20",
        "timeframe",
    ]
    combined = combined[cols]
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch MT5 OHLC data")
    parser.add_argument("symbol", help="Symbol to fetch", nargs="?", default="EURUSD")
    parser.add_argument(
        "--output",
        help="Output CSV file",
        default=None,
    )

    args = parser.parse_args()

    output = (
        Path(args.output)
        if args.output
        else Path("data/raw") / f"{args.symbol.lower()}_multi_tf.csv"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        _init_mt5()
        df = fetch_multi_tf(args.symbol)
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False)
        LOGGER.info("Saved data to %s", output)
    except Exception as exc:
        LOGGER.error("Error fetching data: %s", exc)
        raise SystemExit(1)
    finally:
        _shutdown_mt5()


if __name__ == "__main__":
    main()
