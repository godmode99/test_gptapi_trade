"""Fetch OHLCV data via yfinance and compute indicators."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf
from gpt_trader.utils.indicators import compute_indicators
from gpt_trader.utils import write_json_no_nulls

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
    """Return the UNIX timestamp for *ts* as a string."""
    return str(int(pd.Timestamp(ts).timestamp()))


def get_session(ts: pd.Timestamp) -> str:
    """Return the trading session name for *ts*."""
    hour = pd.Timestamp(ts).hour
    if 0 <= hour < 8:
        return "asia"
    if 8 <= hour < 16:
        return "london"
    return "newyork"


def _fetch_rates(symbol: str, interval: str, bars: int, tz_shift: int = 0) -> pd.DataFrame:
    """Fetch OHLC data from yfinance."""
    LOGGER.info(
        "Fetching %s bars for %s interval on %s",
        bars,
        interval,
        symbol,
    )
    df = yf.download(symbol, interval=interval, period="60d", progress=False)
    if df.empty:
        raise RuntimeError(f"Failed to fetch data for {symbol} interval {interval}")
    df = df.tail(bars)
    idx = pd.to_datetime(df.index)
    if idx.tzinfo is not None:
        idx = idx.tz_convert(None)
    df.index = idx + pd.Timedelta(hours=tz_shift)
    df.index.name = "timestamp"
    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "tick_volume",
        }
    )
    df = df.reset_index()
    df = df[["timestamp", "open", "high", "low", "close", "tick_volume"]]
    return df




def fetch_multi_tf(symbol: str, config: Dict[str, Any], tz_shift: int = 0) -> pd.DataFrame:
    """Fetch data for several timeframes and merge into one DataFrame."""
    timeframes_conf: List[Dict[str, Any]] = config.get("timeframes", [])
    indicators_conf = config.get("indicators")
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
        df = compute_indicators(df, indicators_conf)
        df = df.tail(keep)
        df["timeframe"] = label
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined["session"] = combined["timestamp"].apply(get_session)

    cols = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
    ]
    for ind in ["atr14", "rsi14", "sma20", "ema50", "sma200"]:
        if ind in combined.columns:
            cols.append(ind)
    cols += ["timeframe", "session"]
    return combined[cols]


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    default_cfg = Path(__file__).resolve().parent / "config" / "fetch_yf.json"
    pre_parser.add_argument(
        "--config",
        help="Path to JSON config",
        default=str(default_cfg),
    )

    pre_args, remaining = pre_parser.parse_known_args()
    config = _load_config(Path(pre_args.config))
    default_tz = int(config.get("tz_shift", 0))
    default_save_path = config.get("save_as_path", "data/fetch")

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
    signal_prefix = str(config.get("symbol_signal", symbol)).lower()
    output = Path(args.output) if args.output else None

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        df = fetch_multi_tf(symbol, config, tz_shift=args.tz_shift)
        if df.empty:
            LOGGER.error("No data available for the requested time_fetch")
            raise SystemExit(1)
        if output is None:
            ts_now = pd.Timestamp.utcnow().floor("min")
            name = _timestamp_code(ts_now)
            output = Path(default_save_path) / f"{signal_prefix}{name}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False)
        json_out = output.with_suffix(".json")
        write_json_no_nulls(df, json_out)
        LOGGER.info("Saved data to %s and %s", output, json_out)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Error fetching data: %s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
