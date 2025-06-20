"""Scheduler that runs :mod:`main_liveTrade.py` every hour."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
import logging
import threading
import time

from apscheduler.schedulers.blocking import BlockingScheduler


from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main_liveTrade import main as run_main
from gpt_trader.notify import send_line, send_telegram
from gpt_trader.cli.lastest_signal_to_mt5 import TradeSignalSender

LOGGER = logging.getLogger(__name__)

DEFAULT_CFG = ROOT / "config" / "setting_live_trade.json"
LOG_FILE = ROOT / "logs" / "run.log"


def _load_config(path: Path) -> dict:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


def _load_latest_signal(json_dir: Path) -> dict:
    """Return contents of the newest JSON file in *json_dir*."""
    json_files = list(json_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {json_dir}")
    latest = max(json_files, key=lambda p: p.stat().st_mtime)
    return json.loads(latest.read_text(encoding="utf-8"))


def _format_summary_message(detail: str, status: str, signal: dict | None) -> str:
    """Return a decorated summary string for notifications."""
    ts = datetime.now().isoformat(timespec="seconds")
    status_icon = "✅" if status == "success" else "⚠️"
    parts = [f"📅 {ts}", f"{status_icon} {detail} ({status})"]
    if signal:
        type_map = {
            "buy_limit": "🟢⬇️",
            "sell_limit": "🔴⬆️",
            "buy_stop": "🟢⬆️",
            "sell_stop": "🔴⬇️",
        }
        order_type = signal.get("pending_order_type")
        emoji = type_map.get(str(order_type).lower(), "")
        parts.extend(
            [
                f"📌 signal_id:{signal.get('signal_id')}",
                f"💰 entry:{signal.get('entry')}",
                f"🛑 sl:{signal.get('sl')}",
                f"🎯 tp:{signal.get('tp')}",
                f"{emoji} pending_order_type:{order_type}",
                f"⭐ confidence:{signal.get('confidence')}",
            ]
        )
    return "\n".join(parts)


def _notify_summary(notify_cfg: dict, entry: str) -> None:
    """Send *entry* via LINE and Telegram if configured."""
    if not notify_cfg:
        return

    line_cfg = notify_cfg.get("line", {})
    if line_cfg.get("enabled") and line_cfg.get("token"):
        LOGGER.info("Sending LINE notification")
        try:
            send_line(entry, line_cfg["token"])
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Notification failed: %s", exc)
        else:
            LOGGER.info("LINE notified")

    telegram_cfg = notify_cfg.get("telegram", {})
    if (
        telegram_cfg.get("enabled")
        and telegram_cfg.get("token")
        and telegram_cfg.get("chat_id")
    ):
        LOGGER.info("Sending Telegram notification")
        try:
            send_telegram(entry, telegram_cfg["token"], telegram_cfg["chat_id"])
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Notification failed: %s", exc)
        else:
            LOGGER.info("Telegram notified")


def _run_workflow() -> None:
    """Execute the main workflow once."""
    LOGGER.info("Starting scheduled workflow run")
    status = "success"
    results: dict[str, str] | None = None
    try:
        results = asyncio.run(run_main())
        if any(v == "error" for v in results.values()):
            status = "error"
    except SystemExit as exc:
        LOGGER.error("main_liveTrade.py exited with code %s", exc.code)
        status = f"exit {exc.code}"
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("main_liveTrade.py failed: %s", exc)
        status = "error"

    detail = " ".join(
        f"{k}:{results.get(k, 'n/a')}" for k in ("fetch", "send", "parse")
    ) if results else ""
    message = ""
    signal = None
    try:
        cfg = _load_config(DEFAULT_CFG)
        parse_cfg = cfg.get("parse", {})
        notify_cfg = cfg.get("notify", {})
        if results and results.get("parse") == "success":
            json_dir = parse_cfg.get(
                "path_signals_json",
                "data/live_trade/signals/signals_json",
            )
            signal = _load_latest_signal(Path(json_dir))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to load config or signal data: %s", exc)
        notify_cfg = {}
    message = _format_summary_message(detail, status, signal)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to update run log: %s", exc)

    _notify_summary(notify_cfg, message)

    if results and results.get("parse") == "success":
        latest_txt = parse_cfg.get(
            "path_latest_response",
            "data/live_trade/signals/latest_response.txt",
        )
        latest_json = Path(latest_txt).with_suffix(".json")
        try:
            TradeSignalSender(str(latest_json))
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to send MT5 signal: %s", exc)
 

def _start_countdown(job) -> None:
    """Display a simple countdown until *job* runs."""

    def _loop() -> None:
        while True:
            next_run = getattr(job, "next_run_time", getattr(job, "next_fire_time", None))
            if next_run is None:
                time.sleep(1)
                continue
            while True:
                remaining = next_run - datetime.now(next_run.tzinfo)
                if remaining.total_seconds() <= 0:
                    break
                hours, rem = divmod(int(remaining.total_seconds()), 3600)
                minutes, seconds = divmod(rem, 60)
                print(
                    f"Next run in {hours:02d}:{minutes:02d}:{seconds:02d}",
                    end="\r",
                    flush=True,
                )
                time.sleep(1)
            time.sleep(1)

    threading.Thread(target=_loop, daemon=True).start()


def main() -> None:
    """Configure and start the hourly scheduler."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    )
    scheduler = BlockingScheduler()
    job = scheduler.add_job(_run_workflow, "interval", seconds=30)
    _start_countdown(job)
    LOGGER.info("Scheduler started; press Ctrl+C to exit")
    try:
        scheduler.start()
        
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover - manual stop
        LOGGER.info("Scheduler stopped")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
    