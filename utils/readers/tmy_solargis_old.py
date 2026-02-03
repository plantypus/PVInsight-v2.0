# utils/readers/tmy_solargis.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from utils.io import read_text_lines, read_delimited_from_lines
from utils.units import normalize_unit, convert_irradiance_units, UnitConversionResult
from utils.time_series import detect_time_step_from_datetime, resample_to_hourly
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


# -----------------------------------------------------------------------------
# Parsing helpers
# -----------------------------------------------------------------------------
def _extract_header_info_solargis(lines: List[str]) -> Dict[str, str]:
    info: Dict[str, str] = {}

    def put(k: str, v: str):
        k = k.strip()
        v = v.strip()
        if k and v:
            info[k] = v

    for raw in lines:
        s = raw.strip()
        if not s.startswith("#"):
            continue
        s = s.lstrip("#").strip()
        if not s:
            continue

        if ":" in s:
            k, v = s.split(":", 1)
            put(k, v)
            continue

    return info


def _extract_units_from_columns_block(lines: List[str]) -> Dict[str, str]:
    units: Dict[str, str] = {}
    in_block = False

    for raw in lines:
        s = raw.strip()
        if not s.startswith("#"):
            continue
        s2 = s.lstrip("#").strip()

        if s2.lower().startswith("columns:"):
            in_block = True
            continue

        if in_block and s2.lower().startswith("data:"):
            break

        if not in_block:
            continue

        if " - " in s2 and "[" in s2 and "]" in s2:
            code = s2.split(" - ", 1)[0].strip()
            unit = s2.split("[", 1)[1].split("]", 1)[0].strip()
            if code:
                units[code] = normalize_unit(unit)

    return units


def _split_header_and_table(lines: List[str]) -> Tuple[List[str], List[str]]:
    header_lines: List[str] = []
    table_lines: List[str] = []

    data_marker_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "#data:":
            data_marker_idx = i
            break

    if data_marker_idx is None:
        for i, line in enumerate(lines):
            if line.strip() and not line.lstrip().startswith("#"):
                if line.strip().lower().startswith("day;time") or line.strip().lower().startswith("day,time"):
                    data_marker_idx = i - 1
                    break

    if data_marker_idx is None:
        raise ValueError("Could not find Solargis '#Data:' section or the 'Day;Time;...' header row.")

    header_lines = lines[: data_marker_idx + 1]

    j = data_marker_idx + 1
    while j < len(lines):
        s = lines[j].strip()
        if s and not s.startswith("#"):
            table_lines = lines[j:]
            break
        j += 1

    if not table_lines:
        raise ValueError("Found '#Data:' but no table content afterwards.")

    return header_lines, table_lines


def _rename_meteo_columns_solargis(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "GHI": "ghi",
        "DNI": "dni",
        "DIF": "dhi",
        "TEMP": "temp",
        "WS": "wind_speed",
        "WD": "wind_direction",
        "SE": "sun_elevation",
        "SA": "sun_azimuth",
        "Day": "day_of_year",
        "Time": "time",
    }
    return df.rename(columns={k: v for k, v in rename.items() if k in df.columns}).copy()


