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

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gpt_trader.cli.common import _run_step
from gpt_trader.utils import post_signal


def _load_config(path: Path) -> dict:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


async def main() -> dict[str, str]:
    pre_parser = argparse.ArgumentParser(add_help=False)

    root_dir = ROOT
    default_cfg = root_dir / "config" / "setting_live_trade.json"
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
        default=str(
            scripts_cfg.get(
                "send",
                SRC / "gpt_trader" / "send" / "send_to_gpt.py",
            )
        ),
        help="Path to GPT API script",
    )
    parser.add_argument(
        "--parse-script",
        default=str(
            scripts_cfg.get(
                "parse",
                SRC / "gpt_trader" / "parse" / "parse_gpt_response.py",
            )
        ),
        help="Path to response parsing script",
    )
    parser.add_argument(
        "--response",
        default=workflow.get("response", "data/live_trade/signals/latest_response.txt"),
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

    def _resolve_path(p: str | None) -> str | None:
        if p is None:
            return None
        path = Path(p)
        if not path.is_absolute():
            path = root_dir / path
        return str(path)

    args.fetch_script = _resolve_path(args.fetch_script)
    args.send_script = _resolve_path(args.send_script)
    args.parse_script = _resolve_path(args.parse_script)
    args.response = _resolve_path(args.response)

    fetch_cfg = config.get("fetch")
    send_cfg = config.get("send")
    parse_cfg = config.get("parse")

    if not args.fetch_script:
        fetch_map = {
            "yf": SRC / "gpt_trader" / "fetch" / "fetch_yf_data.py",
            "mt5": SRC / "gpt_trader" / "fetch" / "fetch_mt5_data.py",
        }
        args.fetch_script = str(fetch_map[args.fetch_type])

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    results: dict[str, str] = {}

    if not args.skip_fetch:
        try:
            if fetch_cfg:
                with tempfile.NamedTemporaryFile(
                    "w", delete=False, suffix=".json"
                ) as tmp:
                    json.dump(fetch_cfg, tmp)
                try:
                    await _run_step(
                        "fetch", Path(args.fetch_script), "--config", tmp.name
                    )
                finally:
                    Path(tmp.name).unlink(missing_ok=True)
            else:
                await _run_step("fetch", Path(args.fetch_script))
            results["fetch"] = "success"
        except Exception as exc:  # noqa: BLE001
            logging.error("fetch step failed: %s", exc)
            results["fetch"] = "error"
    else:
        results["fetch"] = "skipped"
    if not args.skip_send:
        send_args = ["--output", args.response]
        try:
            if send_cfg:
                with tempfile.NamedTemporaryFile(
                    "w", delete=False, suffix=".json"
                ) as tmp:
                    json.dump(send_cfg, tmp)
                send_args.extend(["--config", tmp.name])
                try:
                    await _run_step("send", Path(args.send_script), *send_args)
                finally:
                    Path(tmp.name).unlink(missing_ok=True)
            else:
                await _run_step("send", Path(args.send_script), *send_args)
            results["send"] = "success"
        except Exception as exc:  # noqa: BLE001
            logging.error("send step failed: %s", exc)
            results["send"] = "error"
    else:
        results["send"] = "skipped"
    if not args.skip_parse:
        parse_args = []
        try:
            if parse_cfg:
                with tempfile.NamedTemporaryFile(
                    "w", delete=False, suffix=".json"
                ) as tmp:
                    json.dump(parse_cfg, tmp)
                parse_args.extend(["--config", tmp.name])
                parse_args.append(args.response)
                try:
                    await _run_step("parse", Path(args.parse_script), *parse_args)
                finally:
                    Path(tmp.name).unlink(missing_ok=True)
            else:
                await _run_step("parse", Path(args.parse_script), args.response)
            results["parse"] = "success"
            try:
                cfg_lookup = parse_cfg or {}
                latest = Path(
                    cfg_lookup.get("path_latest_response", args.response)
                ).with_suffix(".json")
                signal_data = json.loads(latest.read_text(encoding="utf-8"))
                api_cfg = config.get("signal_api", {})
                neon_cfg = config.get("neon", {})
                if api_cfg.get("enabled", True) and api_cfg.get("base_url"):
                    post_signal(
                        api_cfg.get("base_url", ""),
                        api_cfg.get("auth_token", ""),
                        signal_data,
                    )
                if neon_cfg.get("enabled", True) and neon_cfg.get("api_url"):
                    post_signal(
                        neon_cfg.get("api_url", ""),
                        neon_cfg.get("auth_token", ""),
                        signal_data,
                    )
                results["post_signal"] = "success"
            except Exception as exc:  # noqa: BLE001
                logging.error("post signal failed: %s", exc)
                results["post_signal"] = "error"
        except Exception as exc:  # noqa: BLE001
            logging.error("parse step failed: %s", exc)
            results["parse"] = "error"
    else:
        results["parse"] = "skipped"

    return results


if __name__ == "__main__":
    asyncio.run(main())
