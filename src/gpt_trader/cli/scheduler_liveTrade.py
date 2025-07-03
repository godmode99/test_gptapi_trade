"""Schedule :mod:`main_liveTrade.py` at a configurable interval."""
from __future__ import annotations

import argparse
import asyncio
import json
import math
from datetime import datetime, timedelta, time as dt_time
import logging
import threading
import time

from apscheduler.schedulers.blocking import BlockingScheduler


from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gpt_trader.cli.live_trade_workflow import main as run_main
from gpt_trader.notify import send_line, send_telegram
from gpt_trader.cli.latest_signal_to_mt5 import TradeSignalSender
from gpt_trader.utils import post_event

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


DAY_MAP = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def _parse_day(value: str) -> int:
    """Return weekday index for *value* or raise ``ArgumentTypeError``."""
    try:
        return DAY_MAP[value.strip().lower()]
    except KeyError as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError(f"Invalid day: {value}") from exc


def _parse_time(value: str) -> dt_time:
    """Return ``datetime.time`` parsed from HH:MM string."""
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError(f"Invalid time: {value}") from exc


def _minutes_from_day(day: int, t: dt_time) -> int:
    """Convert day/time to minutes since Monday."""
    return day * 24 * 60 + t.hour * 60 + t.minute


def _within_window(
    now: datetime,
    start_day: int,
    start_time: dt_time,
    stop_day: int,
    stop_time: dt_time,
) -> bool:
    """Return ``True`` if *now* falls within the active schedule."""
    start_idx = _minutes_from_day(start_day, start_time)
    stop_idx = _minutes_from_day(stop_day, stop_time)
    current_idx = _minutes_from_day(now.weekday(), now.time())
    if start_idx <= stop_idx:
        return start_idx <= current_idx < stop_idx
    return current_idx >= start_idx or current_idx < stop_idx


def _next_window_run(
    next_run: datetime,
    interval: int,
    start_day: int,
    start_time: dt_time,
    stop_day: int,
    stop_time: dt_time,
) -> datetime:
    """Return the first run time >= *next_run* within the active window."""

    start_of_window = datetime.combine(next_run.date(), start_time)
    if next_run.tzinfo is not None and start_of_window.tzinfo is None:
        start_of_window = start_of_window.replace(tzinfo=next_run.tzinfo)
    start_of_window -= timedelta(
        days=(start_of_window.weekday() - start_day) % 7
    )

    diff = (next_run - start_of_window).total_seconds() / 60
    steps = math.ceil(max(0, diff) / max(1, interval))
    next_run = start_of_window + timedelta(minutes=steps * interval)

    for _ in range(int(7 * 24 * 60 / max(1, interval)) + 1):
        if _within_window(next_run, start_day, start_time, stop_day, stop_time):
            return next_run
        next_run += timedelta(minutes=interval)
    return next_run


