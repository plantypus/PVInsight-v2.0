# core/meteo/tmy_pvsyst.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from utils.io import read_text_lines, split_pvsyst_hash_header, detect_separator, read_delimited_from_lines
from utils.units import normalize_unit, convert_irradiance_units, UnitConversionResult
from utils.time_series import parse_time_step_from_header, detect_time_step_from_datetime, resample_to_hourly
from utils.validation import basic_quality_check, DataQuality


TextSource = Union[str, Path, bytes]


@dataclass(frozen=True)
class TMYDataset:
    df: pd.DataFrame
    header_info: Dict[str, str]
    units_by_col: Dict[str, str]
    time_step_minutes: Optional[int]
    quality: DataQuality
    source_name: str
    warnings: List[str]


def _extract_header_info(header_lines: List[str]) -> Dict[str, str]:
    """
    Parse lines like:
      #Time Step;5min;;;;;;;;;
    into {"Time Step": "5min", ...}
    """
    info: Dict[str, str] = {}
    for line in header_lines:
        s = line.lstrip("#").strip()
        if not s:
            continue
        # Most PVSyst uses ';'
        parts = [p.strip() for p in s.split(";")]
        if len(parts) >= 2 and parts[0]:
            key = parts[0]
            val = parts[1]
            info[key] = val
    return info


def _extract_columns_and_units(body_lines: List[str], sep: str) -> Tuple[List[str], Dict[str, str], List[str]]:
    """
    body_lines starts at:
      YEAR;MONTH;...;WindDir
      ;;;;W/m2;...;°
      data...
    Returns:
      - columns (raw names)
      - units_by_raw_col
      - data_lines_only (starting at first data row)
    """
    # find header row: starts with YEAR (TMY) typically
    hdr_idx = None
    for i, line in enumerate(body_lines[:50]):
        if line.strip().upper().startswith("YEAR" + sep) or line.strip().upper() == "YEAR":
            hdr_idx = i
            break
    if hdr_idx is None:
        raise ValueError("Could not find the TMY table header row starting with 'YEAR'.")

    col_line = body_lines[hdr_idx]
    unit_line = body_lines[hdr_idx + 1] if hdr_idx + 1 < len(body_lines) else ""

    raw_cols = [c.strip() for c in col_line.split(sep)]
    raw_units = [normalize_unit(u.strip()) for u in unit_line.split(sep)]

    # Map col -> unit (align by index)
    units_by_col: Dict[str, str] = {}
    for j, col in enumerate(raw_cols):
        if not col:
            continue
        u = raw_units[j] if j < len(raw_units) else ""
        units_by_col[col] = u

    data_lines = body_lines[hdr_idx:]  # keep header+units for pandas
    return raw_cols, units_by_col, data_lines


def _rename_meteo_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "GHI": "ghi",
        "DNI": "dni",
        "DHI": "dhi",
        "Tamb": "temp",
        "WindVel": "wind_speed",
        "WindDir": "wind_direction",
        "GPI": "gpi",
    }
    out = df.rename(columns={k: v for k, v in rename.items() if k in df.columns}).copy()
    return out


