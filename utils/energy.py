# utils/energy.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple

import pandas as pd

from utils.units import normalize_unit


@dataclass(frozen=True)
class EnergySummary:
    annual_ghi: Optional[float]
    annual_dni: Optional[float]
    annual_dhi: Optional[float]
    unit: str
    warnings: List[str]


def _to_wh_per_m2(series: pd.Series, step_minutes: int, unit: str) -> pd.Series:
    """
    Convert irradiance series to Wh/m² per timestep and sum.
    Assumes series is irradiance (W/m² or kW/m²).
    """
    unit = normalize_unit(unit)
    if unit == "kW/m²":
        w = series * 1000.0
    else:
        w = series

    # Integrate over timestep: W/m² * hours => Wh/m²
    return w * (step_minutes / 60.0)


def annual_irradiation(
    df: pd.DataFrame,
    units_by_col: Dict[str, str],
    step_minutes: Optional[int],
    energy_unit: str = "kWh/m²",
) -> EnergySummary:
    """
    Returns annual irradiation for ghi/dni/dhi as:
      - Wh/m² or kWh/m² depending on energy_unit
    """
    warnings: List[str] = []
    if step_minutes is None or step_minutes <= 0:
        warnings.append("[energy] Unknown timestep; cannot compute integrated energy.")
        return EnergySummary(None, None, None, normalize_unit(energy_unit), warnings)

    energy_unit = normalize_unit(energy_unit)
    if energy_unit not in {"Wh/m²", "kWh/m²"}:
        raise ValueError("energy_unit must be 'Wh/m²' or 'kWh/m²'")

    def compute(col: str) -> Optional[float]:
        if col not in df.columns:
            return None
        u = units_by_col.get(col, "W/m²") or "W/m²"
        wh_series = _to_wh_per_m2(df[col].astype(float), step_minutes, u)
        total_wh = float(wh_series.sum(skipna=True))
        if energy_unit == "kWh/m²":
            return total_wh / 1000.0
        return total_wh

    return EnergySummary(
        annual_ghi=compute("ghi"),
        annual_dni=compute("dni"),
        annual_dhi=compute("dhi"),
        unit=energy_unit,
        warnings=warnings,
    )
