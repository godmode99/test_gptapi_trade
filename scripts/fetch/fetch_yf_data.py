"""Fetch OHLCV data via yfinance and compute indicators."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf

LOGGER = logging.getLogger(__name__)

TF_MAP: Dict[str, str] = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "60m",
    "H4": "240m",
    "D1": "1d",
}


def _load_config(path: Path) -> Dict[str, Any]:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


def _tf_label(tf: str) -> str:
    """Return a human readable label like '5m' for timeframe name."""
    digits = "".join(ch for ch in tf if ch.isdigit())
    letters = "".join(ch for ch in tf if ch.isalpha()).lower()
    return f"{digits}{letters}"


def _timestamp_code(ts: pd.Timestamp) -> str:
    """Return a string like '250616_16H' for a timestamp."""
    return ts.strftime("%d%m%y_%H") + "H"


def _fetch_rates(symbol: str, interval: str, bars: int, tz_shift: int = 0) -> pd.DataFrame:
    """Fetch OHLC data from yfinance."""
    LOGGER.info("Fetching %s bars for %s interval", bars, interval)
    df = yf.download(symbol, interval=interval, period="60d", progress=False)
    if df.empty:
        raise RuntimeError(f"Failed to fetch data for {symbol} interval {interval}")
    df = df.tail(bars)
    idx = pd.to_datetime(df.index)
    if idx.tzinfo is not None:
        idx = idx.tz_convert(None)
    df.index = idx + pd.Timedelta(hours=tz_shift)
    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "tick_volume",
        }
    )
    df = df.reset_index().rename(columns={"index": "timestamp"})
    df = df[["timestamp", "open", "high", "low", "close", "tick_volume"]]
    return df


def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute ATR14, RSI14 and SMA20 for the dataframe."""
    df = df.copy()

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

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["rsi14"] = 100 - 100 / (1 + rs)

    df["sma20"] = df["close"].rolling(window=20).mean()

    return df


def fetch_multi_tf(symbol: str, config: Dict[str, Any], tz_shift: int = 0) -> pd.DataFrame:
    """Fetch data for several timeframes and merge into one DataFrame."""
    timeframes_conf: List[Dict[str, Any]] = config.get("timeframes", [])
    fetch_bars = int(config.get("fetch_bars", 20))

    frames: List[pd.DataFrame] = []
    for item in timeframes_conf:
        tf_name = str(item.get("tf", "")).upper()
        keep = int(item.get("keep", 0))
        interval = TF_MAP.get(tf_name)
        if interval is None:
            raise ValueError(f"Unsupported timeframe: {tf_name}")
        label = _tf_label(tf_name)
        df = _fetch_rates(symbol, interval, fetch_bars, tz_shift)
        df = _compute_indicators(df)
        df = df.tail(keep)
        df["timeframe"] = label
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
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
    return combined[cols]


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument(
        "--config",
        help="Path to JSON config",
        default="config/fetch_yf.json",
    )

    pre_args, remaining = pre_parser.parse_known_args()
    config = _load_config(Path(pre_args.config))
    default_tz = int(config.get("tz_shift", 0))

    parser = argparse.ArgumentParser(description="Fetch yfinance OHLC data", parents=[pre_parser])
    parser.add_argument("--symbol", help="Symbol to fetch and override config")
    parser.add_argument("--output", help="Output CSV file", default=None)
    parser.add_argument(
        "--tz-shift",
        type=int,
        default=default_tz,
        help="Hours to shift timestamps",
    )

    args = parser.parse_args(remaining)

    symbol = args.symbol or config.get("symbol", "EURUSD=X")
    output = Path(args.output) if args.output else None

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        df = fetch_multi_tf(symbol, config, tz_shift=args.tz_shift)
        if output is None:
            h1_label = _tf_label("H1")
            h1_df = df[df["timeframe"] == h1_label]
            last_ts = h1_df["timestamp"].max() if not h1_df.empty else df["timestamp"].max()
            name = _timestamp_code(last_ts)
            output = Path("data/raw") / f"{symbol.lower()}_{name}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False)
        LOGGER.info("Saved data to %s", output)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Error fetching data: %s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