def read_tmy_pvsyst(
    source: TextSource,
    source_name: Optional[str] = None,
    target_irradiance_unit: str = "kW/m²",
    resample_hourly_if_subhourly: bool = True,
) -> TMYDataset:
    """
    Read a PVSyst TMY file (hourly or sub-hourly) with:
      - '#' hash header metadata
      - table header line (YEAR;MONTH;...)
      - units line (;;;;W/m2;...;deg.C;...)
    Returns a normalized dataset (datetime + canonical columns).
    """
    if source_name is None:
        source_name = Path(source).name if isinstance(source, (str, Path)) else "uploaded_tmy.csv"

    warnings: List[str] = []

    lines = read_text_lines(source)
    blocks = split_pvsyst_hash_header(lines)
    header_info = _extract_header_info(blocks.header_lines)

    # detect separator from first non-empty body line
    first = next((l for l in blocks.body_lines if l.strip()), "")
    sep = detect_separator(first)

    # Extract units mapping from the table header lines (YEAR... + units line)
    _, units_by_raw_col, table_lines = _extract_columns_and_units(blocks.body_lines, sep=sep)

    # Read the whole table (pandas) from these lines (it includes header row and units row)
    df_raw = read_delimited_from_lines(table_lines, sep=sep)
    df_raw = df_raw.rename(columns=lambda x: str(x).strip())

    # Drop the units row from data: keep only rows where YEAR is numeric
    if "YEAR" in df_raw.columns:
        df_raw["YEAR"] = pd.to_numeric(df_raw["YEAR"], errors="coerce")
        df_raw = df_raw[df_raw["YEAR"].notna()].copy()
        df_raw["YEAR"] = df_raw["YEAR"].astype(int)


    # Build datetime from YEAR/MONTH/DAY/HOUR + sub-hourly minute offsets by occurrence
    for c in ["MONTH", "DAY", "HOUR"]:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce")

    df_raw["datetime"] = pd.to_datetime(
        df_raw[["YEAR", "MONTH", "DAY", "HOUR"]].rename(
            columns={"YEAR": "year", "MONTH": "month", "DAY": "day", "HOUR": "hour"}
        ),
        errors="coerce",
    )

    # Detect time step from header, fallback auto
    ts = parse_time_step_from_header(header_info)
    time_step_minutes = ts.minutes
    if time_step_minutes is None:
        ts2 = detect_time_step_from_datetime(df_raw)
        time_step_minutes = ts2.minutes
        if time_step_minutes is None:
            warnings.append("[timestep] Could not detect timestep from header or datetime; assuming 60 min.")
            time_step_minutes = 60

    # Sub-hourly: add minute offsets inside each hour (cumcount * step)
    df_raw = df_raw.sort_values("datetime").reset_index(drop=True)
    if time_step_minutes and time_step_minutes < 60:
        df_raw["minute_offset"] = df_raw.groupby(["YEAR", "MONTH", "DAY", "HOUR"]).cumcount() * time_step_minutes
        df_raw["datetime"] = df_raw["datetime"] + pd.to_timedelta(df_raw["minute_offset"], unit="m")
        df_raw = df_raw.drop(columns=["minute_offset"], errors="ignore")

    # Convert numeric columns (except datetime and date fields)
    for col in df_raw.columns:
        if col in {"datetime", "YEAR", "MONTH", "DAY", "HOUR"}:
            continue
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

    # Rename to canonical meteo names
    df = _rename_meteo_columns(df_raw)

    # Map units to renamed columns
    units_by_col: Dict[str, str] = {"datetime": ""}
    for raw_col, u in units_by_raw_col.items():
        # rename if known
        mapping = {
            "GHI": "ghi", "DNI": "dni", "DHI": "dhi",
            "Tamb": "temp", "WindVel": "wind_speed", "WindDir": "wind_direction",
            "GPI": "gpi",
        }
        key = mapping.get(raw_col, raw_col)
        units_by_col[key] = normalize_unit(u)

    # Keep only meteo columns (v1)
    keep = ["datetime", "ghi", "dni", "dhi", "gpi", "temp", "wind_speed", "wind_direction"]
    df = df[[c for c in keep if c in df.columns]].copy()

    # Convert irradiance units to target
    conv: UnitConversionResult = convert_irradiance_units(df, units_by_col, target_unit=target_irradiance_unit)
    df = conv.df
    units_by_col = conv.units_by_col
    warnings.extend(conv.warnings)

    # Optional resample to hourly if sub-hourly
    if resample_hourly_if_subhourly and time_step_minutes < 60:
        df = resample_to_hourly(
            df,
            sum_cols=["ghi", "dni", "dhi", "gpi"],
            mean_cols=["temp", "wind_speed", "wind_direction"],
        )
        # after resampling, timestep is 60
        time_step_minutes = 60
        warnings.append("[resample] Sub-hourly data resampled to 1H (sum irradiance / mean temp+wind).")

    # Quality check
    quality = basic_quality_check(df, step_minutes=time_step_minutes)
    if quality.warning:
        warnings.append(f"[quality] {quality.warning}")

    return TMYDataset(
        df=df,
        header_info=header_info,
        units_by_col=units_by_col,
        time_step_minutes=time_step_minutes,
        quality=quality,
        source_name=source_name,
        warnings=warnings,
    )
