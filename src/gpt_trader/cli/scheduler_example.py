"""Example scheduler that runs main_liveTrade.py every hour."""
from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import threading
import time

from apscheduler.schedulers.blocking import BlockingScheduler

from gpt_trader.cli.main_liveTrade import main as run_main

LOGGER = logging.getLogger(__name__)


def _run_workflow() -> None:
    """Execute the main workflow once."""
    LOGGER.info("Starting scheduled workflow run")
    try:
        asyncio.run(run_main())
    except SystemExit as exc:
        LOGGER.error("main_liveTrade.py exited with code %s", exc.code)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("main_liveTrade.py failed: %s", exc)


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
