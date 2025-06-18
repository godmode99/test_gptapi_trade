from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from scripts.fetch import fetch_yf_data
from scripts.send_api.send_to_gpt import _build_messages, _call_gpt
from scripts.parse_response.parse_gpt_response import _extract_json


LOGGER = logging.getLogger(__name__)


def _load_config(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


def _append_signal(row: dict, csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "signal_id",
                "entry",
                "sl",
                "tp",
                "pending_order_type",
                "confidence",
            ],
        )
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def _run_loop(cfg: dict) -> None:
    symbol = cfg.get("symbol", "XAUUSD")
    timeframe = cfg.get("timeframe", "M15")
    tz_shift = int(cfg.get("tz_shift", 0))
    fetch_bars = int(cfg.get("fetch_bars", 30))

    start = pd.to_datetime(cfg["start_time"])
    end = pd.to_datetime(cfg["end_time"])
    step = timedelta(minutes=int(cfg.get("loop_every_minutes", 60)))

    prompt_template = Path(cfg["prompt_template"]).read_text(encoding="utf-8")
    model = cfg.get("gpt_model", "gpt-4o")
    signal_table = Path(cfg["signal_table"])

    api_key = os.getenv("OPENAI_API_KEY") or cfg.get("openai_api_key")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    now = start
    while now <= end:
        fetch_cfg = {
            "tz_shift": tz_shift,
            "symbol": symbol,
            "fetch_bars": fetch_bars,
            "time_fetch": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timeframes": [{"tf": timeframe, "keep": fetch_bars}],
        }
        df = fetch_yf_data.fetch_multi_tf(symbol, fetch_cfg, tz_shift=tz_shift)
        name = now.strftime("%Y%m%d_%H%M")
        out_csv = Path("back_test/fetch") / f"{symbol.lower()}_{name}.csv"
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_csv, index=False)

        csv_text = out_csv.read_text(encoding="utf-8")
        prompt = prompt_template
        messages = _build_messages(csv_text, prompt)
        response = _call_gpt(messages, model, client)
        data = _extract_json(response)
        row = {
            "timestamp": now.isoformat(),
            "signal_id": data.get("signal_id"),
            "entry": data.get("entry"),
            "sl": data.get("sl"),
            "tp": data.get("tp"),
            "pending_order_type": data.get("pending_order_type"),
            "confidence": data.get("confidence"),
        }
        _append_signal(row, signal_table)
        now += step


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GPT backtest loop")
    default_cfg = Path(__file__).resolve().parent / "backtest.json"
    parser.add_argument("--config", default=str(default_cfg), help="Path to JSON config")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    cfg = _load_config(Path(args.config))
    _run_loop(cfg)


if __name__ == "__main__":
    main()
