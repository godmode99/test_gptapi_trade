"""Fetch trade history from MT5 and save to CSV."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

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


def _load_config(path: Path) -> Dict[str, Any]:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


def _timestamp_code(ts: pd.Timestamp) -> str:
    """Return the UNIX timestamp for *ts* as a string."""
    return str(int(pd.Timestamp(ts).timestamp()))


def fetch_history(config: Dict[str, Any], tz_shift: int = 0) -> pd.DataFrame:
    """Return a DataFrame of trade history for the given config."""
    start_str = str(config.get("start", ""))
    end_str = str(config.get("end", ""))
    if not start_str or not end_str:
        raise ValueError("'start' and 'end' must be specified in config")
    start = pd.to_datetime(start_str, errors="coerce")
    end = pd.to_datetime(end_str, errors="coerce")
    if pd.isna(start) or pd.isna(end):
        raise ValueError("Invalid start or end timestamp")

    deals = mt5.history_deals_get(start.to_pydatetime(), end.to_pydatetime())
    if deals is None:
        raise RuntimeError("Failed to fetch trade history")
    if len(deals) == 0:
        return pd.DataFrame()

    records = [deal._asdict() for deal in deals]
    df = pd.DataFrame.from_records(records)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], unit="s") + pd.Timedelta(hours=tz_shift)
    return df


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    default_cfg = Path(__file__).resolve().parent / "config" / "fetch_mt5_history.json"
    pre_parser.add_argument("--config", help="Path to JSON config", default=str(default_cfg))

    pre_args, remaining = pre_parser.parse_known_args()
    config = _load_config(Path(pre_args.config))
    default_tz = int(config.get("tz_shift", 0))
    default_save_path = config.get("save_as_path", "data/live_trade/history")

    parser = argparse.ArgumentParser(description="Fetch MT5 trade history", parents=[pre_parser])
    parser.add_argument("--output", help="Output CSV file", default=None)
    parser.add_argument("--tz-shift", type=int, default=default_tz, help="Hours to shift timestamps")
    args = parser.parse_args(remaining)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        _init_mt5()
        df = fetch_history(config, tz_shift=args.tz_shift)
        if df.empty:
            LOGGER.error("No trade history available for the given period")
            raise SystemExit(1)
        output = Path(args.output) if args.output else None
        if output is None:
            ts_now = pd.Timestamp.utcnow().floor("min")
            name = _timestamp_code(ts_now)
            output = Path(default_save_path) / f"history{name}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False)
        LOGGER.info("Saved history to %s", output)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Error fetching history: %s", exc)
        raise SystemExit(1)
    finally:
        _shutdown_mt5()


if __name__ == "__main__":
    main()
