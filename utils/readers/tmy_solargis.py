# utils/readers/tmy_solargis.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import re

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


# =============================================================================
# "Intelligent" dictionaries (readable & maintainable)
# =============================================================================

# --- time component synonyms (canonicalized) ---
TIME_SYNONYMS: Dict[str, List[str]] = {
    "datetime": ["datetime", "date_time", "date time", "timestamp", "time_stamp", "datehour", "datehourutc"],
    "year": ["year", "yyyy", "yr", "annee"],
    "month": ["month", "mon", "mm", "mois"],
    "day": ["day", "dd", "jour"],
    "doy": ["doy", "dayofyear", "day_of_year", "dayofyearutc"],
    "hour": ["hour", "hr", "hh"],
    "minute": ["minute", "min", "mn"],
    "time": ["time", "hhmm", "hourminute", "hour_minute"],
}

# --- meteo/solar variable synonyms -> internal column names ---
VAR_SYNONYMS: Dict[str, List[str]] = {
    # irradiation / irradiance (we keep the internal names used by your pipeline)
    "ghi": [
        "ghi",
        "global_horizontal",
        "globalhorizontal",
        "global_hor",
        "globhor",
        "globalhorizontalirradiation",
        "globalhorizontalirradiance",
    ],
    "dni": [
        "dni",
        "direct_normal",
        "directnormal",
        "beam_normal",
        "beamnormal",
        "directnormalirradiation",
        "directnormalirradiance",
    ],
    "dhi": [
        "dhi",
        "dif",
        "diffuse_horizontal",
        "diffusehorizontal",
        "diffuse_hor",
        "diffusehorizontalirradiation",
        "diffusehorizontalirradiance",
    ],
    # "global_inclined" / POA / GTI (optional; kept as gpi to preserve your keep-list)
    "gpi": [
        "gpi",
        "global_inclined",
        "globalinclined",
        "global_tilted",
        "globaltilted",
        "gti",
        "poa",
        "plane_of_array",
        "planeofarray",
    ],
    # meteo
    "temp": [
        "temp",
        "temperature",
        "tair",
        "ta",
        "tamb",
        "ambient_temperature",
        "ambienttemperature",
        "air_temperature",
        "airtemperature",
    ],
    "wind_speed": [
        "ws",
        "wind_speed",
        "windspeed",
        "windvel",
        "wind_vel",
        "windvelocity",
        "wind_velocity",
        "windvel10m",
    ],
    "wind_direction": [
        "wd",
        "wind_direction",
        "winddirection",
        "winddir",
        "wind_dir",
        "winddir10m",
        "winddirection10m",
    ],
    # extras (recognized but not necessarily kept by default)
    "relative_humidity": ["relative_humidity", "rh", "humidity", "humid", "relhumidity"],
    "total_precipitation": ["total_precipitation", "precipitation", "precip", "prcp"],
    "snowfall": ["snowfall", "snow", "snow_depth", "snowdepth"],
}

# Common SolarGIS short codes (example-1 style)
SOLARGIS_SHORT_CODES: Dict[str, str] = {
    "GHI": "ghi",
    "DNI": "dni",
    "DIF": "dhi",
    "DHI": "dhi",
    "GTI": "gpi",
    "POA": "gpi",
    "TEMP": "temp",
    "TAMB": "temp",
    "WS": "wind_speed",
    "WINDVEL": "wind_speed",
    "WD": "wind_direction",
    "WINDDIR": "wind_direction",
    "RH": "relative_humidity",
    "PRECIP": "total_precipitation",
    "SNOW": "snowfall",
}


# =============================================================================
# Helpers
# =============================================================================

_RE_UNIT_BRACKETS = re.compile(r"\[([^\]]+)\]")
_RE_UNIT_PARENS = re.compile(r"\(([^\)]+)\)")
_RE_NUM = re.compile(r"^-?\d+(\.\d+)?$")


def _canon(name: str) -> str:
    """Canonicalize column names for robust matching."""
    s = str(name).strip().lower()
    s = s.replace("\ufeff", "")  # BOM
    s = s.replace("°", "deg")
    # turn separators into underscores
    s = re.sub(r"[ \t\.\-\/]+", "_", s)
    # keep only alnum + underscore
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _is_numberish(token: str) -> bool:
    token = str(token).strip()
    if not token:
        return False
    return bool(_RE_NUM.match(token))


