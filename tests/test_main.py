import sys
import json
from pathlib import Path
from unittest.mock import patch

import asyncio

from gpt_trader.cli.main_liveTrade import main as entry_main


def test_default_fetcher_loaded(tmp_path):
    cfg = {
        "workflow": {
            "fetch_type": "mt5",
            "scripts": {
                "fetch": None,
                "send": "scripts/send_api/send_to_gpt.py",
                "parse": "scripts/parse_response/parse_gpt_response.py",
            },
            "response": "resp.txt",
            "skip": {"fetch": False, "send": True, "parse": True},
        },
        "fetch": {"symbol": "TEST"},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    called = {}

    async def fake_run(step, script, *args):
        called[step] = (script, args)

    with patch.object(
        sys,
        "argv",
        ["src/gpt_trader/cli/main_liveTrade.py", "--config", str(cfg_path), "--skip-send", "--skip-parse"],
    ), patch("gpt_trader.cli.common._run_step", fake_run):
        asyncio.run(entry_main())

    fetch_script, fetch_args = called["fetch"]
    assert str(fetch_script).endswith("src/gpt_trader/fetch/fetch_mt5_data.py")
    assert "--config" in fetch_args


def test_time_fetch_passed(tmp_path):
    cfg = {
        "workflow": {
            "fetch_type": "mt5",
            "scripts": {"fetch": None,
                        "send": "scripts/send_api/send_to_gpt.py",
                        "parse": "scripts/parse_response/parse_gpt_response.py"},
            "response": "resp.txt",
            "skip": {"fetch": False, "send": True, "parse": True},
        },
        "fetch": {"symbol": "TEST", "time_fetch": "2024-01-01 00:00:00"},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    recorded = {}

    async def fake_run(step, script, *args):
        idx = args.index("--config") + 1
        cfg_file = Path(args[idx])
        recorded[step] = json.loads(cfg_file.read_text())

    with patch.object(
        sys,
        "argv",
        ["src/gpt_trader/cli/main_liveTrade.py", "--config", str(cfg_path), "--skip-send", "--skip-parse"],
    ), patch("gpt_trader.cli.common._run_step", fake_run):
        asyncio.run(entry_main())

    assert recorded["fetch"]["time_fetch"] == "2024-01-01 00:00:00"


def test_notify_called(tmp_path):
    cfg = {
        "notify": {
            "line": {"enabled": True, "token": "t"},
            "telegram": {"enabled": True, "token": "tg", "chat_id": "id"},
        }
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(sched, "run_main", return_value={"fetch": "success", "send": "success", "parse": "success"}), patch.object(sched, "_load_latest_signal", return_value={"signal_id": "id", "entry": 1, "sl": 2, "tp": 3, "pending_order_type": "buy_limit", "confidence": 55}), patch.object(sched, "send_line") as line_fn, patch.object(sched, "send_telegram") as tg_fn, patch.object(sched, "TradeSignalSender") as sender_cls:
        sched._run_workflow()
    line_fn.assert_called()
    tg_fn.assert_called()
    assert "signal_id:id" in line_fn.call_args[0][0]


def test_notify_line_only(tmp_path):
    cfg = {
        "notify": {
            "line": {"enabled": True, "token": "t"},
            "telegram": {"enabled": False, "token": "", "chat_id": ""},
        }
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(sched, "run_main", return_value={"fetch": "success", "send": "success", "parse": "success"}), patch.object(sched, "_load_latest_signal", return_value={"signal_id": "id", "entry": 1, "sl": 2, "tp": 3, "pending_order_type": "buy_limit", "confidence": 55}), patch.object(sched, "send_line") as line_fn, patch.object(sched, "send_telegram") as tg_fn, patch.object(sched, "TradeSignalSender") as sender_cls:
        sched._run_workflow()
    line_fn.assert_called()
    tg_fn.assert_not_called()


def test_notify_telegram_only(tmp_path):
    cfg = {
        "notify": {
            "line": {"enabled": False, "token": ""},
            "telegram": {"enabled": True, "token": "tg", "chat_id": "id"},
        }
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(sched, "run_main", return_value={"fetch": "success", "send": "success", "parse": "success"}), patch.object(sched, "_load_latest_signal", return_value={"signal_id": "id", "entry": 1, "sl": 2, "tp": 3, "pending_order_type": "buy_limit", "confidence": 55}), patch.object(sched, "send_line") as line_fn, patch.object(sched, "send_telegram") as tg_fn, patch.object(sched, "TradeSignalSender") as sender_cls:
        sched._run_workflow()
    line_fn.assert_not_called()
    tg_fn.assert_called()
