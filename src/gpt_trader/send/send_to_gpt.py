"""Send JSON data and prompts to GPT API and return raw response."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from openai import OpenAI


LOGGER = logging.getLogger(__name__)

# Template for the default prompt. The JSON filename will be inserted
# in place of ``%s`` to become the ``signal_id`` value.
DEFAULT_PROMPT = (
    "Analyze the market regime and structure from the historical OHLCV and indicator data provided. "
    "Classify the current regime as one of: 'uptrend', 'downtrend', 'sideway', or 'high_volatility'. "
    "If the market is not clear or signals are mixed, set pending_order_type as 'skip' and do not enter a trade. "
    "Only select entry points that align with the dominant trend and are near support/resistance with minimal risk. "
    "Respond with ONLY a valid JSON object, like: "
    '{"signal_id": "%s", "entry": , "sl": , "tp": , '
    '"pending_order_type": "", "confidence": , "regime_type": ""}. '
    "pending_order_type must be one of [buy_limit, sell_limit, buy_stop, sell_stop, skip]. "
    "Confidence is an integer (1-100). If conditions are not optimal, use 'skip' as pending_order_type. "
)


def _load_config(path: Path) -> dict:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


def _find_latest_json(directory: Path) -> Path:
    """Return the most recently modified JSON file in *directory*."""
    json_files = list(directory.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {directory}")
    return max(json_files, key=lambda p: p.stat().st_mtime)


def _timestamp_code(ts: datetime) -> str:
    """Return a string like '250616_153045' for *ts*."""
    return ts.strftime("%d%m%y_%H%M%S")


def _save_prompt_copy(
    json_path: Path, json_text: str, prompt: str, out_dir: Path
) -> None:
    """Save *json_text* and *prompt* to *out_dir* as one JSON file."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = _timestamp_code(datetime.utcnow())
    base = f"{json_path.stem}_{ts}"
    data = {"json": json.loads(json_text), "prompt": prompt}
    (out_dir / f"{base}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _build_messages(json_text: str, prompt: str) -> list[dict[str, str]]:
    """Return OpenAI chat messages for *json_text* and *prompt*."""
    return [
        {
            "role": "system",
            "content": "You analyze trading data and produce JSON signals.",
        },
        {"role": "user", "content": f"{prompt}\n\nJSON Data:\n{json_text}"},
    ]


def _call_gpt(messages: list[dict[str, str]], model: str, client: "OpenAI") -> str:
    """Send *messages* to the GPT API and return the response text."""
    resp = client.chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content.strip()


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    default_cfg = Path(__file__).resolve().parent / "config" / "gpt.json"
    pre_parser.add_argument(
        "--config",
        help="Path to JSON config",
        default=str(default_cfg),
    )

    pre_args, remaining = pre_parser.parse_known_args()

    try:
        config = _load_config(Path(pre_args.config))
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("%s", exc)
        raise SystemExit(1)

    parser = argparse.ArgumentParser(
        description="Send JSON data to GPT API", parents=[pre_parser]
    )
    parser.add_argument("json", nargs="?", help="JSON data file")
    parser.add_argument(
        "--data-dir",
        default=config.get("json_path", "data/fetch"),
        help="Directory containing JSON files",
    )
    parser.add_argument("--prompt", help="Prompt text")
    parser.add_argument("--prompt-file", help="Read prompt from file")
    parser.add_argument(
        "--model",
        help="Model name",
        default=config.get("model", "gpt-4o"),
    )
    parser.add_argument(
        "--save-dir",
        default=config.get("save_prompt_dir", "data/save_prompt_api"),
        help="Directory to save JSON and prompt copies",
    )
    parser.add_argument("--output", help="Save raw response to file")

    args = parser.parse_args(remaining)
    config_json = config.get("json_file") or None

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    data_dir = Path(args.data_dir)

    if args.json:
        json_path = Path(args.json)
        src = "CLI"
    elif config_json:
        json_path = Path(config_json)
        if not json_path.is_absolute():
            json_path = data_dir / json_path
        src = "config json_file"
    else:
        try:
            json_path = _find_latest_json(data_dir)
            src = f"directory scan ({data_dir})"
        except FileNotFoundError as exc:  # noqa: BLE001
            LOGGER.error("%s", exc)
            raise SystemExit(1)
    LOGGER.info("Using JSON file %s from %s", json_path, src)

    try:
        json_text = json_path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to read JSON: %s", exc)
        raise SystemExit(1)

    prompt = args.prompt
    if args.prompt_file:
        try:
            prompt = Path(args.prompt_file).read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to read prompt file: %s", exc)
            raise SystemExit(1)

    if prompt is None:
        prompt = DEFAULT_PROMPT % json_path.stem

    try:
        _save_prompt_copy(json_path, json_text, prompt, Path(args.save_dir))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to save prompt copy: %s", exc)

    from openai import OpenAI  # imported here to avoid mandatory dependency for tests

    api_key = os.getenv("OPENAI_API_KEY") or config.get("openai_api_key")
    if not api_key:
        LOGGER.error(
            "OPENAI_API_KEY environment variable is not set and no api key in config"
        )
        raise SystemExit(1)
    client = OpenAI(api_key=api_key)

    messages = _build_messages(json_text, prompt)

    try:
        response = _call_gpt(messages, args.model, client)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("GPT API request failed: %s", exc)
        raise SystemExit(1)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(response, encoding="utf-8")
        LOGGER.info("Saved response to %s", output)
    else:
        print(response)


if __name__ == "__main__":
    main()
