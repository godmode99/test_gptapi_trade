"""Unit tests for risk management helpers."""

from __future__ import annotations

import importlib
from types import ModuleType
import sys

import pytest


def _get_sender():
    mod = importlib.import_module("gpt_trader.cli.lastest_signal_to_mt5")
    importlib.reload(mod)
    sender = object.__new__(mod.TradeSignalSender)
    sender.risk_per_trade = 1
    sender.entry = 2000
    sender.sl = 1990
    return sender


def test_calculate_lot_basic() -> None:
    sender = _get_sender()
    lot = sender.calculate_lot(
        balance=10000,
        tick_value=1.0,
        tick_size=0.1,
        volume_min=0.01,
        volume_max=2.0,
        volume_step=0.01,
    )
    assert lot == 1.0


def test_calculate_lot_zero_sl_raises() -> None:
    sender = _get_sender()
    sender.sl = sender.entry
    with pytest.raises(ValueError):
        sender.calculate_lot(
            balance=10000,
            tick_value=1.0,
            tick_size=0.1,
            volume_min=0.01,
            volume_max=2.0,
            volume_step=0.01,
        )

