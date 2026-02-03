# utils/validation.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass(frozen=True)
class DataQuality:
    n_rows: int
    n_nan: int
    n_nat: int
    start: Optional[pd.Timestamp]
    end: Optional[pd.Timestamp]
    expected_rows: Optional[int]
    warning: Optional[str]


def basic_quality_check(df: pd.DataFrame, step_minutes: Optional[int]) -> DataQuality:
    n_rows = len(df)
    n_nat = int(df["datetime"].isna().sum()) if "datetime" in df.columns else 0
    n_nan_total = int(df.isna().sum().sum())
    # remove NaT counted within NaNs if datetime exists
    n_nan = max(0, n_nan_total - n_nat)

    start = df["datetime"].min() if "datetime" in df.columns else None
    end = df["datetime"].max() if "datetime" in df.columns else None

    expected = None
    warning = None
    if step_minutes and start is not None and end is not None and pd.notna(start) and pd.notna(end):
        expected = int(((end - start).total_seconds() / 60.0) / step_minutes) + 1
        if expected != n_rows:
            warning = f"Row count mismatch: got {n_rows}, expected {expected} for step={step_minutes} min."

    return DataQuality(
        n_rows=n_rows,
        n_nan=n_nan,
        n_nat=n_nat,
        start=start,
        end=end,
        expected_rows=expected,
        warning=warning,
    )
