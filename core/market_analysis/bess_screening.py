# core/market_analysis/bess_screening.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from core.market_analysis.market_price_analysis import MarketPVAnalysisResult

SEASON_ORDER = ["winter", "spring", "summer", "autumn"]


@dataclass
class BESSScreeningResult:
    hourly_data: pd.DataFrame
    annual_indicators: Dict[str, Any]
    monthly_summary: pd.DataFrame
    seasonal_summary: pd.DataFrame
    assumptions_used: Dict[str, Any]
    meta: Dict[str, Any]
    warnings: List[str]


# =============================================================================
# Defaults / helpers
# =============================================================================

def _safe_div(numerator: float, denominator: float) -> Optional[float]:
    if denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _sort_season_df(df: pd.DataFrame) -> pd.DataFrame:
    if "season" in df.columns:
        out = df.copy()
        out["season"] = pd.Categorical(out["season"], categories=SEASON_ORDER, ordered=True)
        out = out.sort_values("season").reset_index(drop=True)
        return out
    return df


def _coalesce_param(
    user_params: Dict[str, Any],
    key: str,
    default_value: Any,
    source_flags: Dict[str, str],
) -> Any:
    if key in user_params and user_params[key] not in (None, ""):
        source_flags[key] = "user"
        return user_params[key]
    source_flags[key] = "default"
    return default_value


def _build_default_bess_params(analysis_result: MarketPVAnalysisResult) -> Dict[str, Any]:
    annual = analysis_result.annual_indicators

    energy_curtailed_negative_mwh = annual.get("energy_curtailed_negative_mwh") or 0.0
    variant_label = analysis_result.meta.get("variant_label", "")

    # Defaults intentionally simple / indicative
    return {
        "capacity_mwh": max(1.0, energy_curtailed_negative_mwh / 4.0) if energy_curtailed_negative_mwh > 0 else 5.0,
        "charge_power_mw": 5.0,
        "discharge_power_mw": 5.0,
        "roundtrip_efficiency": 0.90,
        "charge_price_threshold_eur_per_mwh": 0.0,
        "discharge_price_threshold_eur_per_mwh": annual.get("avg_market_price_eur_per_mwh", 60.0) or 60.0,
        "variant_label": variant_label,
    }


