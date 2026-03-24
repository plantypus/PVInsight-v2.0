# utils/readers/reader_market_prices_csv.py
from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from core.market_analysis.standardization import (
    ANALYSIS_TIME_STEP_MINUTES,
    CANONICAL_MARKET_COLS,
    CanonicalMarketResult,
    harmonize_market_to_analysis_step,
)

EXPECTED_EXPORT_SCHEMA_VERSION = "market_prices_csv_v1"
CSV_SEPARATOR = ";"
CSV_ENCODING = "utf-8-sig"


# =============================================================================
# Helpers
# =============================================================================

def _parse_header_lines(lines: List[str]) -> Tuple[Dict[str, Any], List[str], int]:
    meta: Dict[str, Any] = {}
    warnings: List[str] = []
    data_start_idx = 0

    for i, raw in enumerate(lines):
        line = raw.strip("\n\r")
        if not line.startswith("#"):
            data_start_idx = i
            break

        content = line[1:].strip()
        parts = content.split(CSV_SEPARATOR)

        if not parts:
            continue

        tag = parts[0].strip()

        if tag == "export_schema_version" and len(parts) >= 2:
            meta["export_schema_version"] = parts[1].strip()

        elif tag == "backend_price_unit" and len(parts) >= 2:
            meta["backend_price_unit"] = parts[1].strip()

        elif tag == "separator" and len(parts) >= 2:
            meta["separator"] = parts[1]

        elif tag == "encoding" and len(parts) >= 2:
            meta["encoding"] = parts[1].strip()

        elif tag == "meta" and len(parts) >= 3:
            key = parts[1].strip()
            value = CSV_SEPARATOR.join(parts[2:]).strip()
            meta[key] = value

        elif tag == "warning" and len(parts) >= 2:
            value = CSV_SEPARATOR.join(parts[1:]).strip()
            warnings.append(value)

    else:
        data_start_idx = len(lines)

    return meta, warnings, data_start_idx


def _coerce_bool_int_series(s: pd.Series) -> pd.Series:
    if s.empty:
        return s

    s2 = s.astype(str).str.strip().str.lower()

    mapping = {
        "1": True,
        "0": False,
        "true": True,
        "false": False,
        "nan": pd.NA,
        "": pd.NA,
        "<na>": pd.NA,
        "none": pd.NA,
    }
    return s2.map(mapping).astype("boolean")


