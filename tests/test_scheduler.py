from datetime import datetime, time, timezone

from gpt_trader.cli.scheduler_liveTrade import _within_window, _next_window_run


def test_within_window_basic() -> None:
    assert _within_window(
        datetime(2024, 6, 10, 10, 0),
        0,
        time(8, 30),
        4,
        time(23, 35),
    )
    assert not _within_window(
        datetime(2024, 6, 15, 1, 0),
        0,
        time(8, 30),
        4,
        time(23, 35),
    )


def test_within_window_cross_week() -> None:
    start_day = 4  # Friday
    stop_day = 0  # Monday
    assert _within_window(
        datetime(2024, 6, 8, 1, 0),
        start_day,
        time(23, 0),
        stop_day,
        time(5, 0),
    )
    assert not _within_window(
        datetime(2024, 6, 10, 6, 0),
        start_day,
        time(23, 0),
        stop_day,
        time(5, 0),
    )


def test_next_run_waits_until_monday() -> None:
    sunday = datetime(2024, 6, 9, 12, 0)
    next_run = _next_window_run(
        sunday,
        30,
        0,
        time(8, 30),
        4,
        time(23, 35),
    )
    assert next_run == datetime(2024, 6, 10, 8, 30)


def test_next_run_aligns_to_start_time() -> None:
    start = datetime(2024, 6, 9, 17, 21)
    next_run = _next_window_run(
        start,
        30,
        0,
        time(8, 30),
        4,
        time(23, 35),
    )
    assert next_run == datetime(2024, 6, 10, 8, 30)


def test_next_run_timezone_aware() -> None:
    start = datetime(2024, 6, 9, 17, 21, tzinfo=timezone.utc)
    next_run = _next_window_run(
        start,
        30,
        0,
        time(8, 30),
        4,
        time(23, 35),
    )
    assert next_run == datetime(2024, 6, 10, 8, 30, tzinfo=timezone.utc)
