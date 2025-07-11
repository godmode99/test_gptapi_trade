"""Fetch OHLCV data from MT5 and compute indicators.

This script connects to the MetaTrader5 terminal and retrieves OHLCV data
according to parameters defined in a JSON configuration file. The data is
enriched with ATR14, RSI14 and SMA20 values before being saved to CSV.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import MetaTrader5 as mt5
from gpt_trader.utils.indicators import compute_indicators
from gpt_trader.utils import write_json_no_nulls


LOGGER = logging.getLogger(__name__)


TF_MAP: Dict[str, int] = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}

TF_DELTA: Dict[int, pd.Timedelta] = {
    mt5.TIMEFRAME_M1: pd.Timedelta(minutes=1),
    mt5.TIMEFRAME_M5: pd.Timedelta(minutes=5),
    mt5.TIMEFRAME_M15: pd.Timedelta(minutes=15),
    mt5.TIMEFRAME_M30: pd.Timedelta(minutes=30),
    mt5.TIMEFRAME_H1: pd.Timedelta(hours=1),
    mt5.TIMEFRAME_H4: pd.Timedelta(hours=4),
    mt5.TIMEFRAME_D1: pd.Timedelta(days=1),
}


def _init_mt5() -> None:
    """Initialize connection to MetaTrader5."""
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize() failed: {mt5.last_error()}")


def _shutdown_mt5() -> None:
    """Shutdown MetaTrader5 connection."""
    mt5.shutdown()


def _load_config(path: Path) -> Dict[str, Any]:
    """Load JSON configuration from *path*."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc
    return data


def _tf_label(tf: str) -> str:
    """Return a human readable label like '5m' for timeframe name."""
    digits = "".join(ch for ch in tf if ch.isdigit())
    letters = "".join(ch for ch in tf if ch.isalpha()).lower()
    return f"{digits}{letters}"


def _timestamp_code(ts: pd.Timestamp) -> str:
    """Return the UNIX timestamp for *ts* as a string."""
    return str(int(pd.Timestamp(ts).timestamp()))


def get_session(ts: pd.Timestamp) -> str:
    """Return the trading session name for *ts* (เวลาประเทศไทย ตามภาพ)."""
    hour = pd.Timestamp(ts).hour

    if 5 <= hour < 14:
        return "asia"        # Sydney + Tokyo
    elif 14 <= hour < 18:
        return "london"      # London only
    elif 19 <= hour or hour < 5:
        return "newyork"     # New York
    return "closed"



def _fetch_rates(
    symbol: str,
    timeframe: int,
    bars: int,
    tz_shift: int = 0,
    end_time: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Fetch OHLC data from MT5 for a given timeframe.

    If *end_time* is provided the data will end at that timestamp.
    """
    LOGGER.info(
        "Fetching %s bars for %s timeframe on %s",
        bars,
        timeframe,
        symbol,
    )
    if end_time is None:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    else:
        delta = TF_DELTA.get(timeframe)
        if delta is None:
            raise ValueError(f"Unknown timeframe constant: {timeframe}")
        end = pd.Timestamp(end_time)
        start = end - delta * (bars - 1)
        rates = mt5.copy_rates_range(
            symbol,
            timeframe,
            start.to_pydatetime(),
            end.to_pydatetime(),
        )
    if rates is None:
        raise RuntimeError(f"Failed to fetch data for {symbol} timeframe {timeframe}")
    df = pd.DataFrame(rates)
    df = df.sort_values("time").reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["time"], unit="s") + pd.Timedelta(hours=tz_shift)
    df = df.drop(columns=["time", "spread", "real_volume"], errors="ignore")
    return df




def fetch_multi_tf(symbol: str, config: Dict[str, Any], tz_shift: int = 0) -> pd.DataFrame:
    """Fetch data for several timeframes and merge into one DataFrame."""
    timeframes_conf = config.get("timeframes", [])
    indicators_conf = config.get("indicators")
    fetch_bars = int(config.get("fetch_bars", 20))

    time_fetch_str = str(config.get("time_fetch", "")).strip()
    if time_fetch_str:
        end_time = pd.to_datetime(time_fetch_str, errors="coerce")
        if pd.isna(end_time):
            raise ValueError(
                "Timestamp format must be YYYY-MM-DD HH:MM:SS and the chosen date may not be available"
            )
    else:
        end_time = None

    frames = []
    for item in timeframes_conf:
        tf_name = str(item.get("tf", "")).upper()
        keep = int(item.get("keep", 0))
        tf_const = TF_MAP.get(tf_name)
        if tf_const is None:
            raise ValueError(f"Unsupported timeframe: {tf_name}")
        label = _tf_label(tf_name)
        df = _fetch_rates(symbol, tf_const, fetch_bars, tz_shift, end_time)
        df = compute_indicators(df, indicators_conf)
        df = df.tail(keep)
        df["timeframe"] = label
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        raise ValueError(
            "Timestamp format must be YYYY-MM-DD HH:MM:SS and the chosen date may not be available"
        )

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
    combined = combined[cols]
    return combined


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    default_cfg = Path(__file__).resolve().parent / "config" / "fetch_mt5.json"
    pre_parser.add_argument(
        "--config",
        help="Path to JSON config",
        default=str(default_cfg),
    )

    # First parse only --config to determine defaults from file
    pre_args, remaining = pre_parser.parse_known_args()
    config = _load_config(Path(pre_args.config))
    default_tz = int(config.get("tz_shift", 0))
    default_save_path = config.get("save_as_path", "data/live_trade/fetch")

    parser = argparse.ArgumentParser(
        description="Fetch MT5 OHLC data", parents=[pre_parser]
    )
    parser.add_argument("--symbol", help="Symbol to fetch and override config")
    parser.add_argument(
        "--output",
        help="Output CSV file",
        default=None,
    )
    parser.add_argument(
        "--tz-shift",
        type=int,
        default=default_tz,
        help="Hours to shift timestamps (e.g. 4 for GMT+3 to GMT+7)",
    )
    parser.add_argument(
        "--time-fetch",
        default=str(config.get("time_fetch", "")),
        help="Fetch bars ending at this time (YYYY-MM-DD HH:MM:SS)",
    )

    args = parser.parse_args(remaining)

    symbol = args.symbol or config.get("symbol", "EURUSD")
    signal_prefix = str(config.get("symbol_signal", symbol)).lower()

    if args.time_fetch:
        config["time_fetch"] = args.time_fetch

    output = Path(args.output) if args.output else None

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        _init_mt5()
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
    except Exception as exc:
        LOGGER.error("Error fetching data: %s", exc)
        raise SystemExit(1)
    finally:
        _shutdown_mt5()


if __name__ == "__main__":
    main()
