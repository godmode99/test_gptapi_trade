from __future__ import annotations

"""Simple HTTP client helpers."""

import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


def post_signal(base_url: str, token: str, data: dict[str, Any]) -> None:
    """POST *data* to ``/signal`` on *base_url* using Bearer *token*."""
    url = base_url.rstrip("/") + "/signal"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=10)
        resp.raise_for_status()
        LOGGER.info("Posted signal to %s", url)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Signal POST failed: %s", exc)
        raise

__all__ = ["post_signal"]
