# core/market_analysis/export_market_prices_csv.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from core.market_analysis.standardization import (
    BACKEND_PRICE_UNIT,
    CANONICAL_MARKET_COLS,
    CanonicalMarketResult,
)


# =============================================================================
# CSV EXPORT CONVENTIONS
# =============================================================================

EXPORT_SCHEMA_VERSION = "market_prices_csv_v1"
EXPORT_SEPARATOR = ";"
EXPORT_ENCODING = "utf-8-sig"
EXPORT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S%z"


# =============================================================================
# HELPERS
# =============================================================================

def _stringify_meta_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " | ".join(str(v) for v in value)
    if isinstance(value, dict):
        return " | ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def _build_metadata_lines(meta: Dict[str, Any], warnings: Optional[Iterable[str]] = None) -> List[str]:
    """
    Build metadata header lines for the exported CSV.
    Each line starts with '#', so the future reader can easily skip them.
    """
    lines: List[str] = []

    lines.append(f"# export_schema_version{EXPORT_SEPARATOR}{EXPORT_SCHEMA_VERSION}")
    lines.append(f"# backend_price_unit{EXPORT_SEPARATOR}{BACKEND_PRICE_UNIT}")
    lines.append(f"# separator{EXPORT_SEPARATOR}{EXPORT_SEPARATOR}")
    lines.append(f"# encoding{EXPORT_SEPARATOR}{EXPORT_ENCODING}")

    preferred_meta_order = [
        "schema_version",
        "source",
        "source_mode",
        "endpoint",
        "bzn",
        "start",
        "end",
        "backend_price_unit",
        "unit_raw",
        "license_info",
        "deprecated",
        "local_timezone",
        "time_basis_note",
        "n_rows",
        "time_start",
        "time_end",
        "negative_hours",
        "request_url",
    ]

    written_keys = set()

    for key in preferred_meta_order:
        if key in meta:
            lines.append(f"# meta{EXPORT_SEPARATOR}{key}{EXPORT_SEPARATOR}{_stringify_meta_value(meta[key])}")
            written_keys.add(key)

    for key in sorted(meta.keys()):
        if key in written_keys:
            continue
        lines.append(f"# meta{EXPORT_SEPARATOR}{key}{EXPORT_SEPARATOR}{_stringify_meta_value(meta[key])}")

    if warnings:
        for w in warnings:
            lines.append(f"# warning{EXPORT_SEPARATOR}{_stringify_meta_value(w)}")

    return lines


def _prepare_market_dataframe_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare canonical market DataFrame for stable CSV export.
    """
    if df.empty:
        return df.copy()

    df_out = df.copy()

    required_cols = set(CANONICAL_MARKET_COLS)
    missing = required_cols - set(df_out.columns)
    if missing:
        raise ValueError(
            "Cannot export market CSV: missing canonical column(s): "
            + ", ".join(sorted(missing))
        )

    # Ensure optional columns exist if present in canonical pipeline
    optional_cols = ["timestamp_local", "timestamp_utc", "unix_seconds"]
    for col in optional_cols:
        if col not in df_out.columns:
            df_out[col] = pd.NA

    # Datetime formatting
    for col in ("timestamp", "timestamp_local", "timestamp_utc"):
        if col in df_out.columns:
            if pd.api.types.is_datetime64_any_dtype(df_out[col]) or str(df_out[col].dtype).startswith("datetime64"):
                # timezone-aware keeps offset in formatted string; naive will have no offset
                df_out[col] = df_out[col].dt.strftime(EXPORT_DATE_FORMAT)
            else:
                df_out[col] = df_out[col].astype(str)

    # Booleans as 0/1 for stable re-read
    bool_cols = ["is_negative_price", "deprecated"] if "deprecated" in df_out.columns else ["is_negative_price"]
    for col in bool_cols:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype("Int64")

    # Stable export order
    ordered_cols = [
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
    existing_cols = [c for c in ordered_cols if c in df_out.columns]
    remaining_cols = [c for c in df_out.columns if c not in existing_cols]
    df_out = df_out[existing_cols + remaining_cols]

    return df_out


# =============================================================================
# PUBLIC EXPORT FUNCTIONS
# =============================================================================

def export_market_prices_csv(
    result: CanonicalMarketResult,
    output_path: str | Path,
) -> Path:
    """
    Export canonical market data to a standardized CSV file with metadata header.

    Parameters
    ----------
    result : CanonicalMarketResult
        Standardized market result.
    output_path : str | Path
        Output CSV path.

    Returns
    -------
    Path
        Written file path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_out = _prepare_market_dataframe_for_export(result.data)
    meta_lines = _build_metadata_lines(result.meta, result.warnings)

    with output_path.open("w", encoding=EXPORT_ENCODING, newline="") as f:
        for line in meta_lines:
            f.write(line + "\n")
        df_out.to_csv(
            f,
            sep=EXPORT_SEPARATOR,
            index=False,
            encoding=EXPORT_ENCODING,
            lineterminator="\n",
        )

    return output_path


def build_default_market_csv_filename(
    *,
    bzn: str,
    start: str,
    end: str,
    prefix: str = "market_prices",
) -> str:
    """
    Build a stable default CSV filename.
    """
    safe_bzn = str(bzn).strip().replace("/", "-").replace(" ", "_")
    safe_start = str(start).strip().replace(":", "-").replace(" ", "_")
    safe_end = str(end).strip().replace(":", "-").replace(" ", "_")
    return f"{prefix}_{safe_bzn}_{safe_start}_{safe_end}.csv"