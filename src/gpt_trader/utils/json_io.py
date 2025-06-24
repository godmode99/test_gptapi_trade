from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def write_json_no_nulls(df: pd.DataFrame, path: Path) -> None:
    """Write *df* to *path* as JSON omitting null values.

    ``pandas.Timestamp`` values are converted to ISO formatted strings so that
    ``json.dumps`` receives only serializable objects.
    """

    records: list[dict[str, Any]] = []
    for record in df.to_dict(orient="records"):
        clean: dict[str, Any] = {}
        for k, v in record.items():
            if pd.isna(v):
                continue
            if isinstance(v, pd.Timestamp):
                v = v.isoformat()
            clean[k] = v
        records.append(clean)
    path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
