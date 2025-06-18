from pathlib import Path

from gpt_trader.send.send_to_gpt import _build_messages


def test_build_messages() -> None:
    messages = _build_messages("a,b", "Prompt")
    assert messages[0]["role"] == "system"
    assert "trading data" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "Prompt" in messages[1]["content"]
    assert "a,b" in messages[1]["content"]
