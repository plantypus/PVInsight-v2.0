# utils/time_series.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass(frozen=True)
class TimeStepInfo:
    minutes: Optional[int]
    source: str  # "header" | "auto" | "unknown"


def parse_time_step_from_header(header_info: Dict[str, str]) -> TimeStepInfo:
    """
    PVSyst TMY header uses:
      #Time Step;h
      #Time Step;5min
    """
    raw = (header_info.get("Time Step") or "").strip().lower()
    if not raw:
        return TimeStepInfo(minutes=None, source="unknown")

    if raw == "h" or raw == "hour" or raw == "1h":
        return TimeStepInfo(minutes=60, source="header")

    if raw.endswith("min"):
        try:
            n = int(raw.replace("min", "").strip())
            return TimeStepInfo(minutes=n, source="header")
        except ValueError:
            return TimeStepInfo(minutes=None, source="unknown")

    # sometimes could be "60min"
    try:
        n = int(raw)
        return TimeStepInfo(minutes=n, source="header")
    except ValueError:
        return TimeStepInfo(minutes=None, source="unknown")


def detect_time_step_from_datetime(df: pd.DataFrame) -> TimeStepInfo:
    if "datetime" not in df.columns or len(df) < 2:
        return TimeStepInfo(minutes=None, source="unknown")

    s = df["datetime"].dropna()
    if len(s) < 2:
        return TimeStepInfo(minutes=None, source="unknown")

    delta = (s.iloc[1] - s.iloc[0]).total_seconds() / 60.0
    if delta <= 0:
        return TimeStepInfo(minutes=None, source="unknown")

    return TimeStepInfo(minutes=int(round(delta)), source="auto")


def resample_to_hourly(
    df: pd.DataFrame,
    sum_cols: List[str],
    mean_cols: List[str],
) -> pd.DataFrame:
    """
    Resample to 1H:
      - sum_cols summed per hour
      - mean_cols averaged per hour
    """
    if "datetime" not in df.columns:
        raise KeyError("df must contain a 'datetime' column for resampling")

    dfi = df.copy().set_index("datetime")

    agg: Dict[str, str] = {}
    for c in sum_cols:
        if c in dfi.columns:
            agg[c] = "sum"
    for c in mean_cols:
        if c in dfi.columns:
            agg[c] = "mean"

    # keep other cols? In v1 we keep only known meteo cols, so no need.
    out = dfi.resample("1h").agg(agg).reset_index()
    return out
