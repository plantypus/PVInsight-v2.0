# utils/readers/hourly_results.py
from __future__ import annotations

from typing import Dict, List, Tuple
import pandas as pd

from config import PVSYST_DATE_FMT


def _decode_bytes(source: bytes) -> str:
    for enc in ("latin-1", "utf-8"):
        try:
            return source.decode(enc)
        except Exception:
            continue
    return source.decode("latin-1", errors="ignore")


def parse_general_info(lines: List[str]) -> Dict[str, str]:
    """
    Extracts a few useful fields from the PVSyst header.

    With your sample:
      Projet;9312_LGR_9-E3.PRJ;26/08/25 09h50;...
    We capture:
      Project_file = 9312_LGR_9-E3.PRJ
      Project_code = 9312_LGR_9-E3    (best-effort)
    """
    info: Dict[str, str] = {}

    if lines:
        info["PVSyst_version"] = lines[0].strip()

    for line in lines:
        if line.startswith("Simulation date"):
            parts = line.split(";")
            if len(parts) > 2:
                info["Simulation_date"] = parts[2].strip()

        # Project
        if line.startswith("Projet;"):
            parts = line.split(";")
            if len(parts) >= 2:
                info["Project_file"] = parts[1].strip()
                # best-effort "code": take file stem before .PRJ
                pf = info["Project_file"]
                if "." in pf:
                    info["Project_code"] = pf.split(".", 1)[0].strip()
                else:
                    info["Project_code"] = pf.strip()

        # Site
        if line.startswith("Site géographique;"):
            parts = line.split(";")
            if len(parts) >= 4:
                info["Site_name"] = parts[3].strip()

        # Meteo
        if line.startswith("Données météo;"):
            parts = line.split(";")
            if len(parts) >= 4:
                info["Meteo_name"] = parts[3].strip()

        # Variant
        if line.startswith("Variante de simulation;"):
            parts = line.split(";")
            if len(parts) >= 4:
                info["Variant_name"] = parts[3].strip()

    return info


def detect_table(lines: List[str]) -> Tuple[str, List[str], List[str], int]:
    for i, raw in enumerate(lines):
        line = raw.lstrip().replace("\ufeff", "")
        if line.lower().startswith("date;"):
            headers = [h.strip() for h in line.split(";")]
            if i + 1 >= len(lines):
                raise ValueError("Missing units row after header line.")
            units_line = lines[i + 1].lstrip().replace("\ufeff", "")
            units = [u.strip() for u in units_line.split(";")]
            date_col = headers[0] if headers else "date"
            return date_col, headers, units, i + 2
    raise ValueError("Hourly table not found (missing 'date;...' header line).")


def _clean_text_series(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.replace("\u00a0", " ", regex=False)
        .str.replace('"', "", regex=False)
        .str.strip()
    )


def _parse_datetime_flexible(s: pd.Series) -> pd.Series:
    s = _clean_text_series(s)

    fmts: List[str] = []
    if PVSYST_DATE_FMT:
        fmts.append(PVSYST_DATE_FMT)

    # Matches your sample: 01/01/90 00:00
    fmts += [
        "%d/%m/%y %H:%M",
        "%d/%m/%Y %H:%M",
        "%d/%m/%y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d.%m.%y %H:%M",
        "%d.%m.%Y %H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ]

    best = None
    best_valid = -1

    for fmt in fmts:
        try:
            dt = pd.to_datetime(s, format=fmt, errors="coerce")
            valid = int(dt.notna().sum())
            if valid > best_valid:
                best, best_valid = dt, valid
            if len(s) > 0 and valid >= int(0.98 * len(s)):
                return dt
        except Exception:
            continue

    if best is not None and best_valid > 0:
        return best

    return pd.to_datetime(s, errors="coerce", dayfirst=True)


def load_hourly_dataframe(lines: List[str]) -> Tuple[pd.DataFrame, Dict[str, str]]:
    date_col, headers, units, start = detect_table(lines)

    if "E_Grid" not in headers:
        raise ValueError("Missing mandatory column 'E_Grid'.")

    # Normalize units length
    if len(units) < len(headers):
        units = units + [""] * (len(headers) - len(units))
    elif len(units) > len(headers):
        units = units[: len(headers)]

    rows: List[List[str]] = []
    for raw in lines[start:]:
        if not raw.strip():
            continue
        parts = raw.split(";")
        if len(parts) < len(headers):
            continue
        if len(parts) > len(headers):
            parts = parts[: len(headers)]
        rows.append(parts)

    df = pd.DataFrame(rows, columns=headers)
    units_map = dict(zip(headers, units))

    if df.empty:
        return df, units_map

    # Resolve date column name
    if date_col not in df.columns:
        for cand in ("date", "Date", "DATE"):
            if cand in df.columns:
                date_col = cand
                break
    if date_col not in df.columns:
        raise ValueError("Date column not found in parsed hourly table.")

    dt = _parse_datetime_flexible(df[date_col])

    # Fix: avoid dropping "date" if it's already named date
    df["date"] = dt
    if date_col != "date":
        df = df.drop(columns=[date_col])

    df = df.dropna(subset=["date"])
    if df.empty:
        raise ValueError("No valid timestamps could be parsed from the date column.")

    numeric_cols = [c for c in df.columns if c != "date"]
    for c in numeric_cols:
        df[c] = _clean_text_series(df[c]).str.replace(",", ".", regex=False)
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Sanity check
    n_total = len(df)
    n_valid = int(df[numeric_cols].notna().any(axis=1).sum()) if n_total > 0 else 0
    if n_total > 0 and (n_valid / n_total) < 0.5:
        raise ValueError(
            "Less than 50% of rows contain valid numeric values. Check decimal separator / file integrity."
        )

    df = df.set_index("date").sort_index()

    if date_col != "date" and date_col in units_map:
        units_map["date"] = units_map.pop(date_col)

    return df, units_map


def read_hourly_from_bytes(source: bytes) -> tuple[dict, pd.DataFrame, dict]:
    text = _decode_bytes(source)
    lines = text.splitlines()
    general_info = parse_general_info(lines)
    df, units_map = load_hourly_dataframe(lines)
    return general_info, df, units_map
