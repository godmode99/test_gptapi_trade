#!/usr/bin/env python
"""Run the fetch -> GPT -> parse workflow in one command."""

from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
import logging
import sys
from pathlib import Path


async def _run_step(step: str, script: Path, *args: str) -> None:
    """Run a script as a subprocess and wait for it to finish.

    If *script* points to a Python file, run it as a module so the project
    root is on ``sys.path``. Otherwise fall back to executing the file
    directly with the current Python interpreter.
    """
    if script.suffix == ".py":
        try:
            module = ".".join(
                script.with_suffix("")
                .resolve()
                .relative_to(Path(__file__).resolve().parents[1])
                .parts
            )
        except ValueError:
            module = ".".join(script.with_suffix("").parts)
        cmd = [sys.executable, "-m", module, *args]
    else:
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
    default_cfg = Path(__file__).resolve().parent / "config" / "setting_main.json"
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
    workflow = config.get("workflow", {})
    scripts_cfg = workflow.get("scripts", {})
    skip_cfg = workflow.get("skip", {})

    parser.add_argument(
        "--fetch-type",
        choices=["yf", "mt5"],
        default=workflow.get("fetch_type", "mt5"),
        help="Select built-in data fetcher (ignored if --fetch-script is set)",
    )
    parser.add_argument(
        "--fetch-script",
        default=scripts_cfg.get("fetch"),
        help="Path to data fetching script (overrides --fetch-type)",
    )
    parser.add_argument(
        "--send-script",
        default=scripts_cfg.get("send", "scripts/send_api/send_to_gpt.py"),
        help="Path to GPT API script",
    )
    parser.add_argument(
        "--parse-script",
        default=scripts_cfg.get(
            "parse", "scripts/parse_response/parse_gpt_response.py"
        ),
        help="Path to response parsing script",
    )
    parser.add_argument(
        "--response",
        default=workflow.get(
            "response", "live_trade/data/signals/latest_response.txt"
        ),
        help="Temporary file to store raw GPT response",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        default=bool(skip_cfg.get("fetch", False)),
        help="Skip the data fetching step",
    )
    parser.add_argument(
        "--skip-send",
        action="store_true",
        default=bool(skip_cfg.get("send", False)),
        help="Skip sending data to GPT",
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        default=bool(skip_cfg.get("parse", False)),
        help="Skip parsing the GPT response",
    )
    args = parser.parse_args(remaining)

    fetch_cfg = config.get("fetch")
    send_cfg = config.get("send")
    parse_cfg = config.get("parse")

    if not args.fetch_script:
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
        if fetch_cfg:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
                json.dump(fetch_cfg, tmp)
            try:
                await _run_step("fetch", Path(args.fetch_script), "--config", tmp.name)
            finally:
                Path(tmp.name).unlink(missing_ok=True)
        else:
            await _run_step("fetch", Path(args.fetch_script))
    if not args.skip_send:
        send_args = ["--output", args.response]
        if send_cfg:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
                json.dump(send_cfg, tmp)
            send_args.extend(["--config", tmp.name])
            try:
                await _run_step("send", Path(args.send_script), *send_args)
            finally:
                Path(tmp.name).unlink(missing_ok=True)
        else:
            await _run_step("send", Path(args.send_script), *send_args)
    if not args.skip_parse:
        parse_args = []
        if parse_cfg:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
                json.dump(parse_cfg, tmp)
            parse_args.extend(["--config", tmp.name])
            parse_args.append(args.response)
            try:
                await _run_step("parse", Path(args.parse_script), *parse_args)
            finally:
                Path(tmp.name).unlink(missing_ok=True)
        else:
            await _run_step("parse", Path(args.parse_script), args.response)


if __name__ == "__main__":
    asyncio.run(main())
