"""Unit tests for symbol mapping logic."""

from types import ModuleType
import importlib
import sys


def test_find_matching_symbol_uses_map(tmp_path):
    """Mapped symbols should be returned instead of scanning mt5 symbols."""

    mt5 = ModuleType("MetaTrader5")
    mt5.symbols_get = lambda: [type("Sym", (), {"name": "OTHER"})()]

    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.cli.latest_signal_to_mt5")
        importlib.reload(mod)

        sender = object.__new__(mod.TradeSignalSender)
        sender.symbol_map = {"XAUUSDM": "XAUUSDm"}

        assert sender.find_matching_symbol("XAUUSDM") == "XAUUSDm"

