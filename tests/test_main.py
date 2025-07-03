import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

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
        [
            "src/gpt_trader/cli/live_trade_workflow.py",
            "--config",
            str(cfg_path),
            "--skip-send",
            "--skip-parse",
        ],
    ), patch("gpt_trader.cli.common._run_step", fake_run):
        asyncio.run(entry_main())

    fetch_script, fetch_args = called["fetch"]
    assert str(fetch_script).endswith("src/gpt_trader/fetch/fetch_mt5_data.py")
    assert "--config" in fetch_args


def test_time_fetch_passed(tmp_path):
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
        [
            "src/gpt_trader/cli/live_trade_workflow.py",
            "--config",
            str(cfg_path),
            "--skip-send",
            "--skip-parse",
        ],
    ), patch("gpt_trader.cli.common._run_step", fake_run):
        asyncio.run(entry_main())

    assert recorded["fetch"]["time_fetch"] == "2024-01-01 00:00:00"


def test_post_signal_called(tmp_path):
    cfg = {
        "workflow": {
            "scripts": {
                "fetch": "f.py",
                "send": "s.py",
                "parse": "p.py",
            },
            "response": str(tmp_path / "resp.txt"),
            "skip": {"fetch": True, "send": True, "parse": False},
        },
        "parse": {"path_latest_response": str(tmp_path / "resp.txt")},
        "signal_api": {"base_url": "http://api", "auth_token": "t"},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    async def fake_run(step, script, *args):
        if step == "parse":
            (tmp_path / "resp.json").write_text(json.dumps({"ok": 1}))

    with patch.object(
        sys,
        "argv",
        ["src/gpt_trader/cli/live_trade_workflow.py", "--config", str(cfg_path)],
    ), patch("gpt_trader.cli.common._run_step", fake_run), patch(
        "gpt_trader.utils.api_client.post_signal"
    ) as post_fn:
        asyncio.run(entry_main())

    post_fn.assert_called_once()


def test_post_signal_neon_called(tmp_path):
    cfg = {
        "workflow": {
            "scripts": {"fetch": "f.py", "send": "s.py", "parse": "p.py"},
            "response": str(tmp_path / "resp.txt"),
            "skip": {"fetch": True, "send": True, "parse": False},
        },
        "parse": {"path_latest_response": str(tmp_path / "resp.txt")},
        "neon": {"api_url": "http://neon"},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    async def fake_run(step, script, *args):
        if step == "parse":
            (tmp_path / "resp.json").write_text(json.dumps({"ok": 1}))

    with patch.object(
        sys,
        "argv",
        ["src/gpt_trader/cli/live_trade_workflow.py", "--config", str(cfg_path)],
    ), patch("gpt_trader.cli.common._run_step", fake_run), patch(
        "gpt_trader.utils.api_client.post_signal"
    ) as post_fn:
        asyncio.run(entry_main())

    post_fn.assert_called_once()


def test_post_signal_neon_disabled(tmp_path):
    cfg = {
        "workflow": {
            "scripts": {"fetch": "f.py", "send": "s.py", "parse": "p.py"},
            "response": str(tmp_path / "resp.txt"),
            "skip": {"fetch": True, "send": True, "parse": False},
        },
        "parse": {"path_latest_response": str(tmp_path / "resp.txt")},
        "neon": {"api_url": "http://neon", "enabled": False},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    async def fake_run(step, script, *args):
        if step == "parse":
            (tmp_path / "resp.json").write_text(json.dumps({"ok": 1}))

    with patch.object(
        sys,
        "argv",
        ["src/gpt_trader/cli/live_trade_workflow.py", "--config", str(cfg_path)],
    ), patch("gpt_trader.cli.common._run_step", fake_run), patch(
        "gpt_trader.utils.api_client.post_signal"
    ) as post_fn:
        asyncio.run(entry_main())

    post_fn.assert_not_called()


def test_post_signal_api_disabled(tmp_path):
    cfg = {
        "workflow": {
            "scripts": {"fetch": "f.py", "send": "s.py", "parse": "p.py"},
            "response": str(tmp_path / "resp.txt"),
            "skip": {"fetch": True, "send": True, "parse": False},
        },
        "parse": {"path_latest_response": str(tmp_path / "resp.txt")},
        "signal_api": {
            "base_url": "http://api",
            "auth_token": "t",
            "enabled": False,
        },
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    async def fake_run(step, script, *args):
        if step == "parse":
            (tmp_path / "resp.json").write_text(json.dumps({"ok": 1}))

    with patch.object(
        sys,
        "argv",
        ["src/gpt_trader/cli/live_trade_workflow.py", "--config", str(cfg_path)],
    ), patch("gpt_trader.cli.common._run_step", fake_run), patch(
        "gpt_trader.utils.api_client.post_signal"
    ) as post_fn:
        asyncio.run(entry_main())

    post_fn.assert_not_called()


def test_post_signal_api_string_disabled(tmp_path):
    cfg = {
        "workflow": {
            "scripts": {"fetch": "f.py", "send": "s.py", "parse": "p.py"},
            "response": str(tmp_path / "resp.txt"),
            "skip": {"fetch": True, "send": True, "parse": False},
        },
        "parse": {"path_latest_response": str(tmp_path / "resp.txt")},
        "signal_api": {
            "base_url": "http://api",
            "auth_token": "t",
            "enabled": "false",
        },
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    async def fake_run(step, script, *args):
        if step == "parse":
            (tmp_path / "resp.json").write_text(json.dumps({"ok": 1}))

    with patch.object(
        sys,
        "argv",
        ["src/gpt_trader/cli/live_trade_workflow.py", "--config", str(cfg_path)],
    ), patch("gpt_trader.cli.common._run_step", fake_run), patch(
        "gpt_trader.utils.api_client.post_signal"
    ) as post_fn:
        asyncio.run(entry_main())

    post_fn.assert_not_called()


def test_notify_called(tmp_path):
    cfg = {
        "notify": {
            "line": {"enabled": True, "token": "t"},
            "telegram": {"enabled": True, "token": "tg", "chat_id": "id"},
        },
        "account_name": "acc",
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(
        sched,
        "run_main",
        return_value={"fetch": "success", "send": "success", "parse": "success"},
    ), patch.object(
        sched,
        "_load_latest_signal",
        return_value={
            "signal_id": "id",
            "entry": 1,
            "sl": 2,
            "tp": 3,
            "pending_order_type": "buy_limit",
            "confidence": 55,
            "regime_type": "trend",
            "short_reason": "r",
        },
    ), patch.object(
        sched, "send_line"
    ) as line_fn, patch.object(
        sched, "send_telegram"
    ) as tg_fn, patch.object(
        sched, "TradeSignalSender"
    ) as sender_cls:
        mock_sender = MagicMock()
        mock_sender.lot = 0.1
        mock_sender.rr = 1.5
        mock_sender.risk_per_trade = 1.0
        mock_sender.order_result = "success"
        sender_cls.return_value = mock_sender
        sched._run_workflow()
    line_fn.assert_called()
    tg_fn.assert_called()
    assert "account:acc" in line_fn.call_args[0][0]
    assert "signal_id:id" in line_fn.call_args[0][0]
    assert "regime_type: trend" in line_fn.call_args[0][0]
    assert "risk_per_trade:" in line_fn.call_args[0][0]
    assert "short_reason:" in line_fn.call_args[0][0]
    assert "order:success" in line_fn.call_args[0][0]


def test_notify_line_only(tmp_path):
    cfg = {
        "notify": {
            "line": {"enabled": True, "token": "t"},
            "telegram": {"enabled": False, "token": "", "chat_id": ""},
        },
        "account_name": "acc",
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(
        sched,
        "run_main",
        return_value={"fetch": "success", "send": "success", "parse": "success"},
    ), patch.object(
        sched,
        "_load_latest_signal",
        return_value={
            "signal_id": "id",
            "entry": 1,
            "sl": 2,
            "tp": 3,
            "pending_order_type": "buy_limit",
            "confidence": 55,
            "regime_type": "trend",
            "short_reason": "r",
        },
    ), patch.object(
        sched, "send_line"
    ) as line_fn, patch.object(
        sched, "send_telegram"
    ) as tg_fn, patch.object(
        sched, "TradeSignalSender"
    ) as sender_cls:
        mock_sender = MagicMock()
        mock_sender.lot = 0.1
        mock_sender.rr = 1.5
        mock_sender.risk_per_trade = 1.0
        mock_sender.order_result = "success"
        sender_cls.return_value = mock_sender
        sched._run_workflow()
    line_fn.assert_called()
    tg_fn.assert_not_called()
    assert "account:acc" in line_fn.call_args[0][0]
    assert "risk_per_trade:" in line_fn.call_args[0][0]
    assert "order:success" in line_fn.call_args[0][0]


def test_notify_telegram_only(tmp_path):
    cfg = {
        "notify": {
            "line": {"enabled": False, "token": ""},
            "telegram": {"enabled": True, "token": "tg", "chat_id": "id"},
        },
        "account_name": "acc",
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(
        sched,
        "run_main",
        return_value={"fetch": "success", "send": "success", "parse": "success"},
    ), patch.object(
        sched,
        "_load_latest_signal",
        return_value={
            "signal_id": "id",
            "entry": 1,
            "sl": 2,
            "tp": 3,
            "pending_order_type": "buy_limit",
            "confidence": 55,
            "regime_type": "trend",
            "short_reason": "r",
        },
    ), patch.object(
        sched, "send_line"
    ) as line_fn, patch.object(
        sched, "send_telegram"
    ) as tg_fn, patch.object(
        sched, "TradeSignalSender"
    ) as sender_cls:
        mock_sender = MagicMock()
        mock_sender.lot = 0.1
        mock_sender.rr = 1.5
        mock_sender.risk_per_trade = 1.0
        mock_sender.order_result = "success"
        sender_cls.return_value = mock_sender
        sched._run_workflow()
    line_fn.assert_not_called()
    tg_fn.assert_called()
    assert "account:acc" in tg_fn.call_args[0][0]
    assert "risk_per_trade:" in tg_fn.call_args[0][0]
    assert "order:success" in tg_fn.call_args[0][0]


def test_order_before_notification(tmp_path):
    cfg = {
        "notify": {
            "line": {"enabled": True, "token": "t"},
            "telegram": {"enabled": False},
        },
        "account_name": "acc",
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    calls: list[str] = []

    def record_notify(*_args, **_kw):
        calls.append("notify")

    def record_order(*_args, **_kw):
        calls.append("order")
        mock = MagicMock()
        mock.lot = 0.1
        mock.rr = 1.5
        mock.risk_per_trade = 1.0
        mock.order_result = "success"
        return mock

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(
        sched,
        "run_main",
        return_value={"fetch": "success", "send": "success", "parse": "success"},
    ), patch.object(
        sched,
        "_load_latest_signal",
        return_value={
            "signal_id": "id",
            "entry": 1,
            "sl": 2,
            "tp": 3,
            "pending_order_type": "buy_limit",
            "confidence": 55,
            "regime_type": "trend",
            "short_reason": "r",
        },
    ), patch.object(
        sched, "send_line", side_effect=record_notify
    ) as line_fn, patch.object(
        sched, "send_telegram"
    ), patch.object(
        sched, "TradeSignalSender", side_effect=record_order
    ):
        sched._run_workflow()

    assert calls == ["order", "notify"]
    msg = line_fn.call_args[0][0]
    assert "account:acc" in msg
    assert "lot:" in msg
    assert "rr:" in msg
    assert "risk_per_trade:" in msg
    assert "regime_type: trend" in msg
    assert "short_reason:" in msg
    assert "order:success" in msg


def test_notify_saved_to_db(tmp_path):
    cfg = {
        "notify": {"line": {"enabled": True, "token": "t"}},
        "neon": {"api_url": "http://db"},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(
        sched,
        "run_main",
        return_value={"fetch": "success", "send": "success", "parse": "success"},
    ), patch.object(
        sched,
        "_load_latest_signal",
        return_value={
            "signal_id": "id",
            "entry": 1,
            "sl": 2,
            "tp": 3,
            "pending_order_type": "buy_limit",
            "confidence": 55,
        },
    ), patch.object(
        sched, "send_line"
    ), patch.object(
        sched, "send_telegram"
    ), patch.object(
        sched, "TradeSignalSender"
    ) as sender_cls, patch(
        "gpt_trader.utils.api_client.post_event"
    ) as event_fn:
        mock_sender = MagicMock()
        mock_sender.lot = 0.1
        mock_sender.rr = 1.5
        mock_sender.risk_per_trade = 1.0
        mock_sender.order_result = "success"
        sender_cls.return_value = mock_sender
        sched._run_workflow()

    event_fn.assert_called_once()


def test_notify_not_saved_to_db(tmp_path):
    cfg = {
        "notify": {"line": {"enabled": True, "token": "t"}},
        "neon": {"api_url": "http://db", "enabled": False},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(
        sched,
        "run_main",
        return_value={"fetch": "success", "send": "success", "parse": "success"},
    ), patch.object(
        sched,
        "_load_latest_signal",
        return_value={
            "signal_id": "id",
            "entry": 1,
            "sl": 2,
            "tp": 3,
            "pending_order_type": "buy_limit",
            "confidence": 55,
        },
    ), patch.object(
        sched, "send_line"
    ), patch.object(
        sched, "send_telegram"
    ), patch.object(
        sched, "TradeSignalSender"
    ) as sender_cls, patch(
        "gpt_trader.utils.api_client.post_event"
    ) as event_fn:
        mock_sender = MagicMock()
        mock_sender.lot = 0.1
        mock_sender.rr = 1.5
        mock_sender.risk_per_trade = 1.0
        mock_sender.order_result = "success"
        sender_cls.return_value = mock_sender
        sched._run_workflow()

    event_fn.assert_not_called()


def test_post_signal_error_detail(tmp_path):
    cfg = {"notify": {"line": {"enabled": True, "token": "t"}}}
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(
        sched,
        "run_main",
        return_value={
            "fetch": "success",
            "send": "success",
            "parse": "success",
            "post_signal": "error",
        },
    ), patch.object(
        sched,
        "_load_latest_signal",
        return_value={
            "signal_id": "id",
            "entry": 1,
            "sl": 2,
            "tp": 3,
            "pending_order_type": "buy_limit",
            "confidence": 55,
        },
    ), patch.object(
        sched, "send_line"
    ) as line_fn, patch.object(
        sched, "send_telegram"
    ), patch.object(
        sched, "TradeSignalSender"
    ) as sender_cls:
        mock_sender = MagicMock()
        mock_sender.lot = 0.1
        mock_sender.rr = 1.5
        mock_sender.risk_per_trade = 1.0
        mock_sender.order_result = "success"
        sender_cls.return_value = mock_sender
        sched._run_workflow()

    msg = line_fn.call_args[0][0]
    assert "post_signal:error" in msg


def test_post_event_error_detail(tmp_path):
    cfg = {
        "notify": {"line": {"enabled": True, "token": "t"}},
        "neon": {"api_url": "http://db"},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))
    log_path = tmp_path / "run.log"

    import gpt_trader.cli.scheduler_liveTrade as sched

    with patch.object(sched, "DEFAULT_CFG", cfg_path), patch.object(
        sched, "LOG_FILE", log_path
    ), patch.object(
        sched,
        "run_main",
        return_value={
            "fetch": "success",
            "send": "success",
            "parse": "success",
        },
    ), patch.object(
        sched,
        "_load_latest_signal",
        return_value={
            "signal_id": "id",
            "entry": 1,
            "sl": 2,
            "tp": 3,
            "pending_order_type": "buy_limit",
            "confidence": 55,
        },
    ), patch.object(
        sched, "send_line"
    ) as line_fn, patch.object(
        sched, "send_telegram"
    ), patch.object(
        sched, "TradeSignalSender"
    ) as sender_cls, patch(
        "gpt_trader.utils.api_client.post_event",
        side_effect=RuntimeError("fail"),
    ):
        mock_sender = MagicMock()
        mock_sender.lot = 0.1
        mock_sender.rr = 1.5
        mock_sender.risk_per_trade = 1.0
        mock_sender.order_result = "success"
        sender_cls.return_value = mock_sender
        sched._run_workflow()

    msg = line_fn.call_args[0][0]
    assert "post_event:error" in msg
