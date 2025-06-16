"""Send CSV data and prompts to GPT API and return raw response."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

from openai import OpenAI


LOGGER = logging.getLogger(__name__)

# Template for the default prompt. The CSV filename will be inserted
# in place of ``%s`` to become the ``signal_id`` value.
DEFAULT_PROMPT = (
    "Generate a trading signal and reply only with a JSON object like "
    '{"signal_id": "%s", "entry": , "sl": , "tp": , '
    '"pending_order_type": "", "confidence":  }'
)


def _load_config(path: Path) -> dict:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


def _find_latest_csv(directory: Path) -> Path:
    """Return the most recently modified CSV file in *directory*."""
    csv_files = list(directory.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {directory}")
    return max(csv_files, key=lambda p: p.stat().st_mtime)


def _call_gpt(csv_text: str, prompt: str, model: str, client: OpenAI) -> str:
    """Send data to the GPT API and return the response text."""
    messages = [
        {
            "role": "system",
            "content": "You analyze trading data and produce JSON signals.",
        },
        {"role": "user", "content": f"{prompt}\n\nCSV Data:\n{csv_text}"},
    ]
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
        description="Send CSV data to GPT API", parents=[pre_parser]
    )
    parser.add_argument("csv", nargs="?", help="CSV data file")
    parser.add_argument(
        "--data-dir",
        default=config.get("csv_path", "data/raw"),
        help="Directory containing CSV files",
    )
    parser.add_argument("--prompt", help="Prompt text")
    parser.add_argument("--prompt-file", help="Read prompt from file")
    parser.add_argument(
        "--model",
        help="Model name",
        default=config.get("model", "gpt-4o"),
    )
    parser.add_argument("--output", help="Save raw response to file")

    args = parser.parse_args(remaining)
    config_csv = config.get("csv_file") or None

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    data_dir = Path(args.data_dir)

    if args.csv:
        csv_path = Path(args.csv)
        src = "CLI"
    elif config_csv:
        csv_path = Path(config_csv)
        if not csv_path.is_absolute():
            csv_path = data_dir / csv_path
        src = "config csv_file"
    else:
        try:
            csv_path = _find_latest_csv(data_dir)
            src = f"directory scan ({data_dir})"
        except FileNotFoundError as exc:  # noqa: BLE001
            LOGGER.error("%s", exc)
            raise SystemExit(1)
    LOGGER.info("Using CSV file %s from %s", csv_path, src)

    try:
        csv_text = csv_path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to read CSV: %s", exc)
        raise SystemExit(1)

    prompt = args.prompt
    if args.prompt_file:
        try:
            prompt = Path(args.prompt_file).read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to read prompt file: %s", exc)
            raise SystemExit(1)

    if prompt is None:
        prompt = DEFAULT_PROMPT % csv_path.stem

    api_key = os.getenv("OPENAI_API_KEY") or config.get("openai_api_key")
    if not api_key:
        LOGGER.error(
            "OPENAI_API_KEY environment variable is not set and no api key in config"
        )
        raise SystemExit(1)
    client = OpenAI(api_key=api_key)

    try:
        response = _call_gpt(csv_text, prompt, args.model, client)
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
