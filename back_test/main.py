#!/usr/bin/env python
"""Compatibility wrapper for main_backtest.py."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    target = Path(__file__).with_name("main_backtest.py")
    sys.argv[0] = str(target)
    runpy.run_path(target, run_name="__main__")