def _convert_energy_to_power_if_needed(
    df: pd.DataFrame,
    units_by_col: Dict[str, str],
    target_unit: str,
    step_minutes: int,
    cols: List[str],
    warnings: List[str],
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    SolarGIS typically provides irradiation per step (Wh/m² or kWh/m²).
    If target is power (W/m² or kW/m²), convert using:
        W/m² = (Wh/m²) / (dt_h)
    and update units_by_col accordingly.

    This avoids modifying utils.units.convert_irradiance_units() signature.
    """
    tgt = normalize_unit(target_unit)
    dt_h = (step_minutes or 60) / 60.0

    def is_energy(u: str) -> bool:
        u = normalize_unit(u)
        return u in {"Wh/m²", "kWh/m²"}

    def is_power(u: str) -> bool:
        u = normalize_unit(u)
        return u in {"W/m²", "kW/m²"}

    for c in cols:
        if c not in df.columns:
            continue
        src = normalize_unit(units_by_col.get(c, ""))

        if is_energy(src) and is_power(tgt):
            s = pd.to_numeric(df[c], errors="coerce")

            if src == "Wh/m²" and tgt == "W/m²":
                df[c] = s / dt_h
            elif src == "Wh/m²" and tgt == "kW/m²":
                df[c] = (s / dt_h) / 1000.0
            elif src == "kWh/m²" and tgt == "kW/m²":
                df[c] = s / dt_h
            elif src == "kWh/m²" and tgt == "W/m²":
                df[c] = (s / dt_h) * 1000.0
            else:
                # if we ever land here, we keep value but warn
                # warnings.append(f"[units] Unsupported energy->power conversion: {src} -> {tgt} for column '{c}'")
                continue

            units_by_col[c] = tgt
            # warnings.append(f"[units] Converted {c}: {src} -> {tgt} using dt={dt_h:g}h.")

    return df, units_by_col


# -----------------------------------------------------------------------------
# Public reader
# -----------------------------------------------------------------------------
def read_tmy_solargis(
    source: TextSource,
    source_name: Optional[str] = None,
    target_irradiance_unit: str = "kW/m²",
    resample_hourly_if_subhourly: bool = True,
    assumed_year: int = 2001,
) -> TMYDataset:
    if source_name is None:
        source_name = Path(source).name if isinstance(source, (str, Path)) else "uploaded_tmy_solargis.csv"

    warnings: List[str] = []

    lines = read_text_lines(source)
    header_lines, table_lines = _split_header_and_table(lines)

    header_info = _extract_header_info_solargis(header_lines)
    units_by_raw_col = _extract_units_from_columns_block(header_lines)

    sep = ";"
    df_raw = read_delimited_from_lines(table_lines, sep=sep)
    df_raw = df_raw.rename(columns=lambda x: str(x).strip())

    required = {"Day", "Time"}
    missing = [c for c in required if c not in df_raw.columns]
    if missing:
        raise ValueError(f"Missing required columns in Solargis TMY table: {missing}")

    df_raw["Day"] = pd.to_numeric(df_raw["Day"], errors="coerce")
    df_raw = df_raw[df_raw["Day"].notna()].copy()
    df_raw["Day"] = df_raw["Day"].astype(int)

    df_raw["Time"] = df_raw["Time"].astype(str).str.strip()

    base = pd.Timestamp(datetime(assumed_year, 1, 1))
    t = pd.to_datetime(df_raw["Time"], format="%H:%M", errors="coerce")
    if t.isna().any():
        t2 = pd.to_datetime(df_raw["Time"], errors="coerce")
        t = t.fillna(t2)

    if t.isna().any():
        bad = df_raw.loc[t.isna(), "Time"].head(5).tolist()
        raise ValueError(f"Could not parse some Time values (examples): {bad}")

    df_raw["datetime"] = (
        base
        + pd.to_timedelta(df_raw["Day"] - 1, unit="D")
        + pd.to_timedelta(t.dt.hour, unit="h")
        + pd.to_timedelta(t.dt.minute, unit="m")
    )

    for col in df_raw.columns:
        if col in {"Day", "Time", "datetime"}:
            continue
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

    df = _rename_meteo_columns_solargis(df_raw)

    units_by_col: Dict[str, str] = {"datetime": ""}
    mapping = {
        "GHI": "ghi",
        "DNI": "dni",
        "DIF": "dhi",
        "TEMP": "temp",
        "WS": "wind_speed",
        "WD": "wind_direction",
        "SE": "sun_elevation",
        "SA": "sun_azimuth",
        "Day": "day_of_year",
        "Time": "time",
    }
    for raw_col, u in units_by_raw_col.items():
        units_by_col[mapping.get(raw_col, raw_col)] = normalize_unit(u)

    keep = ["datetime", "ghi", "dni", "dhi", "gpi", "temp", "wind_speed", "wind_direction"]
    df = df[[c for c in keep if c in df.columns]].copy()

    df = df.sort_values("datetime").reset_index(drop=True)
    ts2 = detect_time_step_from_datetime(df)
    time_step_minutes = ts2.minutes
    if time_step_minutes is None:
        time_step_minutes = 60
        warnings.append("[timestep] Could not detect timestep from datetime; assuming 60 min (TMY60).")

    # 1) If SolarGIS is in Wh/m² and target is W/m² (or kW/m²), do the dt-based conversion here.
    df, units_by_col = _convert_energy_to_power_if_needed(
        df=df,
        units_by_col=units_by_col,
        target_unit=target_irradiance_unit,
        step_minutes=int(time_step_minutes or 60),
        cols=["ghi", "dni", "dhi", "gpi"],
        warnings=warnings,
    )

    # 2) Then let the existing converter handle remaining normalization (W<->kW, etc.)
    conv: UnitConversionResult = convert_irradiance_units(df, units_by_col, target_unit=target_irradiance_unit)
    df = conv.df
    units_by_col = conv.units_by_col
    warnings.extend(conv.warnings)

    if resample_hourly_if_subhourly and time_step_minutes < 60:
        df = resample_to_hourly(
            df,
            sum_cols=["ghi", "dni", "dhi", "gpi"],
            mean_cols=["temp", "wind_speed", "wind_direction"],
        )
        time_step_minutes = 60
        warnings.append("[resample] Sub-hourly data resampled to 1H (sum irradiation / mean temp+wind).")

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
