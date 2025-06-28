"""Send JSON data and prompts to GPT API and return raw response."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from openai import OpenAI


LOGGER = logging.getLogger(__name__)

# Template for the default prompt. The JSON filename will be inserted
# in place of ``%s`` to become the ``signal_id`` value.
DEFAULT_PROMPT = (
    "Analyze the current market regime and structure using the provided OHLCV and indicator data, including multi-timeframe trends and current trading session (e.g., asia, london, newyork). "
    "Classify regime_type as one of: 'uptrend', 'downtrend', 'sideway', 'high_volatility'. "
    ""
    "For uptrend: If price consistently makes higher highs and higher lows, stays above EMA/SMA, and RSI > 55, classify as 'uptrend'. "
    "In uptrend, only select buy_limit or buy_stop entries at likely pullback or support areas, NOT at random or in the middle of the trend. "
    "Do NOT enter sell in uptrend unless very strong reversal signals (e.g., RSI > 80 and bearish engulfing with high volume). "
    ""
    "For downtrend: If price consistently makes lower lows and lower highs, stays below EMA/SMA, and RSI < 45, classify as 'downtrend'. "
    "In downtrend, only select sell_limit or sell_stop entries at likely pullback or resistance, NOT at random or in the middle. "
    "Do NOT enter buy in downtrend unless very strong reversal signals (e.g., RSI < 20 and bullish engulfing with high volume). "
    ""
    "For sideway: If price ranges within a horizontal channel and EMA/SMA are flat, classify as 'sideway'. "
    "In sideway, only select buy_limit near lower support or sell_limit near upper resistance. Do NOT enter at the center of the range. "
    ""
    "Session context matters: During asia session, if volatility is low or trend is weak, prioritize 'sideway'. In london or newyork session, strong trends or high volatility are more common—allow trend entries when confirmed. "
    "If session is unclear, or current session is outside normal trading hours, consider the signal less reliable. "
    ""
    "If high volatility, trend unclear, or signals mixed, consider the signal less reliable. "
    ""
    "Entry/SL/TP must always align with the dominant regime and only at logical price levels (support, resistance, pullback), and session must support sufficient liquidity and volatility for trading. "
    ""
    "Do not use 'skip'. Always return a trade signal, but adjust the 'confidence' value (1-100) based on signal quality: "
    "- High confidence if regime and session are ideal, and signal is clear. "
    "- Low confidence if trend is unclear, signals are mixed, volatility is high, or session is unsuitable. "
    ""
    "Reply ONLY with a JSON object like: "
    '{"signal_id": "%s", "entry": , "sl": , "tp": , '
    '"pending_order_type": "", "confidence": , "regime_type": "", "short_reason": "สรุปเหตุผลสั้นๆ เช่น ขาขึ้นรอซื้อดึงกลับ, ขาลงรอขาย, กรอบออกข้าง, confidence ต่ำเพราะ session ไม่เหมาะ/สัญญาณปน"}.' 
    "pending_order_type must be one of [buy_limit, sell_limit, buy_stop, sell_stop]. ไม่ต้องเปลี่ยนค่า signal_id."
    "confidence is an integer (1-100). If the signal is less reliable, return lower confidence."
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
    json_path: Path,
    json_text: str,
    prompt: str,
    out_dir: Path,
    signal_id: str | None = None,
) -> None:
    """Save *json_text*, *prompt*, and *signal_id* to *out_dir* as one JSON file."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = _timestamp_code(datetime.now(timezone.utc))
    base = f"{json_path.stem}_{ts}"
    data = {
        "signal_id": signal_id or json_path.stem,
        "json": json.loads(json_text),
        "prompt": prompt,
    }
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
        default=config.get("save_prompt_dir", "data/live_trade/save_prompt_api"),
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

    signal_id = json_path.stem
    try:
        _save_prompt_copy(json_path, json_text, prompt, Path(args.save_dir), signal_id)
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