def _coerce_numeric_int(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def _coerce_numeric_float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _parse_datetime_col(s: pd.Series, *, utc: bool = False) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", utc=utc)


def _build_minimal_meta_from_original(df: pd.DataFrame) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    if df.empty:
        meta["n_rows_original"] = 0
        return meta

    meta["n_rows_original"] = int(len(df))
    meta["time_start_original"] = df["timestamp"].min().isoformat()
    meta["time_end_original"] = df["timestamp"].max().isoformat()
    if "is_negative_price" in df.columns:
        meta["negative_hours_original"] = int(df["is_negative_price"].fillna(False).sum())
    return meta


# =============================================================================
# Main reader
# =============================================================================

def read_market_prices_csv(
    source: str | Path | bytes,
) -> CanonicalMarketResult:
    warnings: List[str] = []

    # -------------------------------------------------------------------------
    # Read raw text
    # -------------------------------------------------------------------------
    if isinstance(source, (str, Path)):
        path = Path(source)
        text = path.read_text(encoding=CSV_ENCODING)
        source_name = str(path)
    elif isinstance(source, bytes):
        text = source.decode(CSV_ENCODING)
        source_name = "bytes"
    else:
        raise TypeError("source must be a path, string path, or bytes.")

    lines = text.splitlines()
    if not lines:
        raise ValueError("CSV file is empty.")

    # -------------------------------------------------------------------------
    # Parse header
    # -------------------------------------------------------------------------
    header_meta, header_warnings, data_start_idx = _parse_header_lines(lines)
    warnings.extend(header_warnings)

    export_schema_version = header_meta.get("export_schema_version", "")

    # No warning if schema version is absent but the file is still readable.
    # Only keep the version info when present.
    if export_schema_version:
        if export_schema_version != EXPECTED_EXPORT_SCHEMA_VERSION:
            warnings.append(
                f"Unsupported export schema version '{export_schema_version}'. "
                f"Expected '{EXPECTED_EXPORT_SCHEMA_VERSION}'."
            )

    if data_start_idx >= len(lines):
        raise ValueError("CSV data table not found after metadata header.")

    # -------------------------------------------------------------------------
    # Read data table = original standardized data
    # -------------------------------------------------------------------------
    csv_text = "\n".join(lines[data_start_idx:])
    df = pd.read_csv(
        StringIO(csv_text),
        sep=CSV_SEPARATOR,
        encoding=CSV_ENCODING,
    )

    if df.empty:
        meta = dict(header_meta)
        meta["source_mode"] = "csv"
        meta["input_csv_source"] = source_name
        meta["analysis_time_step_minutes"] = ANALYSIS_TIME_STEP_MINUTES
        return CanonicalMarketResult(
            data_original=df,
            data_analysis=df.copy(),
            meta=meta,
            warnings=warnings + ["CSV data table is empty."],
        )

    required_cols = [
        "timestamp",
        "date",
        "year",
        "month",
        "day",
        "hour",
        "season",
        "bzn",
        "price_eur_per_mwh",
        "is_negative_price",
        "source",
        "source_mode",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            "CSV missing required canonical market column(s): "
            + ", ".join(missing)
        )

    # -------------------------------------------------------------------------
    # Coerce types
    # -------------------------------------------------------------------------
    df["timestamp"] = _parse_datetime_col(df["timestamp"], utc=False)

    if "timestamp_local" in df.columns:
        df["timestamp_local"] = _parse_datetime_col(df["timestamp_local"], utc=True)
    if "timestamp_utc" in df.columns:
        df["timestamp_utc"] = _parse_datetime_col(df["timestamp_utc"], utc=True)

    df["year"] = _coerce_numeric_int(df["year"])
    df["month"] = _coerce_numeric_int(df["month"])
    df["day"] = _coerce_numeric_int(df["day"])
    df["hour"] = _coerce_numeric_int(df["hour"])
    df["price_eur_per_mwh"] = _coerce_numeric_float(df["price_eur_per_mwh"])
    df["is_negative_price"] = _coerce_bool_int_series(df["is_negative_price"])

    if "unix_seconds" in df.columns:
        df["unix_seconds"] = _coerce_numeric_float(df["unix_seconds"])

    # -------------------------------------------------------------------------
    # Validate / clean original data
    # -------------------------------------------------------------------------
    n_before = len(df)
    df = df.dropna(subset=["timestamp", "price_eur_per_mwh"]).copy()
    n_dropped = n_before - len(df)
    if n_dropped > 0:
        warnings.append(f"{n_dropped} row(s) dropped due to invalid timestamp or price.")

    if df.empty:
        meta = dict(header_meta)
        meta["source_mode"] = "csv"
        meta["input_csv_source"] = source_name
        meta["analysis_time_step_minutes"] = ANALYSIS_TIME_STEP_MINUTES
        return CanonicalMarketResult(
            data_original=df,
            data_analysis=df.copy(),
            meta=meta,
            warnings=warnings + ["No valid data rows remain after CSV parsing."],
        )

    df = df.sort_values("timestamp").reset_index(drop=True)

    dup_mask = df["timestamp"].duplicated(keep="first")
    n_dup = int(dup_mask.sum())
    if n_dup > 0:
        warnings.append(f"{n_dup} duplicated market timestamp(s) detected in CSV. Keeping first occurrence.")
        df = df.loc[~dup_mask].copy()

    ordered_original_cols = [
        "timestamp",
        "timestamp_local",
        "timestamp_utc",
        "date",
        "year",
        "month",
        "day",
        "hour",
        "season",
        "bzn",
        "price_eur_per_mwh",
        "is_negative_price",
        "source",
        "source_mode",
        "unix_seconds",
    ]
    data_original = df[[c for c in ordered_original_cols if c in df.columns]].copy()

    # -------------------------------------------------------------------------
    # Recompute analysis data from original data
    # -------------------------------------------------------------------------
    data_analysis, harmon_meta, harmon_warnings = harmonize_market_to_analysis_step(
        data_original,
        analysis_step_minutes=ANALYSIS_TIME_STEP_MINUTES,
    )
    warnings.extend(harmon_warnings)

    # -------------------------------------------------------------------------
    # Meta reconstruction
    # -------------------------------------------------------------------------
    meta = dict(header_meta)
    meta["source_mode"] = "csv"
    meta["input_csv_source"] = source_name
    meta["analysis_time_step_minutes"] = ANALYSIS_TIME_STEP_MINUTES

    derived_meta = _build_minimal_meta_from_original(data_original)
    meta.update(derived_meta)
    meta.update(harmon_meta)

    if not data_analysis.empty:
        meta["n_rows_analysis"] = int(len(data_analysis))
        meta["time_start_analysis"] = data_analysis["timestamp"].min().isoformat()
        meta["time_end_analysis"] = data_analysis["timestamp"].max().isoformat()
        meta["negative_hours_analysis"] = int(data_analysis["is_negative_price"].sum())
    else:
        meta["n_rows_analysis"] = 0

    return CanonicalMarketResult(
        data_original=data_original,
        data_analysis=data_analysis,
        meta=meta,
        warnings=warnings,
    )