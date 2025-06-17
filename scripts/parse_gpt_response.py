"""Parse GPT response and save as JSON signal.

This utility logs every parsed response to a CSV file. The log file is
created automatically if it does not exist and each new entry is appended
to preserve previous records. The raw input text is also written to a file
configured via ``path_latest_response`` so the most recent reply can be
inspected easily.
"""
from __future__ import annotations
# python scripts/parse_gpt_response.py

import argparse
import csv
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path


LOGGER = logging.getLogger(__name__)


def _load_config(path: Path) -> dict:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


def _extract_json(text: str) -> dict:
    """Extract a JSON object from raw GPT text.

    The GPT reply may wrap the JSON in code fences like '```json ... ```' or
    plain '``` ... ```' blocks. These fences are stripped before parsing.
    """

    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1)

    # Use a non-greedy pattern so additional text or JSON blocks after the
    # first one do not get included in the match.
    match = re.search(r"{.*?}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in response")
    return json.loads(match.group(0))


def _timestamp_code(ts: datetime) -> str:
    """Return a string like '250616_153045' for a timestamp."""
    return ts.strftime("%d%m%y_%H%M%S")


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    default_cfg = (
        Path(__file__).resolve().parent / "signals" / "config" / "parse.json"
    )
    pre_parser.add_argument(
        "--config", help="Path to JSON config", default=str(default_cfg)
    )

    pre_args, remaining = pre_parser.parse_known_args()
    try:
        config = _load_config(Path(pre_args.config))
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("%s", exc)
        raise SystemExit(1)

    csv_dir = Path(config.get("path_signals_csv", "signals_csv"))
    csv_name = config.get("file_signal_report", "csv_signal_report.csv")
    default_csv_log = csv_dir / csv_name
    default_json_dir = config.get("path_signals_json", "signals_json")
    default_latest = config.get("path_latest_response", "latest_response.txt")
    default_tz = int(config.get("tz_shift", 0))

    parser = argparse.ArgumentParser(
        description="Parse GPT response to JSON", parents=[pre_parser]
    )
    parser.add_argument("input", help="File with raw GPT response")
    parser.add_argument(
        "--output", help="Output JSON file path", default=None
    )
    parser.add_argument(
        "--csv-log", default=str(default_csv_log), help="Path to CSV log file"
    )
    parser.add_argument(
        "--json-dir", default=default_json_dir, help="Directory for generated JSON files"
    )
    parser.add_argument(
        "--latest-response",
        default=default_latest,
        help="File to store raw GPT response",
    )
    parser.add_argument(
        "--tz-shift",
        type=int,
        default=default_tz,
        help="Hours to shift timestamps",
    )

    args = parser.parse_args(remaining)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        text = Path(args.input).read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to read input file: %s", exc)
        raise SystemExit(1)

    # Store raw response for debugging
    latest_path = Path(args.latest_response)
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        latest_path.write_text(text, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to update %s: %s", latest_path, exc)

    LOGGER.info("Raw response: %s", text)

    try:
        data = _extract_json(text)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to parse response: %s", exc)
        raise SystemExit(1)

    csv_path = Path(args.csv_log)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow() + timedelta(hours=args.tz_shift)
    row = {
        "timestamp": ts.isoformat(),
        "signal_id": data.get("signal_id"),
        "entry": data.get("entry"),
        "sl": data.get("sl"),
        "tp": data.get("tp"),
        "pending_order_type": data.get("pending_order_type"),
        "confidence": data.get("confidence"),
    }
    is_new = not csv_path.exists()
    try:
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
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to write CSV log: %s", exc)

    if args.output:
        output = Path(args.output)
    else:
        name = _timestamp_code(ts)
        output = Path(args.json_dir) / f"{name}.json"

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to write output file: %s", exc)
        raise SystemExit(1)

    LOGGER.info("Saved signal to %s", output)


if __name__ == "__main__":
    main()
