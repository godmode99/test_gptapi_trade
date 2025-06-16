"""Parse GPT response and save as JSON signal.

This utility logs every parsed response to a CSV file. The log file is
created automatically if it does not exist and each new entry is appended
to preserve previous records.
"""
from __future__ import annotations
# python scripts/parse_gpt_response.py

import argparse
import csv
import json
import logging
import re
from datetime import datetime
from pathlib import Path


LOGGER = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    """Extract a JSON object from raw GPT text."""
    match = re.search(r"{.*}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in response")
    return json.loads(match.group(0))


def _timestamp_code(ts: datetime) -> str:
    """Return a string like '250616_153045' for a timestamp."""
    return ts.strftime("%d%m%y_%H%M%S")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse GPT response to JSON")
    parser.add_argument("input", help="File with raw GPT response")
    parser.add_argument(
        "--output",
        help="Output JSON file path",
        default=None,
    )
    parser.add_argument(
        "--csv-log",
        default="logs/responses.csv",
        help="Path to CSV log file",
    )
    parser.add_argument(
        "--json-dir",
        default="signals",
        help="Directory for generated JSON files",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        text = Path(args.input).read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to read input file: %s", exc)
        raise SystemExit(1)

    LOGGER.info("Raw response: %s", text)

    try:
        data = _extract_json(text)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to parse response: %s", exc)
        raise SystemExit(1)

    csv_path = Path(args.csv_log)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "signal_id": data.get("signal_id"),
        "entry": data.get("entry"),
        "sl": data.get("sl"),
        "tp": data.get("tp"),
        "position_type": data.get("position_type"),
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
                    "position_type",
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
        name = _timestamp_code(datetime.utcnow())
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
