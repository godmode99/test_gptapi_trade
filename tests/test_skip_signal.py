from types import ModuleType
import importlib
import sys
import json
from pathlib import Path


def test_skip_signal_no_mt5_calls(tmp_path: Path) -> None:
    data = {
        "signal_id": "xauusd-test",
        "pending_order_type": "skip",
        "short_reason": "r",
    }
    sig = tmp_path / "sig.json"
    sig.write_text(json.dumps(data))

    mt5 = ModuleType("MetaTrader5")
    calls: list[str] = []
    mt5.initialize = lambda: calls.append("init") or True
    mt5.shutdown = lambda: calls.append("shutdown")

    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
        importlib.reload(mod)
        mod.TradeSignalSender(str(sig))

    assert calls == []


def test_skip_signal_numeric_id(tmp_path: Path) -> None:
    data = {
        "signal_id": 123,
        "pending_order_type": "skip",
    }
    sig = tmp_path / "sig.json"
    sig.write_text(json.dumps(data))

    mt5 = ModuleType("MetaTrader5")
    calls: list[str] = []
    mt5.initialize = lambda: calls.append("init") or True
    mt5.shutdown = lambda: calls.append("shutdown")

    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
        importlib.reload(mod)
        mod.TradeSignalSender(str(sig))

    assert calls == []
