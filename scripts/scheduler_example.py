"""Example scheduler that runs main.py every hour."""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from main import main as run_main

LOGGER = logging.getLogger(__name__)


def _run_workflow() -> None:
    """Execute the main workflow once."""
    LOGGER.info("Starting scheduled workflow run")
    try:
        asyncio.run(run_main())
    except SystemExit as exc:
        LOGGER.error("main.py exited with code %s", exc.code)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("main.py failed: %s", exc)


def main() -> None:
    """Configure and start the hourly scheduler."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    scheduler = BlockingScheduler()
    scheduler.add_job(_run_workflow, "interval", hours=1)
    LOGGER.info("Scheduler started; press Ctrl+C to exit")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover - manual stop
        LOGGER.info("Scheduler stopped")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
