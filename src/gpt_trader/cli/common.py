"""Utility helpers used across project scripts."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path


async def _run_step(step: str, script: Path, *args: str) -> None:
    """Run a script as a subprocess and wait for it to finish.

    If *script* points to a Python file, run it as a module so the project
    root is on ``sys.path``. Otherwise fall back to executing the file
    directly with the current Python interpreter.
    """
    if script.suffix == ".py":
        root = Path(__file__).resolve().parents[1]
        try:
            rel = script.with_suffix("").resolve().relative_to(root)
            module = ".".join((root.name, *rel.parts))
        except ValueError:
            module = ".".join(script.with_suffix("").parts)
        cmd = [sys.executable, "-m", module, *args]
    else:
        cmd = [sys.executable, str(script), *args]
    logging.info("Running %s: %s", step, " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.communicate()
    if proc.returncode:
        raise RuntimeError(f"{step} failed with code {proc.returncode}")

__all__ = ["_run_step"]