def _format_summary_message(
    detail: str, status: str, signal: dict | None, account: str | None = None
) -> str:
    """Return a decorated summary string for notifications."""
    ts = datetime.now().isoformat(timespec="seconds")
    status_icon = "✅" if status == "success" else "⚠️"
    parts = [f"📅 {ts}"]
    if account:
        parts.append(f"🏦 account:{account}")
    parts.append(f"{status_icon} {detail} ({status})")
    if signal:
        type_map = {
            "buy_limit": "🟢⬇️",
            "sell_limit": "🔴⬆️",
            "buy_stop": "🟢⬆️",
            "sell_stop": "🔴⬇️",
        }
        order_type = signal.get("pending_order_type")
        emoji = type_map.get(str(order_type).lower(), "")

        basic = [
            f"📌 signal_id:{signal.get('signal_id')}",
            f"💰 entry:{signal.get('entry')}",
            f"🛑 sl:{signal.get('sl')}",
            f"🎯 tp:{signal.get('tp')}",
            f"{emoji} pending_order_type:{order_type}",
            f"⭐ confidence:{signal.get('confidence')}",
        ]
        parts.append("\n".join(basic))

        extra: list[str] = []
        if signal.get("risk_per_trade") is not None:
            try:
                rp_fmt = f"{float(signal['risk_per_trade']):.3f}"
            except Exception:  # noqa: BLE001
                rp_fmt = str(signal['risk_per_trade'])
            extra.append(f"⚖ risk_per_trade:{rp_fmt}%")
        if signal.get("lot") is not None:
            extra.append(f"💵 lot:{signal['lot']}")
        if signal.get("rr") is not None:
            try:
                rr_fmt = f"{float(signal['rr']):.2f}"
            except Exception:
                rr_fmt = str(signal['rr'])
            extra.append(f"📈 rr:{rr_fmt}")
        if signal.get("regime_type") is not None:
            regime = signal["regime_type"]
            if isinstance(regime, dict):
                regime_fmt = ", ".join(
                    f"{k}={v}" for k, v in regime.items()
                )
            else:
                regime_fmt = str(regime)
            extra.append(f"📊 regime_type: {regime_fmt}")
        if extra:
            parts.append("")
            parts.append("\n".join(extra))

        if signal.get("short_reason") is not None:
            parts.append("")
            parts.append(f"📝 short_reason:{signal['short_reason']}")
        if signal.get("order_status") is not None:
            parts.append("")
            parts.append(f"🚩 order:{signal['order_status']}")
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
    order_status: str | None = None
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

    detail_items: list[str] = []
    message = ""
    signal = None
    try:
        cfg = _load_config(DEFAULT_CFG)
        parse_cfg = cfg.get("parse", {})
        notify_cfg = cfg.get("notify", {})
        risk_pct = cfg.get("risk_per_trade")
        max_risk = cfg.get("max_risk_per_trade")
        if results and results.get("parse") == "success":
            json_dir = parse_cfg.get(
                "path_signals_json",
                "data/live_trade/signals/signals_json",
            )
            signal = _load_latest_signal(Path(json_dir))
            latest_txt = parse_cfg.get(
                "path_latest_response",
                "data/live_trade/signals/latest_response.txt",
            )
            latest_json = Path(latest_txt).with_suffix(".json")
            try:
                sender = TradeSignalSender(
                    str(latest_json),
                    risk_per_trade=risk_pct,
                    max_risk_per_trade=max_risk,
                )
                signal["lot"] = sender.lot
                signal["rr"] = sender.rr
                signal["risk_per_trade"] = sender.risk_per_trade
                order_status = sender.order_result
                if getattr(sender, "adjust_note", None):
                    order_status = f"{order_status} {sender.adjust_note}"
                signal["order_status"] = order_status
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Failed to send MT5 signal: %s", exc)
                order_status = "error"
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to load config or signal data: %s", exc)
        notify_cfg = {}

    if results:
        detail_items.extend(
            f"{k}:{results.get(k, 'n/a')}" for k in ("fetch", "send", "parse")
        )
        if "post_signal" in results:
            detail_items.append(f"post_signal:{results['post_signal']}")
    if order_status is not None:
        detail_items.append(f"order:{order_status}")
    detail = " ".join(detail_items)

    account_name = cfg.get("account_name")
    message = _format_summary_message(detail, status, signal, account_name)

    post_event_status: str | None = None
    neon_cfg = cfg.get("neon", {})
    if neon_cfg.get("enabled", True) and neon_cfg.get("api_url"):
        try:
            post_event(
                neon_cfg.get("api_url", ""),
                neon_cfg.get("auth_token", ""),
                {"message": message},
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to save notification to DB: %s", exc)
            post_event_status = "error"
        else:
            post_event_status = "success"

    if post_event_status is not None:
        detail_items.append(f"post_event:{post_event_status}")
        detail = " ".join(detail_items)
        message = _format_summary_message(detail, status, signal, account_name)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to update run log: %s", exc)

    _notify_summary(notify_cfg, message)


def _make_workflow_runner(
    start_day: int,
    start_time: dt_time,
    stop_day: int,
    stop_time: dt_time,
) -> callable:
    """Return function that runs workflow only within the configured window."""

    def _runner() -> None:
        if _within_window(datetime.now(), start_day, start_time, stop_day, stop_time):
            _run_workflow()
        else:
            LOGGER.info("Outside configured window - skipping run")

    return _runner
 


def _start_countdown(
    job,
    interval: int,
    start_day: int,
    start_time: dt_time,
    stop_day: int,
    stop_time: dt_time,
) -> None:
    """Display a simple countdown until the next active job run."""

    def _loop() -> None:
        while True:
            base_run = getattr(job, "next_run_time", getattr(job, "next_fire_time", None))
            if base_run is None:
                time.sleep(1)
                continue
            next_run = _next_window_run(
                base_run, interval, start_day, start_time, stop_day, stop_time
            )
            while True:
                remaining = next_run - datetime.now(next_run.tzinfo)
                if remaining.total_seconds() <= 0:
                    break
                hours, rem = divmod(int(remaining.total_seconds()), 3600)
                minutes, seconds = divmod(rem, 60)
                ts = next_run.strftime("%H:%M:%S")
                print(
                    f"Next run at {ts} ({hours:02d}:{minutes:02d}:{seconds:02d})",
                    end="\r",
                    flush=True,
                )
                time.sleep(1)
            time.sleep(1)

    threading.Thread(target=_loop, daemon=True).start()


def main() -> None:
    """Configure and start the scheduler."""
    parser = argparse.ArgumentParser(description="Run live trade workflow on a schedule")
    parser.add_argument(
        "--interval",
        type=int,

        #### ปรับเวลา loop ทุก n minutes
        default=30,
        help="Minutes between each run",
    )
    parser.add_argument(
        "--start-in",
        type=int,

        ####  ปรับเวลาเริ่มstart ในอีก n minutes
        default=0,
        help="Delay first run by this many minutes",
    )
    parser.add_argument(
        "--start-day",
        default="mon",
        help="Day of week to start running (mon,tue,...)",
    )
    parser.add_argument(
        "--start-time",
        default="08:10",
        help="Time of day to start (HH:MM)",
    )
    parser.add_argument(
        "--stop-day",
        default="fri",
        help="Day of week to stop running",
    )
    parser.add_argument(
        "--stop-time",
        default="23:35",
        help="Time of day to stop (HH:MM)",
    )
    args = parser.parse_args()

    start_day = _parse_day(args.start_day)
    start_time = _parse_time(args.start_time)
    stop_day = _parse_day(args.stop_day)
    stop_time = _parse_time(args.stop_time)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    )

    scheduler = BlockingScheduler()
    first_run = datetime.now() + timedelta(minutes=args.start_in)
    next_exec = _next_window_run(
        first_run, args.interval, start_day, start_time, stop_day, stop_time
    )
    job = scheduler.add_job(
        _make_workflow_runner(start_day, start_time, stop_day, stop_time),
        "interval",
        minutes=args.interval,
        next_run_time=next_exec,
    )

    _start_countdown(job, args.interval, start_day, start_time, stop_day, stop_time)
    LOGGER.info(
        "Scheduler started (initial run at %s, first scheduled run at %s, interval %s minutes, window %s %s to %s %s); press Ctrl+C to exit",
        datetime.now().isoformat(timespec="seconds"),
        next_exec.isoformat(timespec="seconds"),
        args.interval,
        args.start_day,
        args.start_time,
        args.stop_day,
        args.stop_time,
    )

    _run_workflow()

    try:
        scheduler.start()

    except (KeyboardInterrupt, SystemExit):  # pragma: no cover - manual stop
        LOGGER.info("Scheduler stopped")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
    