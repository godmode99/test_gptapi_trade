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

LOGGER = logging.getLogger(__name__)

DEFAULT_CFG = ROOT / "config" / "setting_live_trade.json"
LOG_FILE = ROOT / "logs" / "run.log"


def _load_config(path: Path) -> dict:
    """Load JSON configuration from *path*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read config: {exc}") from exc


def _notify_summary(notify_cfg: dict, entry: str) -> None:
    """Send *entry* using the configured notification method."""
    if not notify_cfg or not notify_cfg.get("enabled"):
        return
    method = notify_cfg.get("method", "line")
    token = notify_cfg.get("token", "")
    chat_id = notify_cfg.get("chat_id", "")
    try:
        if method == "telegram":
            send_telegram(entry, token, chat_id)
        else:
            send_line(entry, token)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Notification failed: %s", exc)


def _run_workflow() -> None:
    """Execute the main workflow once."""
    LOGGER.info("Starting scheduled workflow run")
    status = "success"
    try:
        asyncio.run(run_main())
    except SystemExit as exc:
        LOGGER.error("main_liveTrade.py exited with code %s", exc.code)
        status = f"exit {exc.code}"
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("main_liveTrade.py failed: %s", exc)
        status = "error"

    entry = f"{datetime.now().isoformat(timespec='seconds')} - {status}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to update run log: %s", exc)

    try:
        cfg = _load_config(DEFAULT_CFG)
        notify_cfg = cfg.get("notify", {})
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to load notify config: %s", exc)
        notify_cfg = {}
    _notify_summary(notify_cfg, entry)


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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    scheduler = BlockingScheduler()
    job = scheduler.add_job(_run_workflow, "interval", hours=1)
    _start_countdown(job)
    LOGGER.info("Scheduler started; press Ctrl+C to exit")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover - manual stop
        LOGGER.info("Scheduler stopped")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
