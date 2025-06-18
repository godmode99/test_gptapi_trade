"""Wrapper to launch main_liveTrade from the repository root."""
from __future__ import annotations

from main_liveTrade import main

__all__ = ["main"]

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