def _guess_sep(lines: List[str]) -> str:
    # SolarGIS is usually ';'. We keep it as default, with a light auto-detect.
    for s in lines:
        t = s.strip()
        if not t or t.startswith("#"):
            continue
        if t.count(";") >= 2:
            return ";"
        if t.count(",") >= 2:
            return ","
    return ";"


def _extract_header_info(lines: List[str]) -> Dict[str, str]:
    """
    Reads key/value from header lines that start with '#'.
    Supports:
      #Key: Value
      #Key;Value
    """
    info: Dict[str, str] = {}
    for raw in lines:
        s = raw.strip()
        if not s.startswith("#"):
            continue
        s = s.lstrip("#").strip()
        if not s:
            continue

        if ":" in s:
            k, v = s.split(":", 1)
            k, v = k.strip(), v.strip()
            if k and v:
                info[k] = v
            continue

        if ";" in s:
            k, v = s.split(";", 1)
            k, v = k.strip(), v.strip()
            if k and v:
                info[k] = v
            continue

    return info


def _extract_units_from_header(lines: List[str]) -> Dict[str, str]:
    """
    Extract units from header, typically in a Columns block, but we keep it generic:
      #GHI - ... [Wh/m2]
      #TEMP - ... (deg_C)
    """
    units: Dict[str, str] = {}
    for raw in lines:
        s = raw.strip()
        if not s.startswith("#"):
            continue
        s2 = s.lstrip("#").strip()
        if not s2:
            continue

        # try to identify the column code (first token before space or '-')
        code = s2.split("-", 1)[0].strip().split(" ", 1)[0].strip()
        if not code:
            continue

        m = _RE_UNIT_BRACKETS.search(s2) or _RE_UNIT_PARENS.search(s2)
        if not m:
            continue

        u = m.group(1).strip()
        if u:
            units[code.strip()] = normalize_unit(u)
    return units


def _extract_unit_from_colname(col: str) -> Tuple[str, str]:
    """
    If a column name includes units, e.g. "GHI [Wh/m2]" or "Tamb(deg.C)",
    returns (clean_name, unit) where unit may be "".
    """
    s = str(col).strip()
    unit = ""

    m = _RE_UNIT_BRACKETS.search(s) or _RE_UNIT_PARENS.search(s)
    if m:
        unit = normalize_unit(m.group(1).strip())
        # remove the unit expression from the name
        s = _RE_UNIT_BRACKETS.sub("", s)
        s = _RE_UNIT_PARENS.sub("", s)
        s = s.strip()

    return s, unit


