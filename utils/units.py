# utils/units.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, List
import re

import pandas as pd


# --- Normalize unit strings ---
_UNIT_ALIASES = {
    # Irradiance (power) per area
    "w/m2": "W/m²",
    "w/m^2": "W/m²",
    "w/m²": "W/m²",

    "kw/m2": "kW/m²",
    "kw/m^2": "kW/m²",
    "kw/m²": "kW/m²",

    # Irradiation (energy) per area  ✅ (SolarGIS)
    "wh/m2": "Wh/m²",
    "wh/m^2": "Wh/m²",
    "wh/m²": "Wh/m²",

    "kwh/m2": "kWh/m²",
    "kwh/m^2": "kWh/m²",
    "kwh/m²": "kWh/m²",

    # Temperature
    "deg.c": "°C",
    "deg_c": "°C",
    "°c": "°C",

    # Wind speed
    "m/sec": "m/s",
    "m/s": "m/s",

    # Angles / misc
    "°": "deg",
    "deg": "deg",
    "ratio": "ratio",
    "": "",
}


def normalize_unit(u: str) -> str:
    if u is None:
        return ""
    key = u.strip().lower()
    key = key.replace(" ", "")
    return _UNIT_ALIASES.get(key, u.strip())


# --- Column semantic (v1 meteo) ---
IRRADIANCE_COLS = {"ghi", "dni", "dhi", "gpi"}  # gpi treated as irradiance-like
TEMP_COLS = {"temp"}
WIND_SPEED_COLS = {"wind_speed"}
WIND_DIR_COLS = {"wind_direction"}


@dataclass(frozen=True)
class UnitConversionResult:
    df: pd.DataFrame
    units_by_col: Dict[str, str]
    warnings: List[str]


def convert_irradiance_units(
    df: pd.DataFrame,
    units_by_col: Dict[str, str],
    target_unit: str = "kW/m²",
) -> UnitConversionResult:
    """
    Convert irradiance columns to target_unit (W/m² or kW/m²).
    Only applies to columns recognized as irradiance-like.
    """
    target_unit = normalize_unit(target_unit)
    if target_unit not in {"W/m²", "kW/m²"}:
        raise ValueError("target_unit must be 'W/m²' or 'kW/m²'")

    out = df.copy()
    new_units = dict(units_by_col)
    warnings: List[str] = []

    for col in out.columns:
        if col not in IRRADIANCE_COLS:
            continue

        src = normalize_unit(new_units.get(col, ""))
        if src == "":
            # Default assumption for TMY irradiance if missing
            src = "W/m²"
            warnings.append(f"[units] Missing unit for '{col}', assuming {src}.")

        if src not in {"W/m²", "kW/m²"}:
            warnings.append(f"[units] Unknown irradiance unit '{src}' for '{col}', no conversion applied.")
            continue

        if src == target_unit:
            new_units[col] = src
            continue

        if src == "W/m²" and target_unit == "kW/m²":
            out[col] = out[col] * 0.001
            new_units[col] = "kW/m²"
        elif src == "kW/m²" and target_unit == "W/m²":
            out[col] = out[col] * 1000.0
            new_units[col] = "W/m²"

    return UnitConversionResult(df=out, units_by_col=new_units, warnings=warnings)
