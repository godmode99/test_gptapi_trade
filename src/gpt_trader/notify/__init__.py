from __future__ import annotations

"""Notification helpers for Line and Telegram."""

import logging

import requests

LOGGER = logging.getLogger(__name__)


def send_line(message: str, token: str) -> None:
    """Send *message* via LINE Notify using *token*."""
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    resp = requests.post(url, headers=headers, data=data, timeout=10)
    try:
        resp.raise_for_status()
        LOGGER.info("LINE notification sent")
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("LINE notify failed: %s", exc)
        raise


def send_telegram(message: str, bot_token: str, chat_id: str) -> None:
    """Send *message* to Telegram *chat_id* using *bot_token*."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    resp = requests.post(url, data=data, timeout=10)
    try:
        resp.raise_for_status()
        LOGGER.info("Telegram notification sent")
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Telegram notify failed: %s", exc)
        raise


__all__ = ["send_line", "send_telegram"]
