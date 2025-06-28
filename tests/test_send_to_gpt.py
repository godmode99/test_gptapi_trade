from pathlib import Path

import json

from gpt_trader.send.send_to_gpt import _build_messages, _save_prompt_copy


def test_build_messages() -> None:
    messages = _build_messages("{\"a\":1}", "Prompt")
    assert messages[0]["role"] == "system"
    assert "trading data" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "Prompt" in messages[1]["content"]
    assert "{\"a\":1}" in messages[1]["content"]
    assert "JSON Data:" in messages[1]["content"]


def test_save_prompt_copy(tmp_path: Path) -> None:
    json_path = tmp_path / "foo.json"
    json_text = "{\"a\": 1}"
    json_path.write_text(json_text)
    out_dir = tmp_path / "out"
    _save_prompt_copy(json_path, json_text, "Prompt", out_dir, "foo")
    files = list(out_dir.glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["prompt"] == "Prompt"
    assert data["json"] == {"a": 1}
    assert data["signal_id"] == "foo"
