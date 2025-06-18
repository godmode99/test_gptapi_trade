"""Wrapper to launch main_liveTrade from the repository root."""
from __future__ import annotations

from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from main_liveTrade import main

__all__ = ["main"]

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
