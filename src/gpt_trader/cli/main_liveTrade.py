#!/usr/bin/env python
"""Bridge module to run ``main_liveTrade`` from the package."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add repository root so the top-level module can be imported
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main_liveTrade import main  # type: ignore  # noqa: E402

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    asyncio.run(main())
