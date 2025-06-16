"""Send CSV data and prompts to GPT API and return raw response."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import openai


LOGGER = logging.getLogger(__name__)


def _call_gpt(csv_text: str, prompt: str, model: str) -> str:
    """Send data to the GPT API and return the response text."""
    messages = [
        {
            "role": "system",
            "content": "You analyze trading data and produce JSON signals.",
        },
        {"role": "user", "content": f"{prompt}\n\nCSV Data:\n{csv_text}"},
    ]
    resp = openai.ChatCompletion.create(model=model, messages=messages)
    return resp.choices[0].message.content.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Send CSV data to GPT API")
    parser.add_argument("csv", help="CSV data file")
    parser.add_argument("--prompt", help="Prompt text", default="Generate signal")
    parser.add_argument("--prompt-file", help="Read prompt from file")
    parser.add_argument("--model", help="Model name", default="gpt-3.5-turbo")
    parser.add_argument("--output", help="Save raw response to file")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        csv_text = Path(args.csv).read_text(encoding="utf-8")
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

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        LOGGER.error("OPENAI_API_KEY environment variable is not set")
        raise SystemExit(1)
    openai.api_key = api_key

    try:
        response = _call_gpt(csv_text, prompt, args.model)
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
