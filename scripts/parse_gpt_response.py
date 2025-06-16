"""Parse GPT response and save as JSON signal."""

from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse GPT response to JSON")
    parser.add_argument("input", help="File with raw GPT response")
    parser.add_argument(
        "--output",
        help="Output JSON file path",
        default=None,
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

    try:
        data = _extract_json(text)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to parse response: %s", exc)
        raise SystemExit(1)

    if args.output:
        output = Path(args.output)
    else:
        name = data.get("signal_id") or datetime.utcnow().strftime("%Y%m%d%H%M%S")
        output = Path("signals") / f"{name}.json"

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
