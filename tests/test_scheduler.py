from datetime import datetime, time

from gpt_trader.cli.scheduler_liveTrade import _within_window


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
