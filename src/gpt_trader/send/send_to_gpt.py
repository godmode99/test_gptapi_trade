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
    "Classify regime_type as one of: 'uptrend', 'downtrend', 'sideway', 'high_volatility'. ระบุ regime_type ทุก timeframe(5m, 15m, 1H) ที่ส่งไป "
    "'uptrend': ราคาทำ higher highs/lows, อยู่เหนือ EMA/SMA, RSI > 55, 'downtrend': ราคาทำ lower highs/lows, อยู่ใต้ EMA/SMA, RSI < 45 "
    "'sideway': แกว่งในกรอบแนวนอน, EMA/SMA ค่อนข้าง flat, 'high_volatility': สัญญาณสับสน, ราคาเหวี่ยงแรง ไม่แน่ใจทิศทาง "
    "ใช้ 15m 12แท่งเทียนเป็นหลักในการตัดสินใจว่าจะเทรดอย่างไร ถ้า15m เป็น sideway/high_volatilityให้ ระบุ pending-order: skip ไม่เทรด หาก เป็น uptrend ให้ bias buy หากเป็น downtrend ให้ bias sell "
    "ใช้ 1H 6 แท่งเทียนดูภาพกว้างว่าหากbiasตาม15mจะมีแนวรับแนวต้าน,volumeอะไรรอยู่ มีโอกาสที่ราคาจะโดน pullback กลับมาแรงไหม เลือกจุด tp/sl "
    "ใช้ 5m 20 แท่งเทียนในการเลือกกลยุทธเลือกจุดที่จะ pending_order entry ที่ได้เปรียบ(rr>1.5): "
    "หาก bias buy แล้ว 5m เป็น uptrend ให้ buy_stop ที่ resistance or high "
    "หาก bias buy แล้ว 5m เป็น downtrend/sideway/high_volatility ให้ buy_limit ที่ support or low "
    "หาก bias sell แล้ว 5m เป็น downtrend ให้ sell_stop ที่ support or low "
    "หาก bias sell แล้ว 5m เป็น uptrend/sideway/high_volatility  ให้ sell_limit ที่ resistance or high "
    "วิธีการให้คะแนนค่า confidence(confidence is an integer (0-100)) "
    "1. ถ้า 15m เป็น sideway, high_volatility ให้ระบุ confidence: 0 "
    "2. เต็ม 40 คะแนน ประเมินความชัดเจนของ trend ใน 15m เพราะจะช่วยให้มั่นใจใน bias "
    "3. เต็ม 30 คะแนน ประเมิน trend match กันระหว่าง 15m กับ 5m เพราะจะมั่นใจว่า trend 15m อาจจะไปต่อ "
    "4. เต็ม 20 คะแนน ประเมิน trend match กันระหว่าง 15m กับ 1H เพราะจะมั่นใจว่าไม่สวนทาง trend 1H หากสวนทางก็ดูว่ามีโอกาสที่จะ break หรือไปได้อีกไกลแค่ไหน "
    "6. เต็ม 10 คะแนน ประเมินจากอื่นๆ "
    "5. หักคะแนนเต็ม 10 คะแนน ประเมิน session หาก trend ไม่ match กัน ถ้าเป็น sesion asia,london หักมากที่สุดไม่เกิน-6, newyork หักมากที่สุดไม่เกิน-10 "
    "ใช้ pending_order: skip เพื่อข้ามการเทรดได้ 2 กรณี เท่านั้น. 1. if confidence lower than 40 2. ถ้า 15m เป็น sideway or high_volatility "
    "Reply ONLY with a JSON object like: "
    '{"signal_id": "%s", "entry": , "sl": , "tp": , '
    '"pending_order_type": "", "confidence": , "regime_type": "", "short_reason": "อธิบายการให้คะแนนเป็นภาษาไทย confidence"}.'
    "pending_order_type must be one of [buy_limit, sell_limit, buy_stop, sell_stop, skip-trade]. ไม่ต้องเปลี่ยนค่า signal_id."
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
