from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from core.bess_sizing.dispatch_optimizer import (
    BatteryParameters,
    DispatchOptimizationResult,
    optimize_dispatch_hourly,
)


@dataclass
class BessSizingRunResult:
    aligned_hourly_df: pd.DataFrame
    summary_df: pd.DataFrame
    score_matrix_gain_eur: pd.DataFrame
    dispatch_by_config: Dict[str, pd.DataFrame]
    tmy_coherence: Dict[str, Any]
    warnings: List[str]
    assumptions: Dict[str, Any]
    best_config_id: str | None


def build_power_grid(
    *,
    power_min_mw: float,
    power_max_mw: float,
    power_step_mw: float,
) -> List[float]:
    if power_min_mw <= 0:
        raise ValueError("power_min_mw must be > 0.")
    if power_max_mw <= 0:
        raise ValueError("power_max_mw must be > 0.")
    if power_step_mw <= 0:
        raise ValueError("power_step_mw must be > 0.")
    if power_min_mw > power_max_mw:
        raise ValueError("power_min_mw must be <= power_max_mw.")

    values = np.arange(power_min_mw, power_max_mw + 1e-9, power_step_mw)
    rounded = [float(np.round(v, 6)) for v in values]
    deduped = sorted(set(rounded))
    if not deduped:
        raise ValueError("Generated power grid is empty.")
    return deduped


def _build_config_id(power_mw: float, duration_h: float) -> str:
    return f"P{power_mw:g}_D{duration_h:g}"


def run_bess_sizing_screening(
    *,
    aligned_hourly_df: pd.DataFrame,
    powers_mw: List[float],
    durations_h: List[float],
    soc_min: float = 0.15,
    soc_max: float = 0.95,
    soc_initial: float = 0.50,
    eta_charge: float = 0.922,
    eta_discharge: float = 0.922,
    enforce_terminal_soc: bool = True,
    prefer_lp: bool = True,
    tmy_coherence: Dict[str, Any] | None = None,
) -> BessSizingRunResult:
    if aligned_hourly_df.empty:
        raise ValueError("aligned_hourly_df cannot be empty.")
    if not powers_mw:
        raise ValueError("powers_mw cannot be empty.")
    if not durations_h:
        raise ValueError("durations_h cannot be empty.")

    required_cols = {"timestamp", "pv_mwh", "price_eur_per_mwh"}
    missing = required_cols - set(aligned_hourly_df.columns)
    if missing:
        raise ValueError(
            "aligned_hourly_df missing required column(s): "
            + ", ".join(sorted(missing))
        )

    warnings: List[str] = []
    summary_rows: List[Dict[str, Any]] = []
    dispatch_by_config: Dict[str, pd.DataFrame] = {}

    for power in sorted(set(float(x) for x in powers_mw)):
        if power <= 0:
            raise ValueError("All power values must be > 0.")

        for duration in sorted(set(float(x) for x in durations_h)):
            if duration <= 0:
                raise ValueError("All duration values must be > 0.")

            config_id = _build_config_id(power, duration)
            energy_nominal = power * duration

            params = BatteryParameters(
                p_charge_max_mw=power,
                p_discharge_max_mw=power,
                energy_nominal_mwh=energy_nominal,
                soc_min=soc_min,
                soc_max=soc_max,
                soc_initial=soc_initial,
                eta_charge=eta_charge,
                eta_discharge=eta_discharge,
            )

            result: DispatchOptimizationResult = optimize_dispatch_hourly(
                aligned_hourly_df=aligned_hourly_df,
                battery_params=params,
                enforce_terminal_soc=enforce_terminal_soc,
                prefer_lp=prefer_lp,
            )
            warnings.extend(result.warnings)

            dispatch_by_config[config_id] = result.dispatch_df

            row = {
                "config_id": config_id,
                "power_mw": power,
                "duration_h": duration,
                "energy_nominal_mwh": energy_nominal,
                "soc_min": soc_min,
                "soc_max": soc_max,
                "soc_initial": soc_initial,
                "eta_charge": eta_charge,
                "eta_discharge": eta_discharge,
                "roundtrip_efficiency": eta_charge * eta_discharge,
                "solver": result.solver,
                "solver_status": result.solver_status,
            }
            row.update(result.kpis)
            summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    if summary_df.empty:
        raise RuntimeError("BESS sizing produced no scenario.")

    summary_df = summary_df.sort_values(
        by=["gain_annual_abs_eur", "power_mw", "duration_h"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    best_config_id = str(summary_df.loc[0, "config_id"])

    score_matrix = (
        summary_df.pivot_table(
            index="power_mw",
            columns="duration_h",
            values="gain_annual_abs_eur",
            aggfunc="mean",
        )
        .sort_index(axis=0)
        .sort_index(axis=1)
    )

    assumptions = {
        "time_step_hours": 1.0,
        "market_role": "price signal for value maximization",
        "pv_role": "main available energy series",
        "tmy_role": "coherence only in v1",
        "grid_charging_allowed": False,
        "services_included": False,
        "capex_opex_included": False,
        "degradation_model": "none_v1",
        "dispatch_horizon": "historical_year_with_perfect_foresight",
        "enforce_terminal_soc": enforce_terminal_soc,
        "solver_preference": "lp_if_available" if prefer_lp else "heuristic_only",
        "soc_defaults": {
            "soc_min": soc_min,
            "soc_max": soc_max,
            "soc_initial": soc_initial,
        },
    }

    return BessSizingRunResult(
        aligned_hourly_df=aligned_hourly_df.copy(),
        summary_df=summary_df,
        score_matrix_gain_eur=score_matrix,
        dispatch_by_config=dispatch_by_config,
        tmy_coherence=tmy_coherence or {"available": False},
        warnings=list(dict.fromkeys(warnings)),
        assumptions=assumptions,
        best_config_id=best_config_id,
    )
