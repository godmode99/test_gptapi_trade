from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def write_json_no_nulls(df: pd.DataFrame, path: Path) -> None:
    """Write *df* to *path* as JSON omitting null values."""
    records = []
    for record in df.to_dict(orient="records"):
        clean = {k: v for k, v in record.items() if not pd.isna(v)}
        records.append(clean)
    path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