def _looks_like_units_row(tokens: List[str]) -> bool:
    """
    Heuristic: a units row has many empty fields, and unit-like tokens.
    """
    if not tokens:
        return False

    empties = sum(1 for t in tokens if str(t).strip() == "")
    unit_hits = 0
    value_hits = 0

    for t in tokens:
        x = str(t).strip().lower()
        if not x:
            continue
        # if it looks numeric, it's probably not a units row
        if _is_numberish(x):
            value_hits += 1
            continue
        # unit patterns
        if any(k in x for k in ["wh", "kwh", "w", "kw", "m2", "m²", "deg", "c", "m/s", "msec", "m_sec", "m/sec", "%", "pa"]):
            unit_hits += 1

    # Many empties + some unit tokens + few numeric values
    return (empties >= max(1, len(tokens) // 3)) and (unit_hits >= 2) and (value_hits <= 1)


def _looks_like_columns_row(line: str, sep: str) -> bool:
    toks = [t.strip() for t in line.split(sep)]
    if len(toks) < 3:
        return False

    # should be mostly non-numeric tokens
    non_num = sum(1 for t in toks if t and not _is_numberish(t))
    if non_num < max(2, int(0.6 * len(toks))):
        return False

    # should contain at least one time-ish token
    can = [_canon(t) for t in toks]
    time_vocab = set(sum(TIME_SYNONYMS.values(), []))
    return any(c in time_vocab for c in can)


def _find_table_block(lines: List[str]) -> Tuple[List[str], str, str, Optional[str], List[str]]:
    """
    Returns:
      header_lines, sep, columns_line, units_line(optional), data_lines_after_units
    """
    header_lines = [l for l in lines if l.strip().startswith("#")]
    non_header = [l for l in lines if l.strip() and not l.strip().startswith("#")]

    if not non_header:
        raise ValueError("Solargis TMY: no table found (file contains only header lines).")

    sep = _guess_sep(non_header)

    col_idx = None
    for i, l in enumerate(non_header):
        if _looks_like_columns_row(l, sep):
            col_idx = i
            break

    if col_idx is None:
        # last resort: accept a line that contains common vars even if time tokens are odd
        for i, l in enumerate(non_header):
            if sep not in l:
                continue
            toks = [_canon(t) for t in l.split(sep)]
            if any(t in ("day", "doy", "time", "year", "month", "hour") for t in toks):
                col_idx = i
                break

    if col_idx is None:
        raise ValueError("Solargis TMY: could not identify the columns header row.")

    columns_line = non_header[col_idx].strip()

    # units line: usually the next line, sometimes with blanks
    units_line: Optional[str] = None
    j = col_idx + 1
    while j < len(non_header):
        cand = non_header[j].strip()
        if not cand:
            j += 1
            continue

        toks = [t.strip() for t in cand.split(sep)]
        col_toks = [t.strip() for t in columns_line.split(sep)]
        if len(toks) == len(col_toks) and _looks_like_units_row(toks):
            units_line = cand
            j += 1
        break

    data_start = (j if units_line is not None else col_idx + 1)
    data_lines = non_header[data_start:]

    if not data_lines:
        raise ValueError("Solargis TMY: columns row found, but no data lines afterwards.")

    return header_lines, sep, columns_line, units_line, data_lines


def _synonym_lookup(df_cols: List[str], synonyms: List[str]) -> Optional[str]:
    """
    Return the actual df column matching any synonym (canonical comparison).
    """
    canon_map = {_canon(c): c for c in df_cols}
    for s in synonyms:
        key = _canon(s)
        if key in canon_map:
            return canon_map[key]
    return None


def _build_datetime(
    df: pd.DataFrame,
    assumed_year: int,
    warnings: List[str],
) -> pd.Series:
    """
    Build datetime robustly using time synonyms and rules.
    """
    cols = list(df.columns)

    c_dt = _synonym_lookup(cols, TIME_SYNONYMS["datetime"])
    if c_dt:
        dt = pd.to_datetime(df[c_dt], errors="coerce", utc=False)
        if dt.isna().any():
            bad = df.loc[dt.isna(), c_dt].head(5).tolist()
            raise ValueError(f"Could not parse some datetime values (examples): {bad}")
        return dt

    c_year = _synonym_lookup(cols, TIME_SYNONYMS["year"])
    c_month = _synonym_lookup(cols, TIME_SYNONYMS["month"])
    c_day = _synonym_lookup(cols, TIME_SYNONYMS["day"])
    c_doy = _synonym_lookup(cols, TIME_SYNONYMS["doy"])
    c_hour = _synonym_lookup(cols, TIME_SYNONYMS["hour"])
    c_min = _synonym_lookup(cols, TIME_SYNONYMS["minute"])
    c_time = _synonym_lookup(cols, TIME_SYNONYMS["time"])

    # Rule 1: Y/M/D + H (+ Min)
    if c_year and c_month and c_day and c_hour:
        y = pd.to_numeric(df[c_year], errors="coerce").astype("Int64")
        mo = pd.to_numeric(df[c_month], errors="coerce").astype("Int64")
        da = pd.to_numeric(df[c_day], errors="coerce").astype("Int64")
        ho = pd.to_numeric(df[c_hour], errors="coerce").astype("Int64")
        mi = pd.to_numeric(df[c_min], errors="coerce").astype("Int64") if c_min else 0

        dt = pd.to_datetime(
            dict(year=y, month=mo, day=da, hour=ho, minute=mi),
            errors="coerce",
        )
        if dt.isna().any():
            bad = df.loc[dt.isna(), [c_year, c_month, c_day, c_hour] + ([c_min] if c_min else [])].head(5).to_dict("records")
            raise ValueError(f"Could not build datetime from Y/M/D/H/M (examples): {bad}")
        return dt

    # Decide whether "day" is DOY if month not present
    if c_doy is None and c_day and not c_month:
        c_doy = c_day

    # Helper to parse "Time" to hour/min
    def parse_time_hm(series: pd.Series) -> Tuple[pd.Series, pd.Series]:
        s = series.astype(str).str.strip()

        # common HH:MM
        t1 = pd.to_datetime(s, format="%H:%M", errors="coerce")
        # HH:MM:SS
        t2 = pd.to_datetime(s, format="%H:%M:%S", errors="coerce")
        t = t1.fillna(t2)

        # numeric hours (e.g., 0.5)
        if t.isna().any():
            num = pd.to_numeric(s, errors="coerce")
            ok = num.notna() & t.isna()
            if ok.any():
                h = (num[ok].astype(float)).astype(int)
                m = ((num[ok].astype(float) - h) * 60).round().astype(int)
                # make a fake timestamp for extraction
                fake = pd.to_datetime("2000-01-01", errors="coerce") + pd.to_timedelta(h, unit="h") + pd.to_timedelta(m, unit="m")
                t.loc[ok] = fake

        if t.isna().any():
            bad = series.loc[t.isna()].head(5).tolist()
            raise ValueError(f"Could not parse some Time values (examples): {bad}")

        return t.dt.hour, t.dt.minute

    # Rule 2: DOY + Time
    if c_doy is not None and c_time is not None:
        doy = pd.to_numeric(df[c_doy], errors="coerce")
        doy = doy[doy.notna()].astype(int)
        # align indices
        df2 = df.loc[doy.index].copy()
        df2["_doy"] = doy

        h, m = parse_time_hm(df2[c_time])
        base = pd.Timestamp(datetime(assumed_year, 1, 1))
        dt = (
            base
            + pd.to_timedelta(df2["_doy"] - 1, unit="D")
            + pd.to_timedelta(h, unit="h")
            + pd.to_timedelta(m, unit="m")
        )
        # reindex to original
        out = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        out.loc[df2.index] = dt.values
        out = pd.to_datetime(out, errors="coerce")
        if out.isna().any():
            warnings.append("[datetime] Some datetime values could not be built; rows kept as NaT.")
        return out

    # Rule 3: DOY + Hour (+ Minute)
    if c_doy is not None and c_hour is not None:
        doy = pd.to_numeric(df[c_doy], errors="coerce")
        h = pd.to_numeric(df[c_hour], errors="coerce")
        mi = pd.to_numeric(df[c_min], errors="coerce") if c_min else 0

        base = pd.Timestamp(datetime(assumed_year, 1, 1))
        dt = (
            base
            + pd.to_timedelta(doy - 1, unit="D")
            + pd.to_timedelta(h, unit="h")
            + pd.to_timedelta(mi, unit="m")
        )
        if dt.isna().any():
            bad = df.loc[dt.isna(), [c_doy, c_hour] + ([c_min] if c_min else [])].head(5).to_dict("records")
            raise ValueError(f"Could not build datetime from DOY/H/M (examples): {bad}")
        return dt

    raise ValueError(
        "Solargis TMY: could not build datetime (missing time columns). "
        f"Found columns: {list(df.columns)}"
    )


def _build_rename_and_units(
    raw_columns: List[str],
    units_from_units_row: Dict[str, str],
    units_from_header: Dict[str, str],
    warnings: List[str],
) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    """
    Returns:
      - rename_map: raw column -> internal column name
      - units_by_col: internal column name -> normalized unit
      - cleaned_columns: raw columns cleaned from inline units
    """
    rename_map: Dict[str, str] = {}
    units_by_col: Dict[str, str] = {"datetime": ""}

    cleaned_columns: List[str] = []
    inline_units: Dict[str, str] = {}

    # 1) strip units inside column names (if present)
    for c in raw_columns:
        clean, u = _extract_unit_from_colname(c)
        cleaned_columns.append(clean)
        if u:
            inline_units[clean] = u

    # 2) map columns to internal names via:
    #    - exact SolarGIS short codes
    #    - then synonym sets
    canon_to_internal: Dict[str, str] = {}

    # Prepare a reverse synonym lookup for speed/readability
    for internal, syns in VAR_SYNONYMS.items():
        for s in syns:
            canon_to_internal[_canon(s)] = internal

    for raw in cleaned_columns:
        r = str(raw).strip()
        if not r:
            continue

        # time columns will be handled separately
        c_raw = _canon(r)

        # short code mapping (case-insensitive)
        internal = None
        if r.upper() in SOLARGIS_SHORT_CODES:
            internal = SOLARGIS_SHORT_CODES[r.upper()]
        else:
            internal = canon_to_internal.get(c_raw)

        if internal:
            rename_map[r] = internal

            # units priority:
            # units row > header block > inline in name
            u = ""
            if r in units_from_units_row:
                u = units_from_units_row[r]
            elif r in units_from_header:
                u = units_from_header[r]
            elif r in inline_units:
                u = inline_units[r]

            if u:
                units_by_col[internal] = normalize_unit(u)

    # also accept units mapping where header uses short codes but table uses synonyms, and vice-versa
    # (e.g., header has "GHI", table has "global_horizontal")
    # We keep it light: try matching by canonical name too.
    if units_from_header:
        hdr_canon = {_canon(k): v for k, v in units_from_header.items()}
        for raw in cleaned_columns:
            r = str(raw).strip()
            if not r:
                continue
            if r not in rename_map:
                continue
            internal = rename_map[r]
            if internal in units_by_col and units_by_col[internal]:
                continue
            if _canon(r) in hdr_canon:
                units_by_col[internal] = normalize_unit(hdr_canon[_canon(r)])

    return rename_map, units_by_col, cleaned_columns


def _convert_energy_to_power_if_needed(
    df: pd.DataFrame,
    units_by_col: Dict[str, str],
    target_unit: str,
    step_minutes: int,
    cols: List[str],
    warnings: List[str],
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    SolarGIS often provides irradiation per step (Wh/m² or kWh/m²).
    If target is power (W/m² or kW/m²), convert using:
        W/m² = (Wh/m²) / (dt_h)
    """
    tgt = normalize_unit(target_unit)
    dt_h = (step_minutes or 60) / 60.0

    def is_energy(u: str) -> bool:
        u = normalize_unit(u)
        return u in {"Wh/m²", "kWh/m²", "Wh/m2", "kWh/m2"}

    def is_power(u: str) -> bool:
        u = normalize_unit(u)
        return u in {"W/m²", "kW/m²", "W/m2", "kW/m2"}

    for c in cols:
        if c not in df.columns:
            continue

        src = normalize_unit(units_by_col.get(c, ""))

        if is_energy(src) and is_power(tgt):
            s = pd.to_numeric(df[c], errors="coerce")

            if normalize_unit(src) in {"Wh/m²", "Wh/m2"} and normalize_unit(tgt) in {"W/m²", "W/m2"}:
                df[c] = s / dt_h
            elif normalize_unit(src) in {"Wh/m²", "Wh/m2"} and normalize_unit(tgt) in {"kW/m²", "kW/m2"}:
                df[c] = (s / dt_h) / 1000.0
            elif normalize_unit(src) in {"kWh/m²", "kWh/m2"} and normalize_unit(tgt) in {"kW/m²", "kW/m2"}:
                df[c] = s / dt_h
            elif normalize_unit(src) in {"kWh/m²", "kWh/m2"} and normalize_unit(tgt) in {"W/m²", "W/m2"}:
                df[c] = (s / dt_h) * 1000.0
            else:
                continue

            units_by_col[c] = normalize_unit(tgt)

    return df, units_by_col


# =============================================================================
# Public reader
# =============================================================================
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

    # 1) Identify header/table block intelligently
    header_lines, sep, columns_line, units_line, data_lines = _find_table_block(lines)

    header_info = _extract_header_info(header_lines)
    units_from_header = _extract_units_from_header(header_lines)

    # 2) Read table (header + data) via existing helper to stay consistent with pipeline
    table_lines: List[str] = [columns_line] + data_lines
    df_raw = read_delimited_from_lines(table_lines, sep=sep)
    df_raw = df_raw.rename(columns=lambda x: str(x).strip())

    # Drop duplicated columns conservatively (keep first) + warn
    if df_raw.columns.duplicated().any():
        dups = df_raw.columns[df_raw.columns.duplicated()].tolist()
        warnings.append(f"[columns] Duplicate columns detected; keeping first occurrence: {dups}")
        df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()].copy()

    # 3) Units row parsing (if present)
    units_from_units_row: Dict[str, str] = {}
    if units_line is not None:
        col_tokens = [c.strip() for c in columns_line.split(sep)]
        unit_tokens = [u.strip() for u in units_line.split(sep)]
        if len(unit_tokens) == len(col_tokens):
            for c, u in zip(col_tokens, unit_tokens):
                if u:
                    units_from_units_row[c] = normalize_unit(u)

        # Remove the units row from df_raw: it's the first data row
        # (because we passed table_lines starting at columns_line but NOT units_line,
        #  units_line is still in data_lines; in our construction it is included,
        #  so it becomes first row of df_raw)
        # We detect it by checking if that first row "looks like units".
        first_row = df_raw.iloc[0].astype(str).tolist()
        if _looks_like_units_row(first_row):
            df_raw = df_raw.iloc[1:].reset_index(drop=True)

    # 4) Clean inline-units in column names + build rename map + units_by_col
    rename_map, units_by_col, cleaned_cols = _build_rename_and_units(
        raw_columns=list(df_raw.columns),
        units_from_units_row=units_from_units_row,
        units_from_header=units_from_header,
        warnings=warnings,
    )

    # Apply cleaned column names (remove inline units) before renaming
    df_raw.columns = cleaned_cols
    df_raw = df_raw.rename(columns=rename_map).copy()

    # 5) Build datetime from time columns (before numeric casting)
    dt = _build_datetime(df_raw, assumed_year=assumed_year, warnings=warnings)
    df_raw["datetime"] = dt

    # 6) Convert remaining columns to numeric when possible (excluding datetime + potential datetime source cols)
    for c in df_raw.columns:
        if c == "datetime":
            continue
        # keep original time component columns as numeric too (harmless)
        df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce") if c != "time" else df_raw[c]

    # 7) Keep only the columns expected by the pipeline (unchanged contract)
    keep = ["datetime", "ghi", "dni", "dhi", "gpi", "temp", "wind_speed", "wind_direction"]
    df = df_raw[[c for c in keep if c in df_raw.columns]].copy()

    # Ensure sorted
    df = df.sort_values("datetime").reset_index(drop=True)

    # 8) Detect timestep
    ts2 = detect_time_step_from_datetime(df)
    time_step_minutes = ts2.minutes
    if time_step_minutes is None:
        time_step_minutes = 60
        warnings.append("[timestep] Could not detect timestep from datetime; assuming 60 min (TMY60).")

    # 9) Energy->power conversion for irradiation if needed (dt-based), then normal converter
    df, units_by_col = _convert_energy_to_power_if_needed(
        df=df,
        units_by_col=units_by_col,
        target_unit=target_irradiance_unit,
        step_minutes=int(time_step_minutes or 60),
        cols=["ghi", "dni", "dhi", "gpi"],
        warnings=warnings,
    )

    conv: UnitConversionResult = convert_irradiance_units(df, units_by_col, target_unit=target_irradiance_unit)
    df = conv.df
    units_by_col = conv.units_by_col
    warnings.extend(conv.warnings)

    # 10) Resample if sub-hourly (unchanged)
    if resample_hourly_if_subhourly and time_step_minutes < 60:
        df = resample_to_hourly(
            df,
            sum_cols=["ghi", "dni", "dhi", "gpi"],
            mean_cols=["temp", "wind_speed", "wind_direction"],
        )
        time_step_minutes = 60
        warnings.append("[resample] Sub-hourly data resampled to 1H (sum irradiation / mean temp+wind).")

    # 11) Quality check (unchanged)
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
