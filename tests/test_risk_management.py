"""Unit tests for risk management helpers."""

from __future__ import annotations

import importlib
from types import ModuleType
import sys

import pytest


def _get_sender():
    mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
    importlib.reload(mod)
    sender = object.__new__(mod.TradeSignalSender)
    sender.risk_per_trade = 1
    sender.entry = 2000
    sender.sl = 1990
    return sender


def _make_mt5_stub() -> ModuleType:
    mt5 = ModuleType("MetaTrader5")
    mt5.ORDER_TYPE_BUY_LIMIT = 2
    mt5.ORDER_TYPE_SELL_LIMIT = 3
    mt5.ORDER_TYPE_BUY_STOP = 4
    mt5.ORDER_TYPE_SELL_STOP = 5
    mt5.TRADE_ACTION_PENDING = 6
    mt5.ORDER_TIME_GTC = 7
    mt5.ORDER_FILLING_RETURN = 8
    mt5.TRADE_RETCODE_DONE = 0
    mt5.initialize = lambda: True
    mt5.shutdown = lambda: None
    mt5.symbols_get = lambda: [type("Sym", (), {"name": "XAUUSDm"})()]
    mt5.symbol_select = lambda *a: True
    tick = type("Tick", (), {"ask": 2000.0, "bid": 1999.0})()
    info = type(
        "Info",
        (),
        {
            "trade_tick_value": 1.0,
            "trade_tick_size": 0.1,
            "volume_min": 0.01,
            "volume_max": 1.0,
            "volume_step": 0.01,
            "point": 0.01,
        },
    )()
    account = type("Acc", (), {"balance": 10000.0})()
    mt5.symbol_info_tick = lambda *a: tick
    mt5.symbol_info = lambda *a: info
    mt5.account_info = lambda: account
    mt5.order_send = lambda o: type("Res", (), {"retcode": 0, "comment": "ok"})()
    mt5.last_error = lambda: (0, "ok")
    return mt5


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


def test_config_risk_overrides_json(tmp_path) -> None:
    mt5 = _make_mt5_stub()
    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
        importlib.reload(mod)
        data = {
            "signal_id": "xauusd-test",
            "entry": 2000,
            "sl": 1990,
            "pending_order_type": "buy_limit",
            "risk_per_trade": 5,
        }
        path = tmp_path / "sig.json"
        path.write_text(importlib.import_module("json").dumps(data))
        sender = mod.TradeSignalSender(str(path), risk_per_trade=2)
        assert sender.risk_per_trade == 2


def test_config_risk_defaults_to_json(tmp_path) -> None:
    mt5 = _make_mt5_stub()
    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
        importlib.reload(mod)
        data = {
            "signal_id": "xauusd-test",
            "entry": 2000,
            "sl": 1990,
            "pending_order_type": "buy_limit",
            "risk_per_trade": 5,
        }
        path = tmp_path / "sig.json"
        path.write_text(importlib.import_module("json").dumps(data))
        sender = mod.TradeSignalSender(str(path))
        assert sender.risk_per_trade == 5


def test_max_risk_scales_with_confidence(tmp_path) -> None:
    mt5 = _make_mt5_stub()
    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
        importlib.reload(mod)
        data = {
            "signal_id": "xauusd-test",
            "entry": 2000,
            "sl": 1990,
            "pending_order_type": "buy_limit",
            "confidence": 80,
        }
        path = tmp_path / "sig.json"
        path.write_text(importlib.import_module("json").dumps(data))
        sender = mod.TradeSignalSender(str(path), max_risk_per_trade=2)
        assert sender.risk_per_trade == pytest.approx(1.6)


def test_max_risk_caps_value(tmp_path) -> None:
    mt5 = _make_mt5_stub()
    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
        importlib.reload(mod)
        data = {
            "signal_id": "xauusd-test",
            "entry": 2000,
            "sl": 1990,
            "pending_order_type": "buy_limit",
            "confidence": 150,
        }
        path = tmp_path / "sig.json"
        path.write_text(importlib.import_module("json").dumps(data))
        sender = mod.TradeSignalSender(str(path), max_risk_per_trade=2)
        assert sender.risk_per_trade == 2


def test_tp_value_preserved(tmp_path) -> None:
    """TP from the JSON signal should not be modified."""
    mt5 = _make_mt5_stub()
    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
        importlib.reload(mod)
        data = {
            "signal_id": "xauusd-test",
            "entry": 2000,
            "sl": 1995,
            "tp": 1990,
            "pending_order_type": "sell_limit",
        }
        path = tmp_path / "sig.json"
        path.write_text(importlib.import_module("json").dumps(data))
        sender = mod.TradeSignalSender(str(path))
        assert sender.tp == 1990

