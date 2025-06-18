import sys
from pathlib import Path
from unittest.mock import patch

import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_trade.main_liveTrade import _run_step


class DummyProc:
    def __init__(self):
        self.returncode = 0

    async def communicate(self):
        pass


def _fake_exec(*cmd):
    _fake_exec.called = cmd
    return DummyProc()


def test_run_step_py_module():
    script = Path("scripts/fetch/fetch_mt5_data.py")
    with patch("asyncio.create_subprocess_exec", side_effect=_fake_exec):
        asyncio.run(_run_step("fetch", script, "--foo"))
    assert _fake_exec.called[0] == sys.executable
    assert _fake_exec.called[1] == "-m"
    assert _fake_exec.called[2].endswith("scripts.fetch.fetch_mt5_data")
    assert _fake_exec.called[3:] == ("--foo",)


def test_run_step_non_py():
    script = Path("scripts/install_deps.sh")
    with patch("asyncio.create_subprocess_exec", side_effect=_fake_exec):
        asyncio.run(_run_step("install", script, "arg"))
    assert _fake_exec.called == (sys.executable, str(script), "arg")

