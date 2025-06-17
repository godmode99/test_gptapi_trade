#!/usr/bin/env python
"""Run the fetch -> GPT -> parse workflow in one command."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path


async def _run_step(step: str, script: Path, *args: str) -> None:
    """Run a script as a subprocess and wait for it to finish."""
    cmd = [sys.executable, str(script), *args]
    logging.info("Running %s: %s", step, " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.communicate()
    if proc.returncode:
        raise RuntimeError(f"{step} failed with code {proc.returncode}")


def _load_config(path: Path) -> dict:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


async def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    default_cfg = Path(__file__).resolve().parent / "config" / "main.json"
    pre_parser.add_argument(
        "--config", help="Path to JSON config", default=str(default_cfg)
    )

    pre_args, remaining = pre_parser.parse_known_args()
    try:
        config = _load_config(Path(pre_args.config))
    except Exception as exc:  # noqa: BLE001
        logging.error("%s", exc)
        raise SystemExit(1)

    parser = argparse.ArgumentParser(
        description="Fetch data, send to GPT and parse the response sequentially",
        parents=[pre_parser],
    )
    parser.add_argument(
        "--fetch-type",
        choices=["yf", "mt5"],
        default=config.get("fetch_type", "yf"),
        help="Select built-in data fetcher (ignored if --fetch-script is set)",
    )
    parser.add_argument(
        "--fetch-script",
        default=config.get("fetch_script"),
        help="Path to data fetching script (overrides --fetch-type)",
    )
    parser.add_argument(
        "--send-script",
        default=config.get("send_script", "scripts/send_api/send_to_gpt.py"),
        help="Path to GPT API script",
    )
    parser.add_argument(
        "--parse-script",
        default=config.get(
            "parse_script", "scripts/parse_response/parse_gpt_response.py"
        ),
        help="Path to response parsing script",
    )
    parser.add_argument(
        "--response",
        default=config.get("response", "data/signals/latest_response.txt"),
        help="Temporary file to store raw GPT response",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        default=bool(config.get("skip_fetch", False)),
        help="Skip the data fetching step",
    )
    parser.add_argument(
        "--skip-send",
        action="store_true",
        default=bool(config.get("skip_send", False)),
        help="Skip sending data to GPT",
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        default=bool(config.get("skip_parse", False)),
        help="Skip parsing the GPT response",
    )
    args = parser.parse_args(remaining)

    if args.fetch_script is None:
        fetch_map = {
            "yf": "scripts/fetch/fetch_yf_data.py",
            "mt5": "scripts/fetch/fetch_mt5_data.py",
        }
        args.fetch_script = fetch_map[args.fetch_type]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not args.skip_fetch:
        await _run_step("fetch", Path(args.fetch_script))
    if not args.skip_send:
        await _run_step("send", Path(args.send_script), "--output", args.response)
    if not args.skip_parse:
        await _run_step("parse", Path(args.parse_script), args.response)


if __name__ == "__main__":
    asyncio.run(main())
