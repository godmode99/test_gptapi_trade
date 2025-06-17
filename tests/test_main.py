import sys
import json
from pathlib import Path
from unittest.mock import patch

import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import main as entry_main


def test_default_fetcher_loaded(tmp_path):
    cfg = {
        "fetch_type": "yf",
        "fetch_script": None,
        "send_script": "scripts/send_api/send_to_gpt.py",
        "parse_script": "scripts/parse_response/parse_gpt_response.py",
        "response": "resp.txt",
        "skip_fetch": False,
        "skip_send": True,
        "skip_parse": True,
        "fetch_config": {"symbol": "TEST"},
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg))

    called = {}

    async def fake_run(step, script, *args):
        called[step] = (script, args)

    with patch.object(sys, "argv", ["main.py", "--config", str(cfg_path), "--skip-send", "--skip-parse"]), patch("main._run_step", fake_run):
        asyncio.run(entry_main())

    fetch_script, fetch_args = called["fetch"]
    assert str(fetch_script).endswith("scripts/fetch/fetch_yf_data.py")
    assert "--config" in fetch_args
