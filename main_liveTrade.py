#!/usr/bin/env python
"""Thin wrapper to run the live trade workflow."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gpt_trader.cli.live_trade_workflow import main  # noqa: E402

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    asyncio.run(main())
