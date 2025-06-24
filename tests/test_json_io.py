import json
from pathlib import Path

import pandas as pd

from gpt_trader.utils import write_json_no_nulls


def test_write_json_no_nulls(tmp_path: Path) -> None:
    df = pd.DataFrame({"a": [1, pd.NA], "b": [2, 3]})
    out = tmp_path / "out.json"
    write_json_no_nulls(df, out)
    data = json.loads(out.read_text())
    assert data == [{"a": 1, "b": 2}, {"b": 3}]
