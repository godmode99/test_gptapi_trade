import logging
import json
import sys
import importlib
from types import ModuleType, SimpleNamespace

import pandas as pd
import pytest


def _make_mt5_stub(sample_time):
    mt5 = ModuleType("MetaTrader5")
    mt5.initialize = lambda: True
    mt5.shutdown = lambda: None
    deal = SimpleNamespace(ticket=1, time=int(sample_time.timestamp()))
    mt5.history_deals_get = lambda start, end: [deal]
    return mt5


def test_fetch_history_tz_shift() -> None:
    sample_time = pd.Timestamp("2024-01-01 00:00:00")
    mt5 = _make_mt5_stub(sample_time)
    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.fetch.fetch_mt5_history")
        importlib.reload(mod)
        cfg = {"start": "2024-01-01 00:00:00", "end": "2024-01-01 01:00:00"}
        df = mod.fetch_history(cfg, tz_shift=2)
    expected = sample_time + pd.Timedelta(hours=2)
    assert df["time"].iloc[0] == expected


def test_fetch_history_invalid_time() -> None:
    mt5 = _make_mt5_stub(pd.Timestamp("2024-01-01"))
    with importlib.import_module("unittest.mock").patch.dict(sys.modules, {"MetaTrader5": mt5}):
        mod = importlib.import_module("gpt_trader.fetch.fetch_mt5_history")
        importlib.reload(mod)
        cfg = {"start": "bad", "end": "2024-01-01"}
        with pytest.raises(ValueError):
            mod.fetch_history(cfg)


def test_main_writes_csv(tmp_path) -> None:
    cfg = {
        "start": "2024-01-01 00:00:00",
        "end": "2024-01-01 01:00:00",
        "save_as_path": str(tmp_path),
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    df = pd.DataFrame({"time": [pd.Timestamp("2024-01-01")]})

    with importlib.import_module("unittest.mock").patch.object(
        sys,
        "argv",
        ["fetch_mt5_history.py", "--config", str(cfg_path)],
    ), importlib.import_module("unittest.mock").patch(
        "gpt_trader.fetch.fetch_mt5_history.fetch_history", return_value=df
    ), importlib.import_module("unittest.mock").patch(
        "gpt_trader.fetch.fetch_mt5_history._init_mt5"
    ), importlib.import_module("unittest.mock").patch(
        "gpt_trader.fetch.fetch_mt5_history._shutdown_mt5"
    ):
        importlib.import_module("gpt_trader.fetch.fetch_mt5_history").main()

    csv_files = list(tmp_path.glob("*.csv"))
    assert len(csv_files) == 1
    assert pd.read_csv(csv_files[0]).iloc[0]["time"]


def test_main_error_on_empty_df(tmp_path, caplog) -> None:
    cfg = {
        "start": "2024-01-01 00:00:00",
        "end": "2024-01-01 01:00:00",
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    with importlib.import_module("unittest.mock").patch.object(
        sys,
        "argv",
        ["fetch_mt5_history.py", "--config", str(cfg_path)],
    ), importlib.import_module("unittest.mock").patch(
        "gpt_trader.fetch.fetch_mt5_history.fetch_history", return_value=pd.DataFrame()
    ), importlib.import_module("unittest.mock").patch(
        "gpt_trader.fetch.fetch_mt5_history._init_mt5"
    ), importlib.import_module("unittest.mock").patch(
        "gpt_trader.fetch.fetch_mt5_history._shutdown_mt5"
    ):
        with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
            importlib.import_module("gpt_trader.fetch.fetch_mt5_history").main()
        assert exc.value.code == 1
        assert "No trade history" in caplog.text