def _normalize_bess_params(
    analysis_result: MarketPVAnalysisResult,
    user_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    user_params = user_params or {}
    defaults = _build_default_bess_params(analysis_result)
    source_flags: Dict[str, str] = {}

    params = {
        "capacity_mwh": float(_coalesce_param(user_params, "capacity_mwh", defaults["capacity_mwh"], source_flags)),
        "charge_power_mw": float(_coalesce_param(user_params, "charge_power_mw", defaults["charge_power_mw"], source_flags)),
        "discharge_power_mw": float(_coalesce_param(user_params, "discharge_power_mw", defaults["discharge_power_mw"], source_flags)),
        "roundtrip_efficiency": float(_coalesce_param(user_params, "roundtrip_efficiency", defaults["roundtrip_efficiency"], source_flags)),
        "charge_price_threshold_eur_per_mwh": float(
            _coalesce_param(
                user_params,
                "charge_price_threshold_eur_per_mwh",
                defaults["charge_price_threshold_eur_per_mwh"],
                source_flags,
            )
        ),
        "discharge_price_threshold_eur_per_mwh": float(
            _coalesce_param(
                user_params,
                "discharge_price_threshold_eur_per_mwh",
                defaults["discharge_price_threshold_eur_per_mwh"],
                source_flags,
            )
        ),
        "variant_label": str(_coalesce_param(user_params, "variant_label", defaults["variant_label"], source_flags)),
        "param_sources": source_flags,
    }

    if params["capacity_mwh"] <= 0:
        raise ValueError("capacity_mwh must be > 0.")
    if params["charge_power_mw"] <= 0:
        raise ValueError("charge_power_mw must be > 0.")
    if params["discharge_power_mw"] <= 0:
        raise ValueError("discharge_power_mw must be > 0.")
    if not (0 < params["roundtrip_efficiency"] <= 1.0):
        raise ValueError("roundtrip_efficiency must be in ]0, 1].")

    return params


# =============================================================================
# Core simulation
# =============================================================================

def run_bess_screening(
    analysis_result: MarketPVAnalysisResult,
    bess_params: Optional[Dict[str, Any]] = None,
) -> BESSScreeningResult:
    """
    Simplified indicative BESS screening.

    Logic:
    - charge only from energy curtailed during negative-price hours
    - discharge only during hours above discharge threshold
    - market timestamp remains the reference
    - 1-hour timestep assumed
    """
    warnings: List[str] = []

    df = analysis_result.merged_data.copy()
    if df.empty:
        raise ValueError("Cannot run BESS screening on an empty merged dataset.")

    params = _normalize_bess_params(analysis_result, bess_params)

    capacity_mwh = params["capacity_mwh"]
    charge_power_mw = params["charge_power_mw"]
    discharge_power_mw = params["discharge_power_mw"]
    roundtrip_efficiency = params["roundtrip_efficiency"]
    charge_threshold = params["charge_price_threshold_eur_per_mwh"]
    discharge_threshold = params["discharge_price_threshold_eur_per_mwh"]

    # Split roundtrip efficiency symmetrically
    eta_charge = roundtrip_efficiency ** 0.5
    eta_discharge = roundtrip_efficiency ** 0.5

    out = df.copy()

    # Available curtailed energy that could be stored
    out["bess_charge_candidate_mwh"] = 0.0
    out["bess_discharge_candidate_mwh"] = 0.0

    # Charge candidate:
    # use curtailed energy from negative-price hours, optionally threshold-based
    charge_mask = (
        (out["e_grid_curtailed_negative_mwh"] > 0.0)
        & (out["price_eur_per_mwh"] <= charge_threshold)
    )
    out.loc[charge_mask, "bess_charge_candidate_mwh"] = out.loc[charge_mask, "e_grid_curtailed_negative_mwh"]

    # Discharge candidate:
    # allow discharge on high-price hours
    discharge_mask = out["price_eur_per_mwh"] >= discharge_threshold
    out.loc[discharge_mask, "bess_discharge_candidate_mwh"] = discharge_power_mw  # 1h timestep -> MWh candidate

    # Storage state simulation
    soc_before = []
    soc_after = []
    charged_from_source_mwh = []
    charged_into_battery_mwh = []
    discharged_from_battery_mwh = []
    discharged_to_grid_mwh = []
    losses_charge_mwh = []
    losses_discharge_mwh = []
    bess_market_value_eur = []

    soc = 0.0

    for _, row in out.iterrows():
        soc_beg = soc

        # -------------------------------------------------------------
        # Charge
        # -------------------------------------------------------------
        charge_candidate_source = float(row["bess_charge_candidate_mwh"])
        charge_limit_source = charge_power_mw  # 1h timestep
        charge_source = min(charge_candidate_source, charge_limit_source)

        # Energy entering battery after charge losses
        charge_into_battery = charge_source * eta_charge

        # Respect remaining capacity
        remaining_capacity = max(0.0, capacity_mwh - soc)
        if charge_into_battery > remaining_capacity:
            charge_into_battery = remaining_capacity
            charge_source = charge_into_battery / eta_charge if eta_charge > 0 else 0.0

        charge_loss = max(0.0, charge_source - charge_into_battery)
        soc += charge_into_battery

        # -------------------------------------------------------------
        # Discharge
        # -------------------------------------------------------------
        discharge_candidate_to_grid = float(row["bess_discharge_candidate_mwh"])

        # max energy that can leave battery before discharge loss
        max_from_battery = min(discharge_power_mw, soc)

        # corresponding energy to grid after discharge efficiency
        max_to_grid = max_from_battery * eta_discharge

        discharge_to_grid = min(discharge_candidate_to_grid, max_to_grid)
        discharge_from_battery = discharge_to_grid / eta_discharge if eta_discharge > 0 else 0.0

        # adjust SOC
        discharge_from_battery = min(discharge_from_battery, soc)
        discharge_to_grid = discharge_from_battery * eta_discharge
        discharge_loss = max(0.0, discharge_from_battery - discharge_to_grid)
        soc -= discharge_from_battery

        # Economic value of discharged energy
        value_eur = discharge_to_grid * float(row["price_eur_per_mwh"])

        soc_end = soc

        soc_before.append(soc_beg)
        soc_after.append(soc_end)
        charged_from_source_mwh.append(charge_source)
        charged_into_battery_mwh.append(charge_into_battery)
        discharged_from_battery_mwh.append(discharge_from_battery)
        discharged_to_grid_mwh.append(discharge_to_grid)
        losses_charge_mwh.append(charge_loss)
        losses_discharge_mwh.append(discharge_loss)
        bess_market_value_eur.append(value_eur)

    out["bess_soc_before_mwh"] = soc_before
    out["bess_soc_after_mwh"] = soc_after
    out["bess_charge_from_source_mwh"] = charged_from_source_mwh
    out["bess_charge_into_battery_mwh"] = charged_into_battery_mwh
    out["bess_discharge_from_battery_mwh"] = discharged_from_battery_mwh
    out["bess_discharge_to_grid_mwh"] = discharged_to_grid_mwh
    out["bess_charge_losses_mwh"] = losses_charge_mwh
    out["bess_discharge_losses_mwh"] = losses_discharge_mwh
    out["bess_total_losses_mwh"] = out["bess_charge_losses_mwh"] + out["bess_discharge_losses_mwh"]
    out["bess_market_value_eur"] = bess_market_value_eur

    # Opportunity metrics
    out["bess_is_charging"] = out["bess_charge_from_source_mwh"] > 0.0
    out["bess_is_discharging"] = out["bess_discharge_to_grid_mwh"] > 0.0

    # Add a simple total value with BESS overlay:
    # existing market value + value of discharged stored energy
    # (we do not subtract charge cost here because source energy was curtailed)
    out["market_value_with_bess_eur"] = out["market_value_eur"] + out["bess_market_value_eur"]

    # -------------------------------------------------------------------------
    # Annual indicators
    # -------------------------------------------------------------------------
    energy_available_for_storage_mwh = float(out["e_grid_curtailed_negative_mwh"].sum())
    energy_charged_from_source_mwh = float(out["bess_charge_from_source_mwh"].sum())
    energy_charged_into_battery_mwh = float(out["bess_charge_into_battery_mwh"].sum())
    energy_discharged_to_grid_mwh = float(out["bess_discharge_to_grid_mwh"].sum())
    total_losses_mwh = float(out["bess_total_losses_mwh"].sum())
    bess_market_value_eur = float(out["bess_market_value_eur"].sum())
    market_value_base_eur = float(out["market_value_eur"].sum())
    market_value_with_bess_eur = float(out["market_value_with_bess_eur"].sum())

    equivalent_cycles = _safe_div(energy_discharged_to_grid_mwh, capacity_mwh)
    storage_recovery_ratio = _safe_div(energy_discharged_to_grid_mwh, energy_available_for_storage_mwh)

    annual_indicators = {
        "energy_available_for_storage_mwh": energy_available_for_storage_mwh,
        "energy_charged_from_source_mwh": energy_charged_from_source_mwh,
        "energy_charged_into_battery_mwh": energy_charged_into_battery_mwh,
        "energy_discharged_to_grid_mwh": energy_discharged_to_grid_mwh,
        "total_losses_mwh": total_losses_mwh,
        "market_value_base_eur": market_value_base_eur,
        "bess_added_value_eur": bess_market_value_eur,
        "market_value_with_bess_eur": market_value_with_bess_eur,
        "equivalent_cycles": equivalent_cycles,
        "storage_recovery_ratio": storage_recovery_ratio,
        "max_soc_mwh": float(out["bess_soc_after_mwh"].max()),
        "charge_hours": int(out["bess_is_charging"].sum()),
        "discharge_hours": int(out["bess_is_discharging"].sum()),
    }

    # -------------------------------------------------------------------------
    # Monthly summary
    # -------------------------------------------------------------------------
    monthly_summary = (
        out.groupby("month", dropna=False)
        .agg(
            energy_available_for_storage_mwh=("e_grid_curtailed_negative_mwh", "sum"),
            energy_charged_from_source_mwh=("bess_charge_from_source_mwh", "sum"),
            energy_discharged_to_grid_mwh=("bess_discharge_to_grid_mwh", "sum"),
            total_losses_mwh=("bess_total_losses_mwh", "sum"),
            bess_added_value_eur=("bess_market_value_eur", "sum"),
            max_soc_mwh=("bess_soc_after_mwh", "max"),
            charge_hours=("bess_is_charging", "sum"),
            discharge_hours=("bess_is_discharging", "sum"),
        )
        .reset_index()
        .sort_values("month")
        .reset_index(drop=True)
    )

    monthly_summary["storage_recovery_ratio"] = monthly_summary.apply(
        lambda r: _safe_div(r["energy_discharged_to_grid_mwh"], r["energy_available_for_storage_mwh"]),
        axis=1,
    )

    # -------------------------------------------------------------------------
    # Seasonal summary
    # -------------------------------------------------------------------------
    seasonal_summary = (
        out.groupby("season", dropna=False)
        .agg(
            energy_available_for_storage_mwh=("e_grid_curtailed_negative_mwh", "sum"),
            energy_charged_from_source_mwh=("bess_charge_from_source_mwh", "sum"),
            energy_discharged_to_grid_mwh=("bess_discharge_to_grid_mwh", "sum"),
            total_losses_mwh=("bess_total_losses_mwh", "sum"),
            bess_added_value_eur=("bess_market_value_eur", "sum"),
            max_soc_mwh=("bess_soc_after_mwh", "max"),
            charge_hours=("bess_is_charging", "sum"),
            discharge_hours=("bess_is_discharging", "sum"),
        )
        .reset_index()
    )
    seasonal_summary["storage_recovery_ratio"] = seasonal_summary.apply(
        lambda r: _safe_div(r["energy_discharged_to_grid_mwh"], r["energy_available_for_storage_mwh"]),
        axis=1,
    )
    seasonal_summary = _sort_season_df(seasonal_summary)

    assumptions_used = {
        "capacity_mwh": capacity_mwh,
        "charge_power_mw": charge_power_mw,
        "discharge_power_mw": discharge_power_mw,
        "roundtrip_efficiency": roundtrip_efficiency,
        "charge_price_threshold_eur_per_mwh": charge_threshold,
        "discharge_price_threshold_eur_per_mwh": discharge_threshold,
        "variant_label": params["variant_label"],
        "param_sources": params["param_sources"],
        "logic_note": (
            "Indicative BESS screening only. Charge from curtailed negative-price energy, "
            "discharge on hours above threshold, 1h timestep, simplified efficiency model."
        ),
    }

    meta = {
        "schema_version": "bess_screening_v1",
        "backend_energy_unit": "MWh",
        "backend_power_unit": "MW",
        "backend_price_unit": "EUR/MWh",
        "backend_value_unit": "EUR",
        "variant_label": params["variant_label"],
        "time_start": out["timestamp"].min().isoformat(),
        "time_end": out["timestamp"].max().isoformat(),
    }

    # Warnings
    if energy_available_for_storage_mwh <= 0:
        warnings.append("No curtailed negative-price energy available for storage in this dataset.")
    if annual_indicators["max_soc_mwh"] >= capacity_mwh:
        warnings.append("Battery reaches full capacity at least once; capacity may be limiting.")
    if annual_indicators["equivalent_cycles"] is not None and annual_indicators["equivalent_cycles"] > 365:
        warnings.append("Equivalent cycle count is high for this simplified screening; review assumptions.")

    return BESSScreeningResult(
        hourly_data=out,
        annual_indicators=annual_indicators,
        monthly_summary=monthly_summary,
        seasonal_summary=seasonal_summary,
        assumptions_used=assumptions_used,
        meta=meta,
        warnings=warnings,
    )