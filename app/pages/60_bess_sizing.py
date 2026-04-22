from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.bootstrap import bootstrap, configure_page
from config.tools_registry import get_tool_icon
from core.bess_sizing.data_io import (
    ParsedInputTable,
    align_market_prices_to_pv_profile,
    compute_tmy_coherence,
    detect_price_unit_from_metadata,
    detect_pv_unit_from_metadata,
    fetch_market_prices_hourly_from_api,
    load_market_input_table,
    load_pv_input_table,
    load_tmy_input_table,
    prepare_market_hourly_series,
    prepare_pv_hourly_series,
    prepare_tmy_hourly_series,
)
from core.bess_sizing.v2_defaults import get_default_economic_inputs
from core.bess_sizing.v2_models import (
    BessEconomicInputs,
    BessSweepV2Result,
    BessTechnicalInputs,
    MarginalAnalysisInputs,
)
from core.bess_sizing.v2_runner import (
    run_bess_sizing_v2,
)
from ui.i18n import t
from ui.tool_layout import section, tool_header_from_registry
from ui.tool_state import get, init_tool_state, set_


TOOL_ID = "bess_sizing"

configure_page(
    page_title="BESS PV Sizing",
    page_icon=get_tool_icon(TOOL_ID, "🔋"),
    layout="wide",
)
bootstrap(render_sidebar_ui=True)

DEFAULT_ECON = get_default_economic_inputs()

init_tool_state(
    TOOL_ID,
    defaults={
        "market_source_mode": "api",
        "market_bzn": "FR",
        "market_year": 2025,
        "pv_peak_power_mw": 50.0,
        "optimization_goal": "techno_economic",
        "soc_min": 0.15,
        "soc_max": 0.95,
        "soc_initial": 0.50,
        "roundtrip_efficiency": 0.85,
        "enforce_terminal_soc": True,
        "allow_grid_charging": False,
        "use_grid_injection_limit": False,
        "grid_injection_limit_mw": 10.0,
        "ignore_capex_opex": False,
        "degradation_cost_eur_per_mwh": 0.0,
        "auxiliary_losses_mwh_per_h": 0.0,
        "solver_mode": "auto",
        "capex_power_eur_per_kw": float(DEFAULT_ECON.capex_power_eur_per_kw),
        "capex_energy_eur_per_kwh": float(DEFAULT_ECON.capex_energy_eur_per_kwh),
        "capex_fixed_eur": float(DEFAULT_ECON.capex_fixed_eur),
        "opex_fixed_pct_capex": float(DEFAULT_ECON.opex_fixed_pct_capex),
        "opex_fixed_eur_per_year": float(DEFAULT_ECON.opex_fixed_eur_per_year),
        "opex_variable_eur_per_mwh_throughput": float(DEFAULT_ECON.opex_variable_eur_per_mwh_throughput),
        "project_life_years": int(DEFAULT_ECON.project_life_years),
        "discount_rate": float(DEFAULT_ECON.discount_rate),
        "replacement_year_enabled": bool(DEFAULT_ECON.replacement_year is not None),
        "replacement_year": int(DEFAULT_ECON.replacement_year or 8),
        "replacement_fraction_capex": float(DEFAULT_ECON.replacement_fraction_capex),
        "last_result": None,
        "last_prepared_data": None,
        "selected_config_id": "",
    },
)

tool_header_from_registry(TOOL_ID)

PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "bess_screening",
        "height": 720,
        "width": 1300,
        "scale": 2,
    },
}

BZN_OPTIONS: Dict[str, str] = {
    "France": "FR",
    "Germany / Luxembourg": "DE-LU",
    "Belgium": "BE",
    "Netherlands": "NL",
    "Spain": "ES",
    "Italy North": "IT-North",
    "Poland": "PL",
    "Switzerland": "CH",
    "Denmark 1": "DK1",
    "Denmark 2": "DK2",
}

PV_UNIT_OPTIONS = ["auto", "Wh", "kWh", "MWh", "W", "kW", "MW"]
PRICE_UNIT_OPTIONS = ["auto", "EUR/MWh", "EUR/kWh", "cEUR/kWh"]
DEFAULT_SCENARIO_POWER_RATIOS = [0.25, 0.50, 0.75, 1.00]
DEFAULT_SCENARIO_DURATIONS_H = list(range(1, 9))
CRE_REFERENCE_POWER_RATIO = 0.50
CRE_REFERENCE_DURATION_H = 2.0


def _fmt(value: Any, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    try:
        return f"{float(value):,.{decimals}f}".replace(",", " ")
    except Exception:
        return str(value)


def _fmt_compact(value: Any, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    try:
        v = float(value)
        if abs(v - round(v)) < 1e-9:
            return f"{int(round(v)):,}".replace(",", " ")
        return f"{v:,.{decimals}f}".replace(",", " ")
    except Exception:
        return str(value)


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")


def _title_with_help(title_key: str, help_key: str, level: int = 3) -> None:
    cols = st.columns([0.965, 0.035])
    with cols[0]:
        if level == 2:
            st.markdown(f"## {t(title_key)}")
        elif level == 4:
            st.markdown(f"#### {t(title_key)}")
        else:
            st.markdown(f"### {t(title_key)}")
    with cols[1]:
        with st.popover("\u2071"):
            st.markdown(t(help_key))


def _friendly_config_label(
    power_mw: float,
    duration_h: float,
    energy_mwh: float,
    *,
    power_ratio_pv: float | None = None,
    is_cre_reference: bool = False,
) -> str:
    ratio_txt = ""
    if power_ratio_pv is not None and np.isfinite(float(power_ratio_pv)):
        ratio_txt = f" ({float(power_ratio_pv):.2f}x Ppv)"
    label = (
        f"{_fmt_compact(power_mw, 1)} MW{ratio_txt} / "
        f"{_fmt_compact(duration_h, 1)} h "
        f"({_fmt_compact(energy_mwh, 1)} MWh)"
    )
    if is_cre_reference:
        label += " [CRE]"
    return label


def _build_power_grid_from_pv_peak(
    *,
    pv_peak_power_mw: float,
    power_ratios: List[float],
) -> List[float]:
    if pv_peak_power_mw <= 0:
        raise ValueError("pv_peak_power_mw must be > 0.")
    values = [
        float(np.round(float(pv_peak_power_mw) * float(ratio), 6))
        for ratio in power_ratios
        if float(ratio) > 0
    ]
    deduped = sorted(set(values))
    if not deduped:
        raise ValueError("Generated power grid is empty.")
    return deduped


def _attach_scenario_context(summary_df: pd.DataFrame, *, pv_peak_power_mw: float) -> pd.DataFrame:
    work = summary_df.copy()
    if "power_mw" not in work.columns or "duration_h" not in work.columns:
        return work
    if pv_peak_power_mw <= 0:
        work["power_ratio_pv"] = np.nan
        work["is_cre_reference"] = 0
        return work

    work["power_ratio_pv"] = pd.to_numeric(work["power_mw"], errors="coerce") / float(pv_peak_power_mw)
    work["is_cre_reference"] = (
        np.isclose(work["power_ratio_pv"], CRE_REFERENCE_POWER_RATIO, atol=1e-6)
        & np.isclose(pd.to_numeric(work["duration_h"], errors="coerce"), CRE_REFERENCE_DURATION_H, atol=1e-6)
    ).astype(int)
    return work


def _find_cre_config_id(summary_df: pd.DataFrame) -> str | None:
    if summary_df is None or summary_df.empty:
        return None
    if "is_cre_reference" in summary_df.columns:
        cre_rows = summary_df.loc[summary_df["is_cre_reference"].astype(int) == 1]
        if not cre_rows.empty:
            return str(cre_rows.iloc[0]["config_id"])
    if "power_ratio_pv" in summary_df.columns:
        cre_rows = summary_df.loc[
            np.isclose(pd.to_numeric(summary_df["power_ratio_pv"], errors="coerce"), CRE_REFERENCE_POWER_RATIO, atol=1e-6)
            & np.isclose(pd.to_numeric(summary_df["duration_h"], errors="coerce"), CRE_REFERENCE_DURATION_H, atol=1e-6)
        ]
        if not cre_rows.empty:
            return str(cre_rows.iloc[0]["config_id"])
    return None


def _negative_price_context_table(
    *,
    aligned_df: pd.DataFrame,
    optimum_dispatch: pd.DataFrame,
    cre_dispatch: pd.DataFrame,
) -> pd.DataFrame:
    if (
        aligned_df is None
        or aligned_df.empty
        or "timestamp" not in aligned_df.columns
        or "price_eur_per_mwh" not in aligned_df.columns
    ):
        return pd.DataFrame()

    base = aligned_df.copy()
    base["timestamp"] = pd.to_datetime(base["timestamp"], errors="coerce")
    base["price_eur_per_mwh"] = pd.to_numeric(base["price_eur_per_mwh"], errors="coerce")
    if "pv_mwh" in base.columns:
        base["pv_mwh"] = pd.to_numeric(base["pv_mwh"], errors="coerce")
    else:
        base["pv_mwh"] = np.nan
    base = base.dropna(subset=["timestamp", "price_eur_per_mwh"]).sort_values("timestamp")
    negatives = base.loc[base["price_eur_per_mwh"] < 0].head(2)
    if negatives.empty:
        return pd.DataFrame()

    out = negatives[["timestamp", "price_eur_per_mwh", "pv_mwh"]].copy()
    out = out.rename(
        columns={
            "price_eur_per_mwh": "price_eur_mwh",
            "pv_mwh": "pv_generation_mwh",
        }
    )

    def _merge_dispatch(prefix: str, dispatch_df: pd.DataFrame) -> None:
        nonlocal out
        if dispatch_df is None or dispatch_df.empty or "timestamp" not in dispatch_df.columns:
            return
        cols = [
            c
            for c in [
                "timestamp",
                "charge_total_mwh",
                "charge_from_pv_mwh",
                "charge_from_grid_mwh",
                "discharge_to_grid_mwh",
                "net_grid_export_mwh",
                "soc_mwh",
            ]
            if c in dispatch_df.columns
        ]
        tmp = dispatch_df[cols].copy()
        tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
        rename_map = {c: f"{prefix}_{c}" for c in cols if c != "timestamp"}
        tmp = tmp.rename(columns=rename_map)
        out_cols = ["timestamp"] + list(rename_map.values())
        out = out.merge(tmp[out_cols], on="timestamp", how="left")

    _merge_dispatch("opt", optimum_dispatch)
    _merge_dispatch("cre", cre_dispatch)
    return out.sort_values("timestamp").reset_index(drop=True)


def _summary_display_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    work = summary_df.copy()
    work["config_display"] = work.apply(
        lambda r: _friendly_config_label(
            float(r["power_mw"]),
            float(r["duration_h"]),
            float(r["energy_nominal_mwh"]),
            power_ratio_pv=(
                float(r["power_ratio_pv"])
                if "power_ratio_pv" in r and pd.notna(r["power_ratio_pv"])
                else None
            ),
            is_cre_reference=(
                bool(int(r["is_cre_reference"]))
                if "is_cre_reference" in r and pd.notna(r["is_cre_reference"])
                else False
            ),
        ),
        axis=1,
    )

    if "is_cre_reference" in work.columns:
        work["scenario_type"] = work["is_cre_reference"].map(
            lambda x: "CRE reference" if int(x) == 1 else "Scenario matrix"
        )

    ordered_cols = [
        "config_display",
        "power_mw",
        "power_ratio_pv",
        "duration_h",
        "energy_nominal_mwh",
        "scenario_type",
        "revenue_pv_only_eur",
        "revenue_pv_bess_eur",
        "gain_annual_abs_eur",
        "gain_annual_rel_pct",
        "capture_price_pv_only_eur_per_mwh",
        "capture_price_pv_bess_eur_per_mwh",
        "energy_charged_mwh",
        "energy_charged_from_pv_mwh",
        "energy_charged_from_grid_mwh",
        "energy_discharged_mwh",
        "losses_mwh",
        "throughput_mwh",
        "equivalent_cycles",
        "utilization_rate_pct",
        "gain_share_of_max_pct",
        "marginal_gain_per_mw_eur",
        "marginal_gain_per_mwh_eur",
        "used_capacity_share_pct",
        "underutilized_capacity_share_pct",
        "power_saturation_rate_pct",
        "energy_saturation_rate_pct",
        "annual_net_margin_eur",
        "annual_net_revenue_eur",
        "annualized_cost_total_eur",
        "capex_total_eur",
        "opex_total_annual_eur",
        "simple_payback_years",
        "npv_eur",
        "hours_power_saturated",
        "hours_energy_saturated",
        "solver",
    ]
    ordered_cols = [c for c in ordered_cols if c in work.columns]
    work = work[ordered_cols].copy()

    format_specs = {
        "power_mw": 1,
        "power_ratio_pv": 2,
        "duration_h": 1,
        "energy_nominal_mwh": 1,
        "revenue_pv_only_eur": 0,
        "revenue_pv_bess_eur": 0,
        "gain_annual_abs_eur": 0,
        "gain_annual_rel_pct": 2,
        "capture_price_pv_only_eur_per_mwh": 1,
        "capture_price_pv_bess_eur_per_mwh": 1,
        "energy_charged_mwh": 1,
        "energy_charged_from_pv_mwh": 1,
        "energy_charged_from_grid_mwh": 1,
        "energy_discharged_mwh": 1,
        "losses_mwh": 1,
        "throughput_mwh": 1,
        "equivalent_cycles": 1,
        "utilization_rate_pct": 2,
        "gain_share_of_max_pct": 2,
        "marginal_gain_per_mw_eur": 1,
        "marginal_gain_per_mwh_eur": 1,
        "used_capacity_share_pct": 2,
        "underutilized_capacity_share_pct": 2,
        "power_saturation_rate_pct": 2,
        "energy_saturation_rate_pct": 2,
        "annual_net_margin_eur": 0,
        "annual_net_revenue_eur": 0,
        "annualized_cost_total_eur": 0,
        "capex_total_eur": 0,
        "opex_total_annual_eur": 0,
        "simple_payback_years": 2,
        "npv_eur": 0,
        "hours_power_saturated": 0,
        "hours_energy_saturated": 0,
    }
    for col, dec in format_specs.items():
        if col in work.columns:
            work[col] = work[col].map(lambda x: _fmt(x, dec))

    col_labels = {
        "config_display": t("BESS_SIZING_COL_CONFIG"),
        "power_mw": t("BESS_SIZING_COL_POWER"),
        "power_ratio_pv": "Ratio P_BESS / P_PV",
        "duration_h": t("BESS_SIZING_COL_DURATION"),
        "energy_nominal_mwh": t("BESS_SIZING_COL_ENERGY"),
        "scenario_type": "Type de scenario",
        "revenue_pv_only_eur": t("BESS_SIZING_COL_REVENUE_PV_ONLY"),
        "revenue_pv_bess_eur": t("BESS_SIZING_COL_REVENUE_PV_BESS"),
        "gain_annual_abs_eur": t("BESS_SIZING_COL_GAIN_ABS"),
        "gain_annual_rel_pct": t("BESS_SIZING_COL_GAIN_REL"),
        "capture_price_pv_only_eur_per_mwh": t("BESS_SIZING_COL_CAPTURE_PV_ONLY"),
        "capture_price_pv_bess_eur_per_mwh": t("BESS_SIZING_COL_CAPTURE_PV_BESS"),
        "energy_charged_mwh": t("BESS_SIZING_COL_ENERGY_CHARGED"),
        "energy_charged_from_pv_mwh": t("BESS_SIZING_COL_ENERGY_CHARGED_PV"),
        "energy_charged_from_grid_mwh": t("BESS_SIZING_COL_ENERGY_CHARGED_GRID"),
        "energy_discharged_mwh": t("BESS_SIZING_COL_ENERGY_DISCHARGED"),
        "losses_mwh": t("BESS_SIZING_COL_LOSSES"),
        "throughput_mwh": t("BESS_SIZING_COL_THROUGHPUT"),
        "equivalent_cycles": t("BESS_SIZING_COL_CYCLES"),
        "utilization_rate_pct": t("BESS_SIZING_COL_UTILIZATION"),
        "gain_share_of_max_pct": t("BESS_SIZING_COL_GAIN_SHARE_MAX"),
        "marginal_gain_per_mw_eur": t("BESS_SIZING_COL_MARGINAL_MW"),
        "marginal_gain_per_mwh_eur": t("BESS_SIZING_COL_MARGINAL_MWH"),
        "used_capacity_share_pct": t("BESS_SIZING_COL_USED_CAPACITY"),
        "underutilized_capacity_share_pct": t("BESS_SIZING_COL_UNDERUTILIZED"),
        "power_saturation_rate_pct": t("BESS_SIZING_COL_POWER_SAT_RATE"),
        "energy_saturation_rate_pct": t("BESS_SIZING_COL_ENERGY_SAT_RATE"),
        "annual_net_margin_eur": t("BESS_SIZING_COL_NET_MARGIN"),
        "annual_net_revenue_eur": t("BESS_SIZING_COL_NET_REVENUE"),
        "annualized_cost_total_eur": t("BESS_SIZING_COL_ANNUALIZED_COST"),
        "capex_total_eur": t("BESS_SIZING_COL_CAPEX"),
        "opex_total_annual_eur": t("BESS_SIZING_COL_OPEX"),
        "simple_payback_years": t("BESS_SIZING_COL_PAYBACK"),
        "npv_eur": t("BESS_SIZING_COL_NPV"),
        "hours_power_saturated": t("BESS_SIZING_COL_HOURS_POWER_SAT"),
        "hours_energy_saturated": t("BESS_SIZING_COL_HOURS_ENERGY_SAT"),
        "solver": t("BESS_SIZING_COL_SOLVER"),
    }
    return work.rename(columns=col_labels)


def _summary_export_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    work = summary_df.copy()
    work["config_display"] = work.apply(
        lambda r: _friendly_config_label(
            float(r["power_mw"]),
            float(r["duration_h"]),
            float(r["energy_nominal_mwh"]),
            power_ratio_pv=(
                float(r["power_ratio_pv"])
                if "power_ratio_pv" in r and pd.notna(r["power_ratio_pv"])
                else None
            ),
            is_cre_reference=(
                bool(int(r["is_cre_reference"]))
                if "is_cre_reference" in r and pd.notna(r["is_cre_reference"])
                else False
            ),
        ),
        axis=1,
    )

    if "is_cre_reference" in work.columns:
        work["scenario_type"] = work["is_cre_reference"].map(
            lambda x: "CRE reference" if int(x) == 1 else "Scenario matrix"
        )

    ordered_cols = [
        "config_display",
        "power_mw",
        "power_ratio_pv",
        "duration_h",
        "energy_nominal_mwh",
        "scenario_type",
        "revenue_pv_only_eur",
        "revenue_pv_bess_eur",
        "gain_annual_abs_eur",
        "gain_annual_rel_pct",
        "capture_price_pv_only_eur_per_mwh",
        "capture_price_pv_bess_eur_per_mwh",
        "energy_charged_mwh",
        "energy_charged_from_pv_mwh",
        "energy_charged_from_grid_mwh",
        "energy_discharged_mwh",
        "losses_mwh",
        "throughput_mwh",
        "equivalent_cycles",
        "utilization_rate_pct",
        "gain_share_of_max_pct",
        "marginal_gain_per_mw_eur",
        "marginal_gain_per_mwh_eur",
        "used_capacity_share_pct",
        "underutilized_capacity_share_pct",
        "power_saturation_rate_pct",
        "energy_saturation_rate_pct",
        "annual_net_margin_eur",
        "annual_net_revenue_eur",
        "annualized_cost_total_eur",
        "capex_total_eur",
        "opex_total_annual_eur",
        "simple_payback_years",
        "npv_eur",
        "hours_power_saturated",
        "hours_energy_saturated",
        "solver",
    ]
    ordered_cols = [c for c in ordered_cols if c in work.columns]
    work = work[ordered_cols].copy()

    col_labels = {
        "config_display": t("BESS_SIZING_COL_CONFIG"),
        "power_mw": t("BESS_SIZING_COL_POWER"),
        "power_ratio_pv": "Ratio P_BESS / P_PV",
        "duration_h": t("BESS_SIZING_COL_DURATION"),
        "energy_nominal_mwh": t("BESS_SIZING_COL_ENERGY"),
        "scenario_type": "Type de scenario",
        "revenue_pv_only_eur": t("BESS_SIZING_COL_REVENUE_PV_ONLY"),
        "revenue_pv_bess_eur": t("BESS_SIZING_COL_REVENUE_PV_BESS"),
        "gain_annual_abs_eur": t("BESS_SIZING_COL_GAIN_ABS"),
        "gain_annual_rel_pct": t("BESS_SIZING_COL_GAIN_REL"),
        "capture_price_pv_only_eur_per_mwh": t("BESS_SIZING_COL_CAPTURE_PV_ONLY"),
        "capture_price_pv_bess_eur_per_mwh": t("BESS_SIZING_COL_CAPTURE_PV_BESS"),
        "energy_charged_mwh": t("BESS_SIZING_COL_ENERGY_CHARGED"),
        "energy_charged_from_pv_mwh": t("BESS_SIZING_COL_ENERGY_CHARGED_PV"),
        "energy_charged_from_grid_mwh": t("BESS_SIZING_COL_ENERGY_CHARGED_GRID"),
        "energy_discharged_mwh": t("BESS_SIZING_COL_ENERGY_DISCHARGED"),
        "losses_mwh": t("BESS_SIZING_COL_LOSSES"),
        "throughput_mwh": t("BESS_SIZING_COL_THROUGHPUT"),
        "equivalent_cycles": t("BESS_SIZING_COL_CYCLES"),
        "utilization_rate_pct": t("BESS_SIZING_COL_UTILIZATION"),
        "gain_share_of_max_pct": t("BESS_SIZING_COL_GAIN_SHARE_MAX"),
        "marginal_gain_per_mw_eur": t("BESS_SIZING_COL_MARGINAL_MW"),
        "marginal_gain_per_mwh_eur": t("BESS_SIZING_COL_MARGINAL_MWH"),
        "used_capacity_share_pct": t("BESS_SIZING_COL_USED_CAPACITY"),
        "underutilized_capacity_share_pct": t("BESS_SIZING_COL_UNDERUTILIZED"),
        "power_saturation_rate_pct": t("BESS_SIZING_COL_POWER_SAT_RATE"),
        "energy_saturation_rate_pct": t("BESS_SIZING_COL_ENERGY_SAT_RATE"),
        "annual_net_margin_eur": t("BESS_SIZING_COL_NET_MARGIN"),
        "annual_net_revenue_eur": t("BESS_SIZING_COL_NET_REVENUE"),
        "annualized_cost_total_eur": t("BESS_SIZING_COL_ANNUALIZED_COST"),
        "capex_total_eur": t("BESS_SIZING_COL_CAPEX"),
        "opex_total_annual_eur": t("BESS_SIZING_COL_OPEX"),
        "simple_payback_years": t("BESS_SIZING_COL_PAYBACK"),
        "npv_eur": t("BESS_SIZING_COL_NPV"),
        "hours_power_saturated": t("BESS_SIZING_COL_HOURS_POWER_SAT"),
        "hours_energy_saturated": t("BESS_SIZING_COL_HOURS_ENERGY_SAT"),
        "solver": t("BESS_SIZING_COL_SOLVER"),
    }
    return work.rename(columns=col_labels)


def _key_configs_table(summary_df: pd.DataFrame, config_ids: List[str]) -> pd.DataFrame:
    if summary_df is None or summary_df.empty or not config_ids:
        return pd.DataFrame()
    keep = [c for c in config_ids if c in set(summary_df["config_id"].astype(str))]
    if not keep:
        return pd.DataFrame()
    rows = summary_df.loc[summary_df["config_id"].astype(str).isin(keep)].copy()
    rows["rank_hint"] = rows["config_id"].astype(str).map({cid: i for i, cid in enumerate(keep)})
    rows = rows.sort_values("rank_hint").drop(columns=["rank_hint"])
    return _summary_display_table(rows)


def _safe_selectbox(label: str, options: List[str], default_value: str) -> str:
    if not options:
        return ""
    if default_value not in options:
        default_value = options[0]
    idx = options.index(default_value)
    return st.selectbox(label, options=options, index=idx)


def _resolve_default_state_value(options: List[str], state_value: Any, fallback: str) -> str:
    if options and isinstance(state_value, str) and state_value in options:
        return state_value
    if fallback in options:
        return fallback
    return options[0] if options else ""


def _prefer_pv_energy_col_egrid(options: List[str], fallback: str) -> str:
    if not options:
        return fallback
    for col in options:
        n = _norm_col_name(col)
        if n == "egrid" or "egrid" in n:
            return str(col)
    if fallback in options:
        return fallback
    return options[0]


def _parse_uploaded_pv(uploaded) -> ParsedInputTable | None:
    if uploaded is None:
        return None
    return load_pv_input_table(uploaded.getvalue())


def _parse_uploaded_tmy(uploaded) -> ParsedInputTable | None:
    if uploaded is None:
        return None
    return load_tmy_input_table(uploaded.getvalue())


def _parse_uploaded_market(uploaded) -> ParsedInputTable | None:
    if uploaded is None:
        return None
    return load_market_input_table(uploaded.getvalue())


def _plot_metric_heatmap(
    summary_df: pd.DataFrame,
    *,
    value_col: str,
    title: str,
    color_label: str,
    color_scale: str = "Viridis",
    color_midpoint: float | None = None,
    highlight_config_ids: Dict[str, str] | None = None,
) -> go.Figure:
    if summary_df is None or summary_df.empty or value_col not in summary_df.columns:
        return go.Figure()

    work = summary_df[["power_mw", "duration_h", value_col]].copy()
    work = work[work[value_col].notna()].copy()
    if work.empty:
        return go.Figure()

    matrix = (
        work.pivot_table(
            index="power_mw",
            columns="duration_h",
            values=value_col,
            aggfunc="mean",
        )
        .sort_index(axis=0)
        .sort_index(axis=1)
    )

    imshow_kwargs = dict(
        img=matrix,
        aspect="auto",
        color_continuous_scale=color_scale,
        labels={"x": "Duration (h)", "y": "Power (MW)", "color": color_label},
        title=title,
    )
    if color_midpoint is not None:
        imshow_kwargs["color_continuous_midpoint"] = float(color_midpoint)
    fig = px.imshow(**imshow_kwargs)
    fig.update_layout(height=440)

    if highlight_config_ids:
        for label, config_id in highlight_config_ids.items():
            row = summary_df.loc[summary_df["config_id"] == config_id]
            if row.empty:
                continue
            r = row.iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=[float(r["duration_h"])],
                    y=[float(r["power_mw"])],
                    mode="markers+text",
                    text=[label],
                    textposition="top center",
                    marker=dict(size=11, color="#111111", line=dict(color="#ffffff", width=1)),
                    showlegend=False,
                )
            )
    return fig


def _plot_marginal_value_evolution(summary_df: pd.DataFrame) -> go.Figure:
    if summary_df is None or summary_df.empty:
        return go.Figure()
    if "marginal_gain_per_mwh_eur" not in summary_df.columns:
        return go.Figure()

    work = summary_df[
        ["power_mw", "duration_h", "energy_nominal_mwh", "marginal_gain_per_mwh_eur"]
    ].copy()
    work = work[work["marginal_gain_per_mwh_eur"].notna()].copy()
    if work.empty:
        return go.Figure()

    fig = px.line(
        work.sort_values(["power_mw", "duration_h"]),
        x="duration_h",
        y="marginal_gain_per_mwh_eur",
        color="power_mw",
        markers=True,
        labels={
            "duration_h": "Duration (h)",
            "marginal_gain_per_mwh_eur": "Valeur marginale (EUR/MWh additionnel)",
            "power_mw": "Power (MW)",
            "energy_nominal_mwh": "Energy (MWh)",
        },
        title="Evolution de la valeur marginale (a puissance constante)",
        hover_data={"energy_nominal_mwh": ":.1f"},
    )
    fig.update_layout(height=420)
    return fig


def _plot_gain_vs_size(
    summary_df: pd.DataFrame,
    value_col: str,
    title: str,
    *,
    knee_energy_mwh: float | None = None,
    recommended_energy_mwh: float | None = None,
) -> go.Figure:
    work = (
        summary_df[["energy_nominal_mwh", "power_mw", value_col]]
        .dropna()
        .sort_values("energy_nominal_mwh")
        .copy()
    )
    fig = px.line(
        work,
        x="energy_nominal_mwh",
        y=value_col,
        color="power_mw",
        markers=True,
        labels={
            "energy_nominal_mwh": "Energy (MWh)",
            value_col: "EUR",
            "power_mw": "Power (MW)",
        },
        title=title,
    )
    fig.update_layout(height=380)
    if knee_energy_mwh is not None:
        fig.add_vline(x=float(knee_energy_mwh), line_dash="dot", line_color="#d62728")
    if recommended_energy_mwh is not None:
        fig.add_vline(x=float(recommended_energy_mwh), line_dash="dash", line_color="#2ca02c")
    return fig


def _plot_marginal_mw(summary_df: pd.DataFrame) -> go.Figure:
    work = (
        summary_df.groupby("power_mw", as_index=False)["marginal_gain_per_mw_eur"]
        .median()
        .sort_values("power_mw")
    )
    fig = px.line(
        work,
        x="power_mw",
        y="marginal_gain_per_mw_eur",
        markers=True,
        labels={
            "power_mw": "Power (MW)",
            "marginal_gain_per_mw_eur": "EUR per additional MW",
        },
        title="Marginal value of additional MW",
    )
    fig.update_layout(height=360)
    return fig


def _plot_marginal_mwh(summary_df: pd.DataFrame) -> go.Figure:
    work = (
        summary_df.groupby("energy_nominal_mwh", as_index=False)["marginal_gain_per_mwh_eur"]
        .median()
        .sort_values("energy_nominal_mwh")
    )
    fig = px.line(
        work,
        x="energy_nominal_mwh",
        y="marginal_gain_per_mwh_eur",
        markers=True,
        labels={
            "energy_nominal_mwh": "Energy (MWh)",
            "marginal_gain_per_mwh_eur": "EUR per additional MWh",
        },
        title="Marginal value of additional MWh",
    )
    fig.update_layout(height=360)
    return fig


def _plot_gain_share_curve(summary_df: pd.DataFrame, target_share_pct: float) -> go.Figure:
    work = (
        summary_df.groupby("energy_nominal_mwh", as_index=False)["gain_share_of_max_pct"]
        .max()
        .sort_values("energy_nominal_mwh")
    )
    fig = px.line(
        work,
        x="energy_nominal_mwh",
        y="gain_share_of_max_pct",
        markers=True,
        labels={
            "energy_nominal_mwh": "Energy (MWh)",
            "gain_share_of_max_pct": "Share of max gross gain (%)",
        },
        title="Share of max gross gain vs size",
    )
    fig.add_hline(y=target_share_pct, line_dash="dash", line_color="#2ca02c")
    fig.update_layout(height=360)
    return fig


def _plot_gain_vs_power(summary_df: pd.DataFrame) -> go.Figure:
    grouped = (
        summary_df.groupby("power_mw", as_index=False)["gain_annual_abs_eur"]
        .max()
        .sort_values("power_mw")
    )
    fig = px.line(
        grouped,
        x="power_mw",
        y="gain_annual_abs_eur",
        markers=True,
        labels={"power_mw": "Power (MW)", "gain_annual_abs_eur": "Annual gain (EUR)"},
        title="Annual gain vs power",
    )
    fig.update_layout(height=360)
    return fig


def _plot_gain_vs_duration(summary_df: pd.DataFrame) -> go.Figure:
    grouped = (
        summary_df.groupby("duration_h", as_index=False)["gain_annual_abs_eur"]
        .max()
        .sort_values("duration_h")
    )
    fig = px.line(
        grouped,
        x="duration_h",
        y="gain_annual_abs_eur",
        markers=True,
        labels={"duration_h": "Duration (h)", "gain_annual_abs_eur": "Annual gain (EUR)"},
        title="Annual gain vs duration",
    )
    fig.update_layout(height=360)
    return fig


def _plot_comparison_bars(selected_row: pd.Series) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Revenue",
            x=["PV only", "PV + BESS"],
            y=[selected_row["revenue_pv_only_eur"], selected_row["revenue_pv_bess_eur"]],
            yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Capture price",
            mode="lines+markers",
            x=["PV only", "PV + BESS"],
            y=[
                selected_row["capture_price_pv_only_eur_per_mwh"],
                selected_row["capture_price_pv_bess_eur_per_mwh"],
            ],
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="PV only vs PV + BESS",
        yaxis=dict(title="EUR"),
        yaxis2=dict(title="EUR/MWh", overlaying="y", side="right"),
        height=420,
    )
    return fig


def _plot_dispatch_timeseries(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["price_eur_per_mwh"],
            name="Price (EUR/MWh)",
            mode="lines",
            yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["pv_mwh"],
            name="PV (MWh)",
            mode="lines",
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["timestamp"],
            y=df["charge_from_pv_mwh"],
            name="Charge (MWh)",
            yaxis="y2",
            marker_color="#1f77b4",
            opacity=0.55,
        )
    )
    if "charge_from_grid_mwh" in df.columns:
        fig.add_trace(
            go.Bar(
                x=df["timestamp"],
                y=df["charge_from_grid_mwh"],
                name="Grid charge (MWh)",
                yaxis="y2",
                marker_color="#17becf",
                opacity=0.55,
            )
        )
    fig.add_trace(
        go.Bar(
            x=df["timestamp"],
            y=-df["discharge_to_grid_mwh"],
            name="Discharge (MWh, negative axis)",
            yaxis="y2",
            marker_color="#ff7f0e",
            opacity=0.55,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["soc_mwh"],
            name="SOC (MWh)",
            mode="lines",
            yaxis="y3",
            line=dict(width=2),
        )
    )
    fig.update_layout(
        title="Price / PV / Charge / Discharge / SOC (+charge, -discharge display)",
        barmode="relative",
        yaxis=dict(title="EUR/MWh"),
        yaxis2=dict(title="MWh", overlaying="y", side="right"),
        yaxis3=dict(
            title="SOC (MWh)",
            anchor="free",
            overlaying="y",
            side="left",
            position=0.06,
        ),
        height=520,
    )
    return fig


def _plot_dispatch_heatmap(df: pd.DataFrame) -> go.Figure:
    work = df.copy()
    work["month"] = pd.to_datetime(work["timestamp"]).dt.month
    work["hour"] = pd.to_datetime(work["timestamp"]).dt.hour
    if "charge_total_mwh" in work.columns:
        charge_col = "charge_total_mwh"
    elif "charge_from_grid_mwh" in work.columns:
        charge_col = "charge_from_pv_mwh"
        work["charge_total_mwh"] = work["charge_from_pv_mwh"] + work["charge_from_grid_mwh"]
        charge_col = "charge_total_mwh"
    else:
        charge_col = "charge_from_pv_mwh"
    work["net_dispatch_mwh"] = work["discharge_to_grid_mwh"] - work[charge_col]

    pivot = (
        work.groupby(["month", "hour"], as_index=False)["net_dispatch_mwh"]
        .mean()
        .pivot(index="month", columns="hour", values="net_dispatch_mwh")
        .sort_index()
    )
    fig = px.imshow(
        pivot,
        aspect="auto",
        labels={
            "x": "Hour",
            "y": "Month",
            "color": "Net dispatch (MWh, + discharge / - charge)",
        },
        title="Annual charge/discharge heatmap",
        color_continuous_scale="RdBu",
        origin="lower",
    )
    fig.update_layout(height=450)
    return fig


def _display_tmy_coherence(coherence: Dict[str, Any]) -> None:
    if not coherence or not coherence.get("available", False):
        st.info(coherence.get("message", t("BESS_SIZING_TMY_NO_DATA")))
        return

    c1, c2, c3 = st.columns(3)
    c1.metric(
        t("BESS_SIZING_TMY_COVERAGE"),
        f"{_fmt(coherence.get('coverage_pct'), 2)} %",
    )
    c2.metric(
        t("BESS_SIZING_TMY_MATCHED"),
        _fmt(coherence.get("matched_hours"), 0),
    )
    c3.metric(
        t("BESS_SIZING_TMY_CORR"),
        _fmt(coherence.get("pv_tmy_signal_correlation"), 3),
    )

    details = pd.DataFrame(
        [
            {"metric": t("BESS_SIZING_TMY_MATCHED"), "value": _fmt(coherence.get("matched_hours"), 0)},
            {"metric": t("BESS_SIZING_TMY_TOTAL"), "value": _fmt(coherence.get("total_hours"), 0)},
            {"metric": t("BESS_SIZING_TMY_COVERAGE"), "value": f"{_fmt(coherence.get('coverage_pct'), 2)} %"},
            {"metric": t("BESS_SIZING_TMY_CORR"), "value": _fmt(coherence.get("pv_tmy_signal_correlation"), 3)},
        ]
    )
    st.dataframe(details, width="stretch", hide_index=True)


def _display_glossary() -> None:
    terms = [
        ("BESS_SIZING_GLOSS_POWER", "BESS_SIZING_DEF_POWER"),
        ("BESS_SIZING_GLOSS_ENERGY", "BESS_SIZING_DEF_ENERGY"),
        ("BESS_SIZING_GLOSS_USABLE", "BESS_SIZING_DEF_USABLE"),
        ("BESS_SIZING_GLOSS_DURATION", "BESS_SIZING_DEF_DURATION"),
        ("BESS_SIZING_GLOSS_RTE", "BESS_SIZING_DEF_RTE"),
        ("BESS_SIZING_GLOSS_SOC", "BESS_SIZING_DEF_SOC"),
        ("BESS_SIZING_GLOSS_THROUGHPUT", "BESS_SIZING_DEF_THROUGHPUT"),
        ("BESS_SIZING_GLOSS_CYCLE", "BESS_SIZING_DEF_CYCLE"),
        ("BESS_SIZING_GLOSS_GROSS", "BESS_SIZING_DEF_GROSS"),
        ("BESS_SIZING_GLOSS_NET", "BESS_SIZING_DEF_NET"),
        ("BESS_SIZING_GLOSS_ANNUALIZED", "BESS_SIZING_DEF_ANNUALIZED"),
        ("BESS_SIZING_GLOSS_MARGINAL_OPT", "BESS_SIZING_DEF_MARGINAL_OPT"),
        ("BESS_SIZING_GLOSS_MARGINAL_GAIN", "BESS_SIZING_DEF_MARGINAL_GAIN"),
        ("BESS_SIZING_GLOSS_KNEE", "BESS_SIZING_DEF_KNEE"),
        ("BESS_SIZING_GLOSS_CAP_SAT", "BESS_SIZING_DEF_CAP_SAT"),
        ("BESS_SIZING_GLOSS_PWR_SAT", "BESS_SIZING_DEF_PWR_SAT"),
        ("BESS_SIZING_GLOSS_UNDER_OVER", "BESS_SIZING_DEF_UNDER_OVER"),
    ]
    for term_key, def_key in terms:
        st.markdown(f"- **{t(term_key)}**: {t(def_key)}")


def _goal_options() -> Dict[str, str]:
    return {
        "gross_potential": "Potentiel brut",
        "marginal_auto": "Compromis marginal automatique",
        "techno_economic": "Recommandation techno-economique",
    }


def _primary_recommendation_key(goal_key: str, techno_viable: bool) -> str | None:
    if goal_key == "gross_potential":
        return "brut_max"
    if goal_key == "marginal_auto":
        return "marginal"
    if goal_key == "techno_economic" and techno_viable:
        return "techno"
    return None


def _norm_col_name(value: Any) -> str:
    txt = str(value or "").strip().lower()
    for token in (" ", "_", "-", "/", "\\", "(", ")", "[", "]", ".", ":"):
        txt = txt.replace(token, "")
    return txt


def _find_first_column(df: pd.DataFrame, token_groups: List[List[str]]) -> str | None:
    if df is None or df.empty:
        return None
    norm_map = {_norm_col_name(c): str(c) for c in df.columns}
    for tokens in token_groups:
        for norm_name, orig_name in norm_map.items():
            if all(tok in norm_name for tok in tokens):
                return orig_name
    return None


def _plot_time_heatmap(
    df: pd.DataFrame,
    *,
    timestamp_col: str,
    value_col: str,
    title: str,
    color_label: str,
    agg: str = "mean",
    color_scale: str = "Viridis",
) -> go.Figure:
    if df is None or df.empty or timestamp_col not in df.columns or value_col not in df.columns:
        return go.Figure()
    work = df[[timestamp_col, value_col]].copy()
    work[timestamp_col] = pd.to_datetime(work[timestamp_col], errors="coerce")
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=[timestamp_col, value_col])
    if work.empty:
        return go.Figure()

    work["month"] = work[timestamp_col].dt.month
    work["hour"] = work[timestamp_col].dt.hour
    pivot = (
        work.groupby(["month", "hour"], as_index=False)[value_col]
        .agg(agg)
        .pivot(index="month", columns="hour", values=value_col)
        .sort_index()
    )
    fig = px.imshow(
        pivot,
        aspect="auto",
        labels={"x": "Hour", "y": "Month", "color": color_label},
        title=title,
        color_continuous_scale=color_scale,
        origin="lower",
    )
    fig.update_layout(height=430)
    return fig


def _plot_typical_daily_profile(
    df: pd.DataFrame,
    *,
    timestamp_col: str,
    value_col: str,
    title: str,
    y_label: str,
) -> go.Figure:
    if df is None or df.empty or timestamp_col not in df.columns or value_col not in df.columns:
        return go.Figure()
    work = df[[timestamp_col, value_col]].copy()
    work[timestamp_col] = pd.to_datetime(work[timestamp_col], errors="coerce")
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=[timestamp_col, value_col])
    if work.empty:
        return go.Figure()
    work["hour"] = work[timestamp_col].dt.hour

    stats = (
        work.groupby("hour")[value_col]
        .agg(["mean", lambda s: s.quantile(0.25), lambda s: s.quantile(0.75)])
        .reset_index()
    )
    stats.columns = ["hour", "mean", "p25", "p75"]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=stats["hour"],
            y=stats["p75"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats["hour"],
            y=stats["p25"],
            mode="lines",
            fill="tonexty",
            name="P25-P75",
            line=dict(width=0),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats["hour"],
            y=stats["mean"],
            mode="lines+markers",
            name="Moyenne",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Hour",
        yaxis_title=y_label,
        height=420,
    )
    return fig


def _plot_monthly_aggregation(
    df: pd.DataFrame,
    *,
    timestamp_col: str,
    value_col: str,
    title: str,
    y_label: str,
    agg: str = "sum",
) -> go.Figure:
    if df is None or df.empty or timestamp_col not in df.columns or value_col not in df.columns:
        return go.Figure()
    work = df[[timestamp_col, value_col]].copy()
    work[timestamp_col] = pd.to_datetime(work[timestamp_col], errors="coerce")
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=[timestamp_col, value_col])
    if work.empty:
        return go.Figure()
    work["month"] = work[timestamp_col].dt.month
    monthly = work.groupby("month", as_index=False)[value_col].agg(agg).sort_values("month")
    fig = px.bar(
        monthly,
        x="month",
        y=value_col,
        title=title,
        labels={"month": "Month", value_col: y_label},
    )
    fig.update_layout(height=360)
    return fig


def _unit_from_map(units_map: Dict[str, Any], col_name: str | None, fallback: str = "") -> str:
    if not col_name:
        return fallback
    if not isinstance(units_map, dict):
        return fallback
    if col_name in units_map and str(units_map[col_name]).strip():
        return str(units_map[col_name]).strip()

    target = _norm_col_name(col_name)
    for key, unit in units_map.items():
        if _norm_col_name(key) == target and str(unit).strip():
            return str(unit).strip()
    return fallback


def _infer_step_hours(df: pd.DataFrame, timestamp_col: str) -> float:
    if df is None or df.empty or timestamp_col not in df.columns:
        return 1.0
    ts = pd.to_datetime(df[timestamp_col], errors="coerce", dayfirst=True).dropna()
    if ts.empty:
        return 1.0
    ts = ts.sort_values().drop_duplicates()
    if len(ts) < 2:
        return 1.0
    diffs = ts.diff().dropna().dt.total_seconds() / 3600.0
    diffs = diffs[(diffs > 0) & np.isfinite(diffs)]
    if diffs.empty:
        return 1.0
    mode = diffs.mode()
    if not mode.empty:
        return float(mode.iloc[0])
    return float(diffs.median())


def _irradiance_series_to_kwh_per_m2(
    values: pd.Series,
    *,
    unit: str,
    step_hours: float,
) -> pd.Series:
    s = pd.to_numeric(values, errors="coerce")
    unit_n = _norm_col_name(unit)
    step_h = max(float(step_hours), 1e-9)

    if "kwhm2" in unit_n:
        return s
    if "whm2" in unit_n:
        return s / 1000.0
    if "kwm2" in unit_n:
        return s * step_h
    return s * step_h / 1000.0


def _plot_ghi_pv_annual_profile(
    df: pd.DataFrame,
    *,
    timestamp_col: str,
    ghi_col: str,
    pv_col: str,
    ghi_unit: str,
) -> go.Figure:
    if (
        df is None
        or df.empty
        or timestamp_col not in df.columns
        or ghi_col not in df.columns
        or pv_col not in df.columns
    ):
        return go.Figure()

    work = df[[timestamp_col, ghi_col, pv_col]].copy()
    work[timestamp_col] = pd.to_datetime(work[timestamp_col], errors="coerce", dayfirst=True)
    work[ghi_col] = pd.to_numeric(work[ghi_col], errors="coerce")
    work[pv_col] = pd.to_numeric(work[pv_col], errors="coerce")
    work = work.dropna(subset=[timestamp_col, ghi_col, pv_col])
    if work.empty:
        return go.Figure()

    step_h = _infer_step_hours(work, timestamp_col)
    work["ghi_kwh_m2"] = _irradiance_series_to_kwh_per_m2(
        work[ghi_col],
        unit=ghi_unit,
        step_hours=step_h,
    )
    work["doy"] = work[timestamp_col].dt.dayofyear

    daily = (
        work.groupby("doy", as_index=False)[["ghi_kwh_m2", pv_col]]
        .sum()
        .rename(columns={pv_col: "pv_mwh_day"})
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["doy"],
            y=daily["ghi_kwh_m2"],
            mode="lines",
            name="GHI",
            yaxis="y1",
            line=dict(color="#F2B707", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["doy"],
            y=daily["pv_mwh_day"],
            mode="lines",
            name="Production PV",
            yaxis="y2",
            line=dict(color="#0CC8F2", width=2),
        )
    )
    fig.update_layout(
        title="GHI et production PV - profil annuel",
        xaxis_title="Jour de l'annee",
        yaxis=dict(title="GHI (kWh/m2/j)"),
        yaxis2=dict(title="Production PV (MWh/j)", overlaying="y", side="right"),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
    )
    return fig


def _plot_ghi_pv_typical_daily_profile(
    df: pd.DataFrame,
    *,
    timestamp_col: str,
    ghi_col: str,
    pv_col: str,
    ghi_unit: str,
) -> go.Figure:
    if (
        df is None
        or df.empty
        or timestamp_col not in df.columns
        or ghi_col not in df.columns
        or pv_col not in df.columns
    ):
        return go.Figure()

    work = df[[timestamp_col, ghi_col, pv_col]].copy()
    work[timestamp_col] = pd.to_datetime(work[timestamp_col], errors="coerce", dayfirst=True)
    work[ghi_col] = pd.to_numeric(work[ghi_col], errors="coerce")
    work[pv_col] = pd.to_numeric(work[pv_col], errors="coerce")
    work = work.dropna(subset=[timestamp_col, ghi_col, pv_col])
    if work.empty:
        return go.Figure()

    work["hour"] = work[timestamp_col].dt.hour
    stats = (
        work.groupby("hour", as_index=False)[[ghi_col, pv_col]]
        .mean()
        .rename(columns={ghi_col: "ghi_mean", pv_col: "pv_mean"})
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=stats["hour"],
            y=stats["ghi_mean"],
            mode="lines+markers",
            name="GHI",
            yaxis="y1",
            line=dict(color="#F2B707", width=2),
            marker=dict(color="#F2B707"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats["hour"],
            y=stats["pv_mean"],
            mode="lines+markers",
            name="Production PV",
            yaxis="y2",
            line=dict(color="#0CC8F2", width=2),
            marker=dict(color="#0CC8F2"),
        )
    )
    fig.update_layout(
        title="GHI et production PV - profil journalier typique",
        xaxis_title="Heure",
        yaxis=dict(title=f"GHI ({ghi_unit or 'W/m2'})"),
        yaxis2=dict(title="Production PV (MWh/h)", overlaying="y", side="right"),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
    )
    return fig


def _plot_temperature_histogram(
    df: pd.DataFrame,
    *,
    value_col: str,
    unit_label: str,
) -> go.Figure:
    if df is None or df.empty or value_col not in df.columns:
        return go.Figure()
    work = df[[value_col]].copy()
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=[value_col])
    if work.empty:
        return go.Figure()

    fig = px.histogram(
        work,
        x=value_col,
        nbins=40,
        title="Histogramme de temperature",
        labels={value_col: f"Temperature ({unit_label or 'degC'})", "count": "Occurrences"},
    )
    fig.update_layout(height=360, bargap=0.05)
    return fig


with section("SECTION_INPUTS"):
    _title_with_help("BESS_SIZING_INPUT_GUIDE_TITLE", "BESS_SIZING_HELP_INPUTS", level=4)
    st.markdown(t("BESS_SIZING_INPUT_GUIDE_BODY"))

    pv_file = st.file_uploader(
        t("BESS_SIZING_UPLOAD_PV"),
        type=["csv", "txt"],
        accept_multiple_files=False,
    )
    tmy_file = st.file_uploader(
        t("BESS_SIZING_UPLOAD_TMY"),
        type=["csv", "txt"],
        accept_multiple_files=False,
    )

    market_source_mode = st.radio(
        t("BESS_SIZING_MARKET_SOURCE"),
        options=["api", "csv"],
        index=0 if get(TOOL_ID, "market_source_mode", "api") == "api" else 1,
        format_func=lambda x: t("BESS_SIZING_MARKET_SOURCE_API") if x == "api" else t("BESS_SIZING_MARKET_SOURCE_CSV"),
        horizontal=True,
    )
    set_(TOOL_ID, "market_source_mode", market_source_mode)

    market_file = None
    if market_source_mode == "api":
        c_bzn, c_year = st.columns(2)
        with c_bzn:
            bzn_labels = list(BZN_OPTIONS.keys())
            current_bzn = get(TOOL_ID, "market_bzn", "FR")
            default_label = next((k for k, v in BZN_OPTIONS.items() if v == current_bzn), bzn_labels[0])
            selected_label = st.selectbox(
                t("BESS_SIZING_MARKET_BZN"),
                options=bzn_labels,
                index=bzn_labels.index(default_label),
            )
            set_(TOOL_ID, "market_bzn", BZN_OPTIONS[selected_label])
        with c_year:
            year_val = st.number_input(
                t("BESS_SIZING_MARKET_YEAR"),
                min_value=2015,
                max_value=2100,
                value=int(get(TOOL_ID, "market_year", 2025)),
                step=1,
            )
            set_(TOOL_ID, "market_year", int(year_val))
    else:
        market_file = st.file_uploader(
            t("BESS_SIZING_UPLOAD_MARKET"),
            type=["csv", "txt"],
            accept_multiple_files=False,
        )

    pv_parsed = _parse_uploaded_pv(pv_file)
    tmy_parsed = _parse_uploaded_tmy(tmy_file)
    market_parsed = _parse_uploaded_market(market_file) if market_file else None

    if pv_parsed is not None:
        st.caption(
            f"PV: format={pv_parsed.source_format}, rows={len(pv_parsed.dataframe)}, columns={len(pv_parsed.dataframe.columns)}"
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            options = pv_parsed.timestamp_candidates or list(pv_parsed.dataframe.columns)
            current = _resolve_default_state_value(
                options,
                get(TOOL_ID, "pv_timestamp_col", ""),
                pv_parsed.default_timestamp_col or "",
            )
            selected = _safe_selectbox(
                t("BESS_SIZING_COL_TIMESTAMP_PV"),
                options,
                current,
            )
            set_(TOOL_ID, "pv_timestamp_col", selected)

        with c2:
            options = pv_parsed.value_candidates or [c for c in pv_parsed.dataframe.columns if c != get(TOOL_ID, "pv_timestamp_col", "")]
            pv_fallback = _prefer_pv_energy_col_egrid(
                options,
                pv_parsed.default_value_col or "",
            )
            current = _resolve_default_state_value(
                options,
                get(TOOL_ID, "pv_value_col", ""),
                pv_fallback,
            )
            selected = _safe_selectbox(
                t("BESS_SIZING_COL_VALUE_PV"),
                options,
                current,
            )
            set_(TOOL_ID, "pv_value_col", selected)

        with c3:
            detected_unit = detect_pv_unit_from_metadata(
                get(TOOL_ID, "pv_value_col", ""),
                pv_parsed.units_map,
            )
            unit_default = get(TOOL_ID, "pv_unit", "auto")
            unit_selected = _safe_selectbox(
                t("BESS_SIZING_UNIT_PV"),
                PV_UNIT_OPTIONS,
                unit_default if unit_default in PV_UNIT_OPTIONS else "auto",
            )
            set_(TOOL_ID, "pv_unit", unit_selected)
            st.caption(f"{t('BESS_SIZING_DETECTED_UNIT')}: {detected_unit}")

    if tmy_parsed is not None:
        st.caption(
            f"TMY: format={tmy_parsed.source_format}, rows={len(tmy_parsed.dataframe)}, columns={len(tmy_parsed.dataframe.columns)}"
        )

        c1, c2 = st.columns(2)
        with c1:
            options = tmy_parsed.timestamp_candidates or list(tmy_parsed.dataframe.columns)
            current = _resolve_default_state_value(
                options,
                get(TOOL_ID, "tmy_timestamp_col", ""),
                tmy_parsed.default_timestamp_col or "",
            )
            selected = _safe_selectbox(
                t("BESS_SIZING_COL_TIMESTAMP_TMY"),
                options,
                current,
            )
            set_(TOOL_ID, "tmy_timestamp_col", selected)
        with c2:
            options = tmy_parsed.value_candidates or [c for c in tmy_parsed.dataframe.columns if c != get(TOOL_ID, "tmy_timestamp_col", "")]
            current = _resolve_default_state_value(
                options,
                get(TOOL_ID, "tmy_value_col", ""),
                tmy_parsed.default_value_col or "",
            )
            selected = _safe_selectbox(
                t("BESS_SIZING_COL_VALUE_TMY"),
                options,
                current,
            )
            set_(TOOL_ID, "tmy_value_col", selected)

    if market_parsed is not None and market_source_mode == "csv":
        st.caption(
            f"Market CSV: format={market_parsed.source_format}, rows={len(market_parsed.dataframe)}, columns={len(market_parsed.dataframe.columns)}"
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            options = market_parsed.timestamp_candidates or list(market_parsed.dataframe.columns)
            current = _resolve_default_state_value(
                options,
                get(TOOL_ID, "market_timestamp_col", ""),
                market_parsed.default_timestamp_col or "",
            )
            selected = _safe_selectbox(
                t("BESS_SIZING_COL_TIMESTAMP_MARKET"),
                options,
                current,
            )
            set_(TOOL_ID, "market_timestamp_col", selected)
        with c2:
            options = market_parsed.value_candidates or [c for c in market_parsed.dataframe.columns if c != get(TOOL_ID, "market_timestamp_col", "")]
            current = _resolve_default_state_value(
                options,
                get(TOOL_ID, "market_value_col", ""),
                market_parsed.default_value_col or "",
            )
            selected = _safe_selectbox(
                t("BESS_SIZING_COL_VALUE_MARKET"),
                options,
                current,
            )
            set_(TOOL_ID, "market_value_col", selected)
        with c3:
            detected_unit = detect_price_unit_from_metadata(get(TOOL_ID, "market_value_col", ""))
            unit_default = get(TOOL_ID, "market_price_unit", "auto")
            selected = _safe_selectbox(
                t("BESS_SIZING_UNIT_MARKET"),
                PRICE_UNIT_OPTIONS,
                unit_default if unit_default in PRICE_UNIT_OPTIONS else "auto",
            )
            set_(TOOL_ID, "market_price_unit", selected)
            st.caption(f"{t('BESS_SIZING_DETECTED_UNIT')}: {detected_unit}")

    _title_with_help("BESS_SIZING_SIZING_PARAMS_TITLE", "BESS_SIZING_HELP_PARAMS", level=4)
    st.info(t("BESS_SIZING_ANALYSIS_STRATEGY_INFO"))
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**Contraintes d'exploitation**")
        allow_grid_charging = st.checkbox(
            t("BESS_SIZING_ALLOW_GRID_CHARGING"),
            value=bool(get(TOOL_ID, "allow_grid_charging", False)),
            help=t("BESS_SIZING_HELP_ALLOW_GRID_CHARGING"),
        )
        set_(TOOL_ID, "allow_grid_charging", bool(allow_grid_charging))

        use_grid_limit = st.checkbox(
            t("BESS_SIZING_USE_GRID_LIMIT"),
            value=bool(get(TOOL_ID, "use_grid_injection_limit", False)),
            help=t("BESS_SIZING_HELP_GRID_LIMIT"),
        )
        set_(TOOL_ID, "use_grid_injection_limit", bool(use_grid_limit))

        grid_limit_val = st.number_input(
            t("BESS_SIZING_GRID_LIMIT_VALUE"),
            min_value=0.1,
            value=float(get(TOOL_ID, "grid_injection_limit_mw", 10.0)),
            step=0.5,
            disabled=not bool(use_grid_limit),
        )
        set_(TOOL_ID, "grid_injection_limit_mw", float(grid_limit_val))

    with col_right:
        st.markdown("**Puissance crête du projet (MWc)**")
        pv_peak_power_mw = st.number_input(
            "Ppv (MWc)",
            min_value=0.1,
            value=float(get(TOOL_ID, "pv_peak_power_mw", 50.0)),
            step=0.5,
            help="Input principal de dimensionnement. La matrice BESS est deduite automatiquement.",
        )
        set_(TOOL_ID, "pv_peak_power_mw", float(pv_peak_power_mw))

    auto_powers = _build_power_grid_from_pv_peak(
        pv_peak_power_mw=float(pv_peak_power_mw),
        power_ratios=DEFAULT_SCENARIO_POWER_RATIOS,
    )
    auto_durations = [float(d) for d in DEFAULT_SCENARIO_DURATIONS_H]
    n_scenarios = len(auto_powers) * len(auto_durations)
    st.caption(
        "Matrice scenarios auto: ratios P_BESS/P_PV = "
        + ", ".join(f"{r:.2f}" for r in DEFAULT_SCENARIO_POWER_RATIOS)
        + f" | durees = {int(min(auto_durations))}h a {int(max(auto_durations))}h (pas 1h)"
        + f" | total = {n_scenarios} scenarios"
    )

    cre_power_mw = float(pv_peak_power_mw) * CRE_REFERENCE_POWER_RATIO
    cre_energy_mwh = cre_power_mw * CRE_REFERENCE_DURATION_H
    st.markdown("**Scénario de référence CRE**")
    c_cre1, c_cre2, c_cre3 = st.columns(3)
    c_cre1.metric("Ratio P_BESS/P_PV", f"{CRE_REFERENCE_POWER_RATIO:.2f}x")
    c_cre2.metric("Puissance BESS ref", f"{_fmt(cre_power_mw, 2)} MW")
    c_cre3.metric("Durée ref", f"{_fmt(CRE_REFERENCE_DURATION_H, 0)} h")
    st.info(
        f"Référence CRE appliquée automatiquement: P_BESS = {CRE_REFERENCE_POWER_RATIO:.2f} x P_PV, "
        f"durée = {CRE_REFERENCE_DURATION_H:.0f} h, soit E_BESS = {_fmt(cre_energy_mwh, 2)} MWh."
    )

    set_(TOOL_ID, "optimization_goal", "techno_economic")
    ignore_capex_opex = st.checkbox(
        "Mode brut: ignorer CAPEX/OPEX",
        value=bool(get(TOOL_ID, "ignore_capex_opex", False)),
        help="Si active, les parametres CAPEX/OPEX ne sont pas pris en compte dans les KPI economiques.",
    )
    set_(TOOL_ID, "ignore_capex_opex", bool(ignore_capex_opex))
    if ignore_capex_opex:
        st.caption("Mode brut actif: CAPEX/OPEX ignores (les gains sont evalues sans ces depenses).")

    with st.expander("Hypotheses avancees", expanded=False):
        st.caption("Parametres experts: technique, solveur, degradation et economie detaillee.")
        c10, c11, c12 = st.columns(3)
        with c10:
            soc_min = st.number_input(
                t("BESS_SIZING_SOC_MIN"),
                min_value=0.0,
                max_value=1.0,
                value=float(get(TOOL_ID, "soc_min", 0.15)),
                step=0.01,
            )
            set_(TOOL_ID, "soc_min", float(soc_min))
        with c11:
            soc_max = st.number_input(
                t("BESS_SIZING_SOC_MAX"),
                min_value=0.0,
                max_value=1.0,
                value=float(get(TOOL_ID, "soc_max", 0.95)),
                step=0.01,
            )
            set_(TOOL_ID, "soc_max", float(soc_max))
        with c12:
            soc_initial = st.number_input(
                t("BESS_SIZING_SOC_INITIAL"),
                min_value=0.0,
                max_value=1.0,
                value=float(get(TOOL_ID, "soc_initial", 0.50)),
                step=0.01,
            )
            set_(TOOL_ID, "soc_initial", float(soc_initial))

        c13, c14, c15 = st.columns(3)
        with c13:
            rt_eff = st.number_input(
                t("BESS_SIZING_ROUNDTRIP"),
                min_value=0.01,
                max_value=1.0,
                value=float(get(TOOL_ID, "roundtrip_efficiency", 0.85)),
                step=0.01,
            )
            set_(TOOL_ID, "roundtrip_efficiency", float(rt_eff))
        with c14:
            enforce_terminal = st.checkbox(
                t("BESS_SIZING_ENFORCE_TERMINAL_SOC"),
                value=bool(get(TOOL_ID, "enforce_terminal_soc", True)),
            )
            set_(TOOL_ID, "enforce_terminal_soc", bool(enforce_terminal))
        with c15:
            solver_mode = st.radio(
                t("BESS_SIZING_SOLVER_MODE"),
                options=["auto", "heuristic"],
                index=0 if get(TOOL_ID, "solver_mode", "auto") == "auto" else 1,
                format_func=lambda x: t("BESS_SIZING_SOLVER_AUTO") if x == "auto" else t("BESS_SIZING_SOLVER_HEURISTIC"),
                horizontal=True,
                help=t("BESS_SIZING_SOLVER_MODE_HELP"),
            )
            set_(TOOL_ID, "solver_mode", solver_mode)

        c16, c17 = st.columns(2)
        with c16:
            degrad_cost = st.number_input(
                t("BESS_SIZING_DEGRAD_COST"),
                min_value=0.0,
                value=float(get(TOOL_ID, "degradation_cost_eur_per_mwh", 0.0)),
                step=0.1,
            )
            set_(TOOL_ID, "degradation_cost_eur_per_mwh", float(degrad_cost))
        with c17:
            aux_losses = st.number_input(
                t("BESS_SIZING_AUX_LOSSES"),
                min_value=0.0,
                value=float(get(TOOL_ID, "auxiliary_losses_mwh_per_h", 0.0)),
                step=0.01,
            )
            set_(TOOL_ID, "auxiliary_losses_mwh_per_h", float(aux_losses))

        st.markdown("**Economique detaillee (avancee)**")
        c18, c19, c20 = st.columns(3)
        with c18:
            capex_p = st.number_input(
                t("BESS_SIZING_CAPEX_POWER"),
                min_value=0.0,
                value=float(get(TOOL_ID, "capex_power_eur_per_kw", DEFAULT_ECON.capex_power_eur_per_kw)),
                step=5.0,
                key="adv_capex_power",
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "capex_power_eur_per_kw", float(capex_p))
            capex_e = st.number_input(
                t("BESS_SIZING_CAPEX_ENERGY"),
                min_value=0.0,
                value=float(get(TOOL_ID, "capex_energy_eur_per_kwh", DEFAULT_ECON.capex_energy_eur_per_kwh)),
                step=5.0,
                key="adv_capex_energy",
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "capex_energy_eur_per_kwh", float(capex_e))
            capex_fix = st.number_input(
                t("BESS_SIZING_CAPEX_FIXED"),
                min_value=0.0,
                value=float(get(TOOL_ID, "capex_fixed_eur", DEFAULT_ECON.capex_fixed_eur)),
                step=1000.0,
                key="adv_capex_fixed",
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "capex_fixed_eur", float(capex_fix))
        with c19:
            opex_pct = st.number_input(
                t("BESS_SIZING_OPEX_FIXED_PCT"),
                min_value=0.0,
                max_value=1.0,
                value=float(get(TOOL_ID, "opex_fixed_pct_capex", DEFAULT_ECON.opex_fixed_pct_capex)),
                step=0.001,
                key="adv_opex_pct",
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "opex_fixed_pct_capex", float(opex_pct))
            opex_fix = st.number_input(
                t("BESS_SIZING_OPEX_FIXED"),
                min_value=0.0,
                value=float(get(TOOL_ID, "opex_fixed_eur_per_year", DEFAULT_ECON.opex_fixed_eur_per_year)),
                step=1000.0,
                key="adv_opex_fixed",
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "opex_fixed_eur_per_year", float(opex_fix))
            opex_var = st.number_input(
                t("BESS_SIZING_OPEX_VARIABLE"),
                min_value=0.0,
                value=float(
                    get(
                        TOOL_ID,
                        "opex_variable_eur_per_mwh_throughput",
                        DEFAULT_ECON.opex_variable_eur_per_mwh_throughput,
                    )
                ),
                step=0.1,
                key="adv_opex_var",
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "opex_variable_eur_per_mwh_throughput", float(opex_var))
        with c20:
            proj_life = st.number_input(
                t("BESS_SIZING_PROJECT_LIFE"),
                min_value=1,
                max_value=40,
                value=int(get(TOOL_ID, "project_life_years", DEFAULT_ECON.project_life_years)),
                step=1,
                key="adv_project_life",
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "project_life_years", int(proj_life))
            disc = st.number_input(
                t("BESS_SIZING_DISCOUNT_RATE"),
                min_value=0.0,
                max_value=1.0,
                value=float(get(TOOL_ID, "discount_rate", DEFAULT_ECON.discount_rate)),
                step=0.005,
                key="adv_discount",
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "discount_rate", float(disc))

        c21, c22 = st.columns(2)
        with c21:
            repl_enabled = st.checkbox(
                t("BESS_SIZING_REPLACEMENT_ENABLED"),
                value=bool(get(TOOL_ID, "replacement_year_enabled", False)),
                disabled=bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "replacement_year_enabled", bool(repl_enabled))
        with c22:
            repl_year = st.number_input(
                t("BESS_SIZING_REPLACEMENT_YEAR"),
                min_value=1,
                max_value=40,
                value=int(get(TOOL_ID, "replacement_year", 8)),
                step=1,
                disabled=(not repl_enabled) or bool(ignore_capex_opex),
            )
            set_(TOOL_ID, "replacement_year", int(repl_year))
        repl_frac = st.number_input(
            t("BESS_SIZING_REPLACEMENT_FRACTION"),
            min_value=0.0,
            max_value=1.0,
            value=float(get(TOOL_ID, "replacement_fraction_capex", 0.0)),
            step=0.05,
            disabled=(not repl_enabled) or bool(ignore_capex_opex),
        )
        set_(TOOL_ID, "replacement_fraction_capex", float(repl_frac))

    # Values used by runtime section even if advanced expander stays collapsed.
    soc_min = float(get(TOOL_ID, "soc_min", 0.15))
    soc_max = float(get(TOOL_ID, "soc_max", 0.95))
    soc_initial = float(get(TOOL_ID, "soc_initial", 0.50))
    rt_eff = float(get(TOOL_ID, "roundtrip_efficiency", 0.85))
    enforce_terminal = bool(get(TOOL_ID, "enforce_terminal_soc", True))
    solver_mode = str(get(TOOL_ID, "solver_mode", "auto"))
    degrad_cost = float(get(TOOL_ID, "degradation_cost_eur_per_mwh", 0.0))
    aux_losses = float(get(TOOL_ID, "auxiliary_losses_mwh_per_h", 0.0))


with section("SECTION_RUN"):
    _title_with_help("BESS_SIZING_RUN_SECTION_TITLE", "BESS_SIZING_HELP_RUN", level=4)
    st.markdown('<div class="pv-run">', unsafe_allow_html=True)
    run_btn = st.button(t("BESS_SIZING_RUN_BUTTON"), type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if run_btn:
        try:
            if pv_file is None:
                raise ValueError(t("BESS_SIZING_ERROR_NEED_PV"))
            if market_source_mode == "csv" and market_file is None:
                raise ValueError(t("BESS_SIZING_ERROR_NEED_MARKET_CSV"))
            if float(pv_peak_power_mw) <= 0:
                raise ValueError("La puissance crete PV (Ppv) doit etre strictement positive.")
            if not (0 <= soc_min < soc_max <= 1):
                raise ValueError(t("BESS_SIZING_ERROR_SOC_BOUNDS"))
            if not (soc_min <= soc_initial <= soc_max):
                raise ValueError(t("BESS_SIZING_ERROR_SOC_INITIAL"))

            with st.spinner(t("BESS_SIZING_RUNNING")):
                pv_parsed = load_pv_input_table(pv_file.getvalue())
                tmy_parsed = load_tmy_input_table(tmy_file.getvalue()) if tmy_file is not None else None
                tmy_ts_col: str | None = None
                tmy_val_col: str | None = None
                mk_ts_col: str | None = None
                mk_val_col: str | None = None

                pv_ts_col = get(TOOL_ID, "pv_timestamp_col", pv_parsed.default_timestamp_col or "")
                pv_val_col = get(TOOL_ID, "pv_value_col", pv_parsed.default_value_col or "")
                pv_unit = get(TOOL_ID, "pv_unit", "auto")
                if pv_unit == "auto":
                    pv_unit = detect_pv_unit_from_metadata(pv_val_col, pv_parsed.units_map)

                pv_hourly, pv_meta, pv_warnings = prepare_pv_hourly_series(
                    dataframe=pv_parsed.dataframe,
                    timestamp_col=pv_ts_col,
                    value_col=pv_val_col,
                    value_unit=pv_unit,
                )

                tmy_warnings: List[str] = []
                if tmy_parsed is not None:
                    tmy_ts_col = str(get(TOOL_ID, "tmy_timestamp_col", tmy_parsed.default_timestamp_col or ""))
                    tmy_val_col = str(get(TOOL_ID, "tmy_value_col", tmy_parsed.default_value_col or ""))
                    tmy_hourly, tmy_meta, tmy_warnings = prepare_tmy_hourly_series(
                        dataframe=tmy_parsed.dataframe,
                        timestamp_col=tmy_ts_col,
                        value_col=tmy_val_col,
                    )
                else:
                    tmy_hourly = pd.DataFrame(columns=["timestamp", "tmy_signal", "month", "day", "hour"])
                    tmy_meta = {"available": False}
                    tmy_warnings.append("TMY file not provided; coherence metrics are informative only in this run.")

                market_warnings: List[str] = []
                if market_source_mode == "api":
                    market_hourly, market_meta, market_api_warnings = fetch_market_prices_hourly_from_api(
                        bzn=str(get(TOOL_ID, "market_bzn", "FR")),
                        year=int(get(TOOL_ID, "market_year", 2025)),
                        local_tz="Europe/Paris",
                    )
                    market_warnings.extend(market_api_warnings)
                else:
                    market_parsed = load_market_input_table(market_file.getvalue())
                    mk_ts_col = str(get(TOOL_ID, "market_timestamp_col", market_parsed.default_timestamp_col or ""))
                    mk_val_col = str(get(TOOL_ID, "market_value_col", market_parsed.default_value_col or ""))
                    mk_unit = get(TOOL_ID, "market_price_unit", "auto")
                    if mk_unit == "auto":
                        mk_unit = detect_price_unit_from_metadata(mk_val_col)

                    market_hourly, market_meta, market_csv_warnings = prepare_market_hourly_series(
                        dataframe=market_parsed.dataframe,
                        timestamp_col=mk_ts_col,
                        value_col=mk_val_col,
                        value_unit=mk_unit,
                    )
                    market_warnings.extend(market_csv_warnings)

                aligned_df, align_meta, align_warnings = align_market_prices_to_pv_profile(
                    pv_hourly=pv_hourly,
                    market_hourly=market_hourly,
                )
                coherence = compute_tmy_coherence(
                    pv_hourly=pv_hourly,
                    tmy_hourly=tmy_hourly,
                )

                eta_each = float(rt_eff) ** 0.5
                powers = _build_power_grid_from_pv_peak(
                    pv_peak_power_mw=float(pv_peak_power_mw),
                    power_ratios=DEFAULT_SCENARIO_POWER_RATIOS,
                )
                durations_selected = [float(d) for d in DEFAULT_SCENARIO_DURATIONS_H]
                optimization_goal = str(get(TOOL_ID, "optimization_goal", "techno_economic"))
                ignore_capex_opex = bool(get(TOOL_ID, "ignore_capex_opex", False))
                mode_selected = (
                    "mode_a_custom_costs"
                    if optimization_goal == "techno_economic"
                    else "mode_c_marginal"
                )

                technical_inputs = BessTechnicalInputs(
                    soc_min=float(soc_min),
                    soc_max=float(soc_max),
                    soc_initial=float(soc_initial),
                    eta_charge=eta_each,
                    eta_discharge=eta_each,
                    enforce_terminal_soc=bool(enforce_terminal),
                    allow_grid_charging=bool(get(TOOL_ID, "allow_grid_charging", False)),
                    pv_only_charging=not bool(get(TOOL_ID, "allow_grid_charging", False)),
                    grid_injection_limit_mw=(
                        float(get(TOOL_ID, "grid_injection_limit_mw", 10.0))
                        if bool(get(TOOL_ID, "use_grid_injection_limit", False))
                        else None
                    ),
                    degradation_cost_eur_per_mwh_throughput=float(
                        get(TOOL_ID, "degradation_cost_eur_per_mwh", 0.0)
                    ),
                    auxiliary_losses_mwh_per_h=float(
                        get(TOOL_ID, "auxiliary_losses_mwh_per_h", 0.0)
                    ),
                    time_step_hours=1.0,
                )
                marginal_inputs = MarginalAnalysisInputs()
                replacement_enabled = bool(get(TOOL_ID, "replacement_year_enabled", False))
                if ignore_capex_opex:
                    economic_inputs = BessEconomicInputs(
                        capex_power_eur_per_kw=0.0,
                        capex_energy_eur_per_kwh=0.0,
                        capex_fixed_eur=0.0,
                        opex_fixed_pct_capex=0.0,
                        opex_fixed_eur_per_year=0.0,
                        opex_variable_eur_per_mwh_throughput=0.0,
                        project_life_years=int(get(TOOL_ID, "project_life_years", DEFAULT_ECON.project_life_years)),
                        discount_rate=float(get(TOOL_ID, "discount_rate", DEFAULT_ECON.discount_rate)),
                        replacement_year=None,
                        replacement_fraction_capex=0.0,
                    )
                    replacement_enabled = False
                else:
                    economic_inputs = BessEconomicInputs(
                        capex_power_eur_per_kw=float(get(TOOL_ID, "capex_power_eur_per_kw", DEFAULT_ECON.capex_power_eur_per_kw)),
                        capex_energy_eur_per_kwh=float(get(TOOL_ID, "capex_energy_eur_per_kwh", DEFAULT_ECON.capex_energy_eur_per_kwh)),
                        capex_fixed_eur=float(get(TOOL_ID, "capex_fixed_eur", DEFAULT_ECON.capex_fixed_eur)),
                        opex_fixed_pct_capex=float(get(TOOL_ID, "opex_fixed_pct_capex", DEFAULT_ECON.opex_fixed_pct_capex)),
                        opex_fixed_eur_per_year=float(get(TOOL_ID, "opex_fixed_eur_per_year", DEFAULT_ECON.opex_fixed_eur_per_year)),
                        opex_variable_eur_per_mwh_throughput=float(
                            get(TOOL_ID, "opex_variable_eur_per_mwh_throughput", DEFAULT_ECON.opex_variable_eur_per_mwh_throughput)
                        ),
                        project_life_years=int(get(TOOL_ID, "project_life_years", DEFAULT_ECON.project_life_years)),
                        discount_rate=float(get(TOOL_ID, "discount_rate", DEFAULT_ECON.discount_rate)),
                        replacement_year=int(get(TOOL_ID, "replacement_year", 8)) if replacement_enabled else None,
                        replacement_fraction_capex=float(get(TOOL_ID, "replacement_fraction_capex", 0.0)) if replacement_enabled else 0.0,
                    )
                economic_overlap_warnings: List[str] = []
                if (
                    float(economic_inputs.opex_variable_eur_per_mwh_throughput) > 0
                    and float(technical_inputs.degradation_cost_eur_per_mwh_throughput) > 0
                ):
                    economic_overlap_warnings.append(
                        "OPEX variable throughput et cout de degradation variable sont tous deux actifs: verifier l'absence de double comptage."
                    )
                if replacement_enabled and float(economic_inputs.opex_variable_eur_per_mwh_throughput) > 0:
                    economic_overlap_warnings.append(
                        "Remplacement simplifie et OPEX variable actifs simultanement: verifier la coherence economique."
                    )
                if ignore_capex_opex:
                    economic_overlap_warnings.append(
                        "Mode brut actif: CAPEX/OPEX ignores dans les KPI economiques."
                    )

                recommendation_metric = (
                    "gain_annual_abs_eur"
                    if ignore_capex_opex
                    else "annual_net_margin_eur"
                )

                result = run_bess_sizing_v2(
                    aligned_hourly_df=aligned_df,
                    powers_mw=powers,
                    durations_h=[float(x) for x in durations_selected],
                    technical_inputs=technical_inputs,
                    analysis_mode=mode_selected,
                    marginal_inputs=marginal_inputs,
                    economic_inputs=economic_inputs,
                    recommendation_metric=recommendation_metric,
                    prefer_lp=(solver_mode == "auto"),
                    tmy_coherence=coherence,
                )
                result.summary_df = _attach_scenario_context(
                    result.summary_df,
                    pv_peak_power_mw=float(pv_peak_power_mw),
                )

                extra_warnings = (
                    pv_parsed.warnings
                    + (tmy_parsed.warnings if tmy_parsed is not None else [])
                    + pv_warnings
                    + tmy_warnings
                    + market_warnings
                    + align_warnings
                )
                result.warnings = list(
                    dict.fromkeys(result.warnings + extra_warnings + economic_overlap_warnings)
                )

                result.assumptions["preparation_meta"] = {
                    "pv": pv_meta,
                    "tmy": tmy_meta,
                    "market": market_meta,
                    "alignment": align_meta,
                }
                result.assumptions["optimization_goal"] = optimization_goal
                result.assumptions["ignore_capex_opex"] = bool(ignore_capex_opex)
                result.assumptions["pv_peak_power_mw"] = float(pv_peak_power_mw)
                result.assumptions["scenario_power_ratios"] = [float(r) for r in DEFAULT_SCENARIO_POWER_RATIOS]
                result.assumptions["scenario_durations_h"] = [float(d) for d in DEFAULT_SCENARIO_DURATIONS_H]
                result.assumptions["cre_reference"] = {
                    "power_ratio": CRE_REFERENCE_POWER_RATIO,
                    "duration_h": CRE_REFERENCE_DURATION_H,
                }

                set_(TOOL_ID, "last_result", result)
                set_(
                    TOOL_ID,
                    "last_prepared_data",
                    {
                        "pv_hourly": pv_hourly.copy(),
                        "tmy_hourly": tmy_hourly.copy() if tmy_hourly is not None else pd.DataFrame(),
                        "market_hourly": market_hourly.copy(),
                        "aligned_df": aligned_df.copy(),
                        "pv_raw_df": pv_parsed.dataframe.copy(),
                        "tmy_raw_df": tmy_parsed.dataframe.copy() if tmy_parsed is not None else pd.DataFrame(),
                        "market_raw_df": (
                            market_parsed.dataframe.copy()
                            if market_source_mode == "csv" and market_parsed is not None
                            else market_hourly.copy()
                        ),
                        "pv_meta": dict(pv_meta or {}),
                        "tmy_meta": dict(tmy_meta or {}),
                        "market_meta": dict(market_meta or {}),
                        "align_meta": dict(align_meta or {}),
                        "pv_units_map": dict(pv_parsed.units_map or {}),
                        "tmy_units_map": dict(tmy_parsed.units_map or {}) if tmy_parsed is not None else {},
                        "pv_timestamp_col": pv_ts_col,
                        "pv_value_col": pv_val_col,
                        "tmy_timestamp_col": tmy_ts_col,
                        "tmy_value_col": tmy_val_col,
                        "market_timestamp_col": mk_ts_col,
                        "market_value_col": mk_val_col,
                    },
                )
                primary_key = _primary_recommendation_key(
                    optimization_goal,
                    bool(result.recommendations.get("techno") and result.recommendations["techno"].config_id),
                )
                selected_default = (
                    (result.recommendations.get(primary_key).config_id if primary_key else None)
                    or (result.recommendations.get("techno").config_id if result.recommendations.get("techno") else None)
                    or (result.recommendations.get("marginal").config_id if result.recommendations.get("marginal") else None)
                    or (result.recommendations.get("brut_max").config_id if result.recommendations.get("brut_max") else None)
                    or ""
                )
                set_(TOOL_ID, "selected_config_id", selected_default)
                st.success(t("BESS_SIZING_DONE"))
        except Exception as exc:
            st.error(str(exc))


with section("SECTION_RESULTS"):
    result_obj: BessSweepV2Result | None = get(TOOL_ID, "last_result", None)
    prepared_data = get(TOOL_ID, "last_prepared_data", None) or {}
    if result_obj is None:
        st.info(t("BESS_SIZING_NO_RESULTS"))
    else:
        pv_peak_power_mw_result = float(
            result_obj.assumptions.get(
                "pv_peak_power_mw",
                get(TOOL_ID, "pv_peak_power_mw", 50.0),
            )
        )
        summary_df = _attach_scenario_context(
            result_obj.summary_df.copy(),
            pv_peak_power_mw=pv_peak_power_mw_result,
        )
        summary_display_df = _summary_display_table(summary_df)
        best_row = summary_df.sort_values("gain_annual_abs_eur", ascending=False).iloc[0]

        pv_hourly = prepared_data.get("pv_hourly", pd.DataFrame())
        market_hourly = prepared_data.get("market_hourly", pd.DataFrame())
        aligned_df = prepared_data.get("aligned_df", pd.DataFrame())
        tmy_hourly = prepared_data.get("tmy_hourly", pd.DataFrame())
        pv_raw_df = prepared_data.get("pv_raw_df", pd.DataFrame())
        tmy_raw_df = prepared_data.get("tmy_raw_df", pd.DataFrame())
        pv_units_map = prepared_data.get("pv_units_map", {}) if isinstance(prepared_data.get("pv_units_map", {}), dict) else {}
        tmy_units_map = prepared_data.get("tmy_units_map", {}) if isinstance(prepared_data.get("tmy_units_map", {}), dict) else {}

        config_ids = summary_df["config_id"].astype(str).tolist()
        config_labels = {
            str(r["config_id"]): str(r.get("config_label", _friendly_config_label(
                float(r["power_mw"]),
                float(r["duration_h"]),
                float(r["energy_nominal_mwh"]),
                power_ratio_pv=(
                    float(r["power_ratio_pv"])
                    if "power_ratio_pv" in r and pd.notna(r["power_ratio_pv"])
                    else None
                ),
                is_cre_reference=(
                    bool(int(r["is_cre_reference"]))
                    if "is_cre_reference" in r and pd.notna(r["is_cre_reference"])
                    else False
                ),
            )))
            for _, r in summary_df.iterrows()
        }

        current_selected = get(TOOL_ID, "selected_config_id", "")
        if current_selected not in config_ids:
            current_selected = config_ids[0]

        reco_brut = result_obj.recommendations.get("brut_max")
        reco_tech = result_obj.recommendations.get("techno")
        reco_marginal = result_obj.recommendations.get("marginal")

        def _reco_label(config_id: str | None) -> str:
            if not config_id:
                return "n/a"
            return config_labels.get(config_id, config_id)

        key_config_ids = [
            cid
            for cid in [
                reco_brut.config_id if reco_brut else None,
                reco_tech.config_id if reco_tech else None,
                reco_marginal.config_id if reco_marginal else None,
                _find_cre_config_id(summary_df),
            ]
            if cid
        ]
        key_config_ids = list(dict.fromkeys(key_config_ids))

        optimization_goal = str(
            result_obj.assumptions.get(
                "optimization_goal",
                get(TOOL_ID, "optimization_goal", "techno_economic"),
            )
        )
        goal_labels = _goal_options()
        techno_viable = bool(
            reco_tech
            and reco_tech.config_id
            and reco_tech.config_id in set(summary_df["config_id"])
        )
        primary_key = _primary_recommendation_key(optimization_goal, techno_viable)
        primary_reco = result_obj.recommendations.get(primary_key) if primary_key else None
        primary_config_id = (
            (primary_reco.config_id if primary_reco else None)
            or (reco_brut.config_id if reco_brut else None)
            or config_ids[0]
        )
        primary_row = summary_df.loc[summary_df["config_id"] == primary_config_id].iloc[0]
        primary_dispatch = result_obj.dispatch_by_config.get(primary_config_id, pd.DataFrame())

        techno_config_id = (
            reco_tech.config_id
            if (
                reco_tech
                and reco_tech.config_id
                and reco_tech.config_id in set(summary_df["config_id"].astype(str))
            )
            else primary_config_id
        )
        techno_row = summary_df.loc[summary_df["config_id"] == techno_config_id].iloc[0]
        techno_dispatch = result_obj.dispatch_by_config.get(techno_config_id, pd.DataFrame())

        cre_config_id = _find_cre_config_id(summary_df)
        cre_row = (
            summary_df.loc[summary_df["config_id"] == cre_config_id].iloc[0]
            if cre_config_id and cre_config_id in set(summary_df["config_id"].astype(str))
            else None
        )
        cre_dispatch = (
            result_obj.dispatch_by_config.get(cre_config_id, pd.DataFrame())
            if cre_config_id
            else pd.DataFrame()
        )

        if current_selected not in config_ids:
            current_selected = primary_config_id

        tabs = st.tabs(
            [
                "Résultats principaux",
                "PV+BESS",
                "PV",
                "Météo",
                "Analyse marché",
                "Résultats détaillés",
            ]
        )
        tab_main, tab_pvbess, tab_pv, tab_weather, tab_market, tab_detail = tabs

        with tab_main:
            if bool(result_obj.assumptions.get("ignore_capex_opex", False)):
                st.info("Mode brut actif: CAPEX/OPEX ignores pour la comparaison des scenarios.")
            if techno_viable:
                st.success("Verdict economique: au moins une configuration est rentable dans le domaine teste.")
            else:
                st.error("Verdict economique: aucune configuration rentable dans le domaine teste.")

            primary_label = _reco_label(primary_config_id)
            st.markdown(
                f"**Solution retenue ({goal_labels.get(optimization_goal, optimization_goal)}):** {primary_label}"
            )
            if primary_reco and primary_reco.reason:
                st.caption(primary_reco.reason)

            pv_total = float(pv_hourly["pv_mwh"].sum()) if isinstance(pv_hourly, pd.DataFrame) and not pv_hourly.empty else np.nan
            mean_price = float(aligned_df["price_eur_per_mwh"].mean()) if isinstance(aligned_df, pd.DataFrame) and not aligned_df.empty else np.nan

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gain brut max", f"{_fmt(best_row.get('gain_annual_abs_eur'), 0)} EUR")
            c2.metric("Marge nette", f"{_fmt(primary_row.get('annual_net_margin_eur'), 0)} EUR")
            c3.metric("Cycles equivalents", _fmt(primary_row.get("equivalent_cycles"), 1))
            c4.metric("Production PV", f"{_fmt(pv_total, 1)} MWh")

            c5, c6, c7 = st.columns(3)
            c5.metric("Prix moyen electricite", f"{_fmt(mean_price, 1)} EUR/MWh")
            c6.metric("Prix capte PV", f"{_fmt(primary_row.get('capture_price_pv_only_eur_per_mwh'), 1)} EUR/MWh")
            c7.metric("Prix capte PV+BESS", f"{_fmt(primary_row.get('capture_price_pv_bess_eur_per_mwh'), 1)} EUR/MWh")

            if isinstance(primary_dispatch, pd.DataFrame) and not primary_dispatch.empty:
                st.plotly_chart(
                    _plot_dispatch_heatmap(primary_dispatch),
                    width="stretch",
                    config=PLOT_CONFIG,
                    key="chart_main_dispatch_heatmap",
                )
            else:
                st.info("Aucune serie de dispatch disponible pour la configuration retenue.")

        with tab_pvbess:
            st.markdown("### Analyses completes de l'hybridation PV+BESS")
            st.caption(
                f"Dimensionnement centre sur Ppv={_fmt(pv_peak_power_mw_result, 2)} MW | "
                "ratios [0.25, 0.50, 0.75, 1.00] x Ppv | durees 1h a 8h."
            )

            selected_config = st.selectbox(
                t("BESS_SIZING_SELECT_CONFIG"),
                options=config_ids,
                index=config_ids.index(current_selected),
                format_func=lambda x: config_labels.get(x, x),
                key="tab_pvbess_config",
            )
            set_(TOOL_ID, "selected_config_id", selected_config)
            selected_row = summary_df.loc[summary_df["config_id"] == selected_config].iloc[0]
            selected_dispatch = result_obj.dispatch_by_config[selected_config]

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Gain brut", f"{_fmt(selected_row.get('gain_annual_abs_eur'), 0)} EUR")
            c2.metric("Marge nette", f"{_fmt(selected_row.get('annual_net_margin_eur'), 0)} EUR")
            c3.metric("Cycles", _fmt(selected_row.get("equivalent_cycles"), 1))
            c4.metric("CAPEX total BESS", f"{_fmt(selected_row.get('capex_total_eur'), 0)} EUR")
            c5.metric("OPEX BESS", f"{_fmt(selected_row.get('opex_total_annual_eur'), 0)} EUR/an")

            st.plotly_chart(
                _plot_comparison_bars(selected_row),
                width="stretch",
                config=PLOT_CONFIG,
                key="chart_pvbess_comparison_bars",
            )

            st.markdown("#### Comparaison explicite: optimum techno-economique vs scenario CRE")
            if cre_row is not None and cre_config_id:
                st.markdown(
                    f"Optimum techno-economique: **{_reco_label(techno_config_id)}**  |  "
                    f"Reference CRE: **{_reco_label(cre_config_id)}**"
                )
                delta_gain = float(techno_row.get("gain_annual_abs_eur", np.nan)) - float(
                    cre_row.get("gain_annual_abs_eur", np.nan)
                )
                delta_margin = float(techno_row.get("annual_net_margin_eur", np.nan)) - float(
                    cre_row.get("annual_net_margin_eur", np.nan)
                )
                delta_capture = float(techno_row.get("capture_price_pv_bess_eur_per_mwh", np.nan)) - float(
                    cre_row.get("capture_price_pv_bess_eur_per_mwh", np.nan)
                )
                delta_cycles = float(techno_row.get("equivalent_cycles", np.nan)) - float(
                    cre_row.get("equivalent_cycles", np.nan)
                )

                k1, k2, k3, k4 = st.columns(4)
                k1.metric(
                    "Gain brut annuel (optimum)",
                    f"{_fmt(techno_row.get('gain_annual_abs_eur'), 0)} EUR",
                    delta=f"{_fmt(delta_gain, 0)} EUR vs CRE",
                )
                k2.metric(
                    "Marge nette annuelle (optimum)",
                    f"{_fmt(techno_row.get('annual_net_margin_eur'), 0)} EUR",
                    delta=f"{_fmt(delta_margin, 0)} EUR vs CRE",
                )
                k3.metric(
                    "Prix capte PV+BESS (optimum)",
                    f"{_fmt(techno_row.get('capture_price_pv_bess_eur_per_mwh'), 1)} EUR/MWh",
                    delta=f"{_fmt(delta_capture, 1)} EUR/MWh vs CRE",
                )
                k4.metric(
                    "Cycles equivalents (optimum)",
                    _fmt(techno_row.get("equivalent_cycles"), 1),
                    delta=f"{_fmt(delta_cycles, 1)} vs CRE",
                )

                comparison_rows = []
                for scenario_name, row in [
                    ("Optimum techno-economique", techno_row),
                    ("Reference CRE (0.50x Ppv, 2h)", cre_row),
                ]:
                    comparison_rows.append(
                        {
                            "Scenario": scenario_name,
                            "Configuration": _friendly_config_label(
                                float(row["power_mw"]),
                                float(row["duration_h"]),
                                float(row["energy_nominal_mwh"]),
                                power_ratio_pv=(
                                    float(row["power_ratio_pv"])
                                    if "power_ratio_pv" in row and pd.notna(row["power_ratio_pv"])
                                    else None
                                ),
                                is_cre_reference=(
                                    bool(int(row["is_cre_reference"]))
                                    if "is_cre_reference" in row and pd.notna(row["is_cre_reference"])
                                    else False
                                ),
                            ),
                            "Gain brut annuel (EUR)": _fmt(row.get("gain_annual_abs_eur"), 0),
                            "Marge nette annuelle (EUR)": _fmt(row.get("annual_net_margin_eur"), 0),
                            "Prix capte PV+BESS (EUR/MWh)": _fmt(row.get("capture_price_pv_bess_eur_per_mwh"), 1),
                            "Cycles equivalents": _fmt(row.get("equivalent_cycles"), 1),
                        }
                    )
                st.dataframe(pd.DataFrame(comparison_rows), width="stretch", hide_index=True)

                neg_context = _negative_price_context_table(
                    aligned_df=aligned_df,
                    optimum_dispatch=techno_dispatch,
                    cre_dispatch=cre_dispatch,
                )
                if not neg_context.empty:
                    st.markdown("#### Contexte des 2 premieres heures de prix negatifs")
                    neg_hours = pd.to_datetime(neg_context["timestamp"], errors="coerce").dropna().sort_values()
                    if len(neg_hours) >= 2:
                        is_consecutive = bool(
                            abs((neg_hours.iloc[1] - neg_hours.iloc[0]).total_seconds() - 3600.0) < 1e-6
                        )
                        st.caption(
                            "Heures observees: "
                            + ", ".join(ts.strftime("%Y-%m-%d %H:%M") for ts in neg_hours.iloc[:2])
                            + (" (consecutives)." if is_consecutive else " (non consecutives).")
                        )
                    else:
                        st.caption("Une seule heure negative detectee dans l'historique.")

                    ctx_display = neg_context.copy()
                    ctx_display["timestamp"] = pd.to_datetime(
                        ctx_display["timestamp"],
                        errors="coerce",
                    ).dt.strftime("%Y-%m-%d %H:%M")
                    for col in [c for c in ctx_display.columns if c != "timestamp"]:
                        ctx_display[col] = pd.to_numeric(ctx_display[col], errors="coerce").map(
                            lambda x: _fmt(x, 2)
                        )
                    st.dataframe(ctx_display, width="stretch", hide_index=True)
                else:
                    st.info("Aucune heure de prix negatif detectee pour la comparaison Optimum vs CRE.")
            else:
                st.warning("Scenario CRE non retrouve dans la matrice calculee.")

            key_table = _key_configs_table(summary_df, key_config_ids)
            if not key_table.empty:
                st.markdown("#### Comparaison des configurations clés")
                st.dataframe(key_table, width="stretch")

            st.markdown("#### Tableau de synthese")
            st.dataframe(summary_display_df, width="stretch")

            highlights: Dict[str, str] = {}
            if reco_brut and reco_brut.config_id:
                highlights["Gain brut max"] = reco_brut.config_id
            if reco_marginal and reco_marginal.config_id:
                highlights["Reco marginale"] = reco_marginal.config_id
            if reco_tech and reco_tech.config_id:
                highlights["Reco techno"] = reco_tech.config_id
            if cre_config_id:
                highlights["Scenario CRE"] = cre_config_id

            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(
                    _plot_metric_heatmap(
                        summary_df,
                        value_col="gain_annual_abs_eur",
                        title="Heatmap potentiel brut (MW x duree)",
                        color_label="Gain brut annuel (EUR)",
                        color_scale="Viridis",
                        highlight_config_ids=highlights,
                    ),
                    width="stretch",
                    config=PLOT_CONFIG,
                    key="chart_pvbess_heatmap_gain",
                )
            with col_b:
                st.plotly_chart(
                    _plot_metric_heatmap(
                        summary_df,
                        value_col="annual_net_margin_eur",
                        title="Heatmap rentabilite (MW x duree)",
                        color_label="Marge nette annuelle (EUR)",
                        color_scale="RdBu",
                        color_midpoint=0.0,
                        highlight_config_ids=highlights,
                    ),
                    width="stretch",
                    config=PLOT_CONFIG,
                    key="chart_pvbess_heatmap_net",
                )
            st.plotly_chart(
                _plot_marginal_value_evolution(summary_df),
                width="stretch",
                config=PLOT_CONFIG,
                key="chart_pvbess_marginal_value",
            )
            st.plotly_chart(
                _plot_dispatch_heatmap(selected_dispatch),
                width="stretch",
                config=PLOT_CONFIG,
                key="chart_pvbess_dispatch_heatmap_selected",
            )

            st.markdown("#### Conclusions")
            if result_obj.conclusions:
                for line in result_obj.conclusions:
                    st.markdown(f"- {line}")
            else:
                st.info(t("BESS_SIZING_NO_CONCLUSIONS"))

        with tab_pv:
            st.markdown("### Analyse PV")
            if not isinstance(pv_hourly, pd.DataFrame) or pv_hourly.empty:
                st.info("Donnees PV indisponibles.")
            else:
                pv_total = float(pv_hourly["pv_mwh"].sum())
                pv_peak = float(pv_hourly["pv_mwh"].max())
                pv_mean_prod = float(pv_hourly.loc[pv_hourly["pv_mwh"] > 0, "pv_mwh"].mean()) if (pv_hourly["pv_mwh"] > 0).any() else np.nan
                grid_charge = (
                    float(primary_dispatch["charge_from_grid_mwh"].sum())
                    if isinstance(primary_dispatch, pd.DataFrame) and "charge_from_grid_mwh" in primary_dispatch.columns
                    else 0.0
                )

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Production PV annuelle", f"{_fmt(pv_total, 1)} MWh")
                c2.metric("Puissance horaire max", f"{_fmt(pv_peak, 2)} MWh/h")
                c3.metric("Soutirage reseau (BESS)", f"{_fmt(grid_charge, 1)} MWh")
                c4.metric("Production moyenne sur heures actives", f"{_fmt(pv_mean_prod, 2)} MWh/h")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.plotly_chart(
                        _plot_typical_daily_profile(
                            pv_hourly,
                            timestamp_col="timestamp",
                            value_col="pv_mwh",
                            title="Courbe typique journaliere de production PV",
                            y_label="MWh",
                        ),
                        width="stretch",
                        config=PLOT_CONFIG,
                        key="chart_pv_typical_daily_profile",
                    )
                with col_b:
                    st.plotly_chart(
                        _plot_time_heatmap(
                            pv_hourly,
                            timestamp_col="timestamp",
                            value_col="pv_mwh",
                            title="Heatmap production annuelle PV (mois x heure)",
                            color_label="MWh",
                            agg="mean",
                            color_scale="YlOrRd",
                        ),
                        width="stretch",
                        config=PLOT_CONFIG,
                        key="chart_pv_heatmap_month_hour",
                    )

                st.plotly_chart(
                    _plot_monthly_aggregation(
                        pv_hourly,
                        timestamp_col="timestamp",
                        value_col="pv_mwh",
                        title="Production PV mensuelle",
                        y_label="MWh",
                        agg="sum",
                    ),
                    width="stretch",
                    config=PLOT_CONFIG,
                    key="chart_pv_monthly_aggregation",
                )

        with tab_weather:
            st.markdown("### Analyse Meteo (TMY)")
            has_tmy = isinstance(tmy_raw_df, pd.DataFrame) and not tmy_raw_df.empty
            if not has_tmy:
                st.info("Fichier TMY non fourni ou non exploitable.")
            else:
                tmy_ts_col = prepared_data.get("tmy_timestamp_col")
                if tmy_ts_col is None or tmy_ts_col not in tmy_raw_df.columns:
                    st.info("Colonne temporelle TMY indisponible.")
                else:
                    met = tmy_raw_df.copy()
                    met["timestamp"] = pd.to_datetime(met[str(tmy_ts_col)], errors="coerce", dayfirst=True)
                    met = met.dropna(subset=["timestamp"]).copy()
                    if met.empty:
                        st.info("Aucune donnee meteo valide.")
                    else:
                        ghi_col = _find_first_column(met, [["ghi"]])
                        dni_col = _find_first_column(met, [["dni"]])
                        dhi_col = _find_first_column(met, [["dhi"]])
                        temp_col = _find_first_column(met, [["temp"], ["temperature"]])
                        ghi_unit = _unit_from_map(tmy_units_map, ghi_col, "W/m2")
                        dni_unit = _unit_from_map(tmy_units_map, dni_col, "W/m2")
                        dhi_unit = _unit_from_map(tmy_units_map, dhi_col, "W/m2")
                        temp_unit = _unit_from_map(tmy_units_map, temp_col, "degC")

                        def _annual_irradiance(metric_col: str | None, unit_label: str) -> float:
                            if metric_col is None or metric_col not in met.columns:
                                return np.nan
                            step_h = _infer_step_hours(met, "timestamp")
                            converted = _irradiance_series_to_kwh_per_m2(
                                met[metric_col],
                                unit=unit_label,
                                step_hours=step_h,
                            )
                            return float(converted.dropna().sum()) if converted.notna().any() else np.nan

                        annual_ghi = _annual_irradiance(ghi_col, ghi_unit)
                        annual_dni = _annual_irradiance(dni_col, dni_unit)
                        annual_dhi = _annual_irradiance(dhi_col, dhi_unit)
                        mean_temp = (
                            float(pd.to_numeric(met[temp_col], errors="coerce").mean())
                            if temp_col is not None
                            else np.nan
                        )

                        annual_poa = np.nan
                        annual_horiz = np.nan
                        tilt_gain_pct = np.nan

                        if isinstance(pv_raw_df, pd.DataFrame) and not pv_raw_df.empty:
                            pv_weather = pv_raw_df.copy()
                            pv_ts_col = prepared_data.get("pv_timestamp_col")
                            if pv_ts_col and pv_ts_col in pv_weather.columns:
                                pv_weather["timestamp"] = pd.to_datetime(
                                    pv_weather[str(pv_ts_col)],
                                    errors="coerce",
                                    dayfirst=True,
                                )
                            else:
                                ts_guess = _find_first_column(pv_weather, [["date"], ["time"], ["timestamp"]])
                                if ts_guess is not None:
                                    pv_weather["timestamp"] = pd.to_datetime(
                                        pv_weather[ts_guess],
                                        errors="coerce",
                                        dayfirst=True,
                                    )

                            if "timestamp" in pv_weather.columns:
                                pv_weather = pv_weather.dropna(subset=["timestamp"]).copy()
                                if not pv_weather.empty:
                                    poa_col = _find_first_column(
                                        pv_weather,
                                        [["globinc"], ["gti"], ["gpoa"], ["poa"], ["globeff"]],
                                    )
                                    horiz_col = _find_first_column(
                                        pv_weather,
                                        [["globhor"], ["ghi"]],
                                    )
                                    step_h_pv = _infer_step_hours(pv_weather, "timestamp")

                                    if poa_col is not None and poa_col in pv_weather.columns:
                                        poa_unit = _unit_from_map(pv_units_map, poa_col, "W/m2")
                                        poa_energy = _irradiance_series_to_kwh_per_m2(
                                            pv_weather[poa_col],
                                            unit=poa_unit,
                                            step_hours=step_h_pv,
                                        )
                                        if poa_energy.notna().any():
                                            annual_poa = float(poa_energy.dropna().sum())

                                    if horiz_col is not None and horiz_col in pv_weather.columns:
                                        horiz_unit = _unit_from_map(pv_units_map, horiz_col, "W/m2")
                                        horiz_energy = _irradiance_series_to_kwh_per_m2(
                                            pv_weather[horiz_col],
                                            unit=horiz_unit,
                                            step_hours=step_h_pv,
                                        )
                                        if horiz_energy.notna().any():
                                            annual_horiz = float(horiz_energy.dropna().sum())

                        if pd.isna(annual_horiz) and pd.notna(annual_ghi):
                            annual_horiz = annual_ghi
                        if pd.notna(annual_poa) and pd.notna(annual_horiz) and float(annual_horiz) > 0:
                            tilt_gain_pct = 100.0 * (float(annual_poa) / float(annual_horiz) - 1.0)

                        c1, c2, c3, c4, c5 = st.columns(5)
                        c1.metric(
                            "Irradiance annuelle GHI (kWh/m²)",
                            _fmt(annual_ghi, 1) if pd.notna(annual_ghi) else "n/a",
                        )
                        c2.metric(
                            "Irradiance annuelle DNI (kWh/m²)",
                            _fmt(annual_dni, 1) if pd.notna(annual_dni) else "n/a",
                        )
                        c3.metric(
                            "Irradiance annuelle DHI (kWh/m²)",
                            _fmt(annual_dhi, 1) if pd.notna(annual_dhi) else "n/a",
                        )
                        c4.metric(
                            "Irradiance annuelle plan incline (kWh/m²)",
                            _fmt(annual_poa, 1) if pd.notna(annual_poa) else "n/a",
                        )
                        c5.metric(
                            "Gain inclinaison vs horizontal (%)",
                            _fmt(tilt_gain_pct, 1) if pd.notna(tilt_gain_pct) else "n/a",
                        )

                        c6 = st.columns(1)[0]
                        c6.metric(
                            f"Temperature moyenne ({temp_unit or 'degC'})",
                            _fmt(mean_temp, 1) if pd.notna(mean_temp) else "n/a",
                        )

                        if ghi_col is None:
                            st.info("Colonne GHI indisponible: graphiques GHI + production PV non affiches.")
                        elif not isinstance(pv_hourly, pd.DataFrame) or pv_hourly.empty:
                            st.info("Production PV indisponible: graphiques GHI + production PV non affiches.")
                        else:
                            ghi_df = met[["timestamp", ghi_col]].copy().rename(columns={ghi_col: "ghi"})
                            ghi_df["ghi"] = pd.to_numeric(ghi_df["ghi"], errors="coerce")
                            ghi_df = ghi_df.dropna(subset=["timestamp", "ghi"])

                            pv_plot = pv_hourly[["timestamp", "pv_mwh"]].copy()
                            pv_plot["timestamp"] = pd.to_datetime(pv_plot["timestamp"], errors="coerce")
                            pv_plot["pv_mwh"] = pd.to_numeric(pv_plot["pv_mwh"], errors="coerce")
                            pv_plot = pv_plot.dropna(subset=["timestamp", "pv_mwh"])

                            merged_weather = pv_plot.merge(ghi_df, on="timestamp", how="inner")
                            if merged_weather.empty:
                                ghi_key = ghi_df.copy()
                                ghi_key["month"] = ghi_key["timestamp"].dt.month
                                ghi_key["day"] = ghi_key["timestamp"].dt.day
                                ghi_key["hour"] = ghi_key["timestamp"].dt.hour
                                ghi_key = ghi_key.groupby(["month", "day", "hour"], as_index=False)["ghi"].mean()

                                pv_key = pv_plot.copy()
                                pv_key["month"] = pv_key["timestamp"].dt.month
                                pv_key["day"] = pv_key["timestamp"].dt.day
                                pv_key["hour"] = pv_key["timestamp"].dt.hour
                                merged_weather = pv_key.merge(
                                    ghi_key,
                                    on=["month", "day", "hour"],
                                    how="left",
                                )
                                merged_weather = merged_weather.dropna(subset=["ghi"])
                            if merged_weather.empty:
                                st.info("Impossible de construire les profils combines GHI + production PV.")
                            else:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.plotly_chart(
                                        _plot_ghi_pv_annual_profile(
                                            merged_weather,
                                            timestamp_col="timestamp",
                                            ghi_col="ghi",
                                            pv_col="pv_mwh",
                                            ghi_unit=ghi_unit,
                                        ),
                                        width="stretch",
                                        config=PLOT_CONFIG,
                                        key="chart_weather_ghi_pv_annual",
                                    )
                                with col_b:
                                    st.plotly_chart(
                                        _plot_ghi_pv_typical_daily_profile(
                                            merged_weather,
                                            timestamp_col="timestamp",
                                            ghi_col="ghi",
                                            pv_col="pv_mwh",
                                            ghi_unit=ghi_unit,
                                        ),
                                        width="stretch",
                                        config=PLOT_CONFIG,
                                        key="chart_weather_ghi_pv_typical",
                                    )

                        if temp_col is not None:
                            st.plotly_chart(
                                _plot_temperature_histogram(
                                    met,
                                    value_col=temp_col,
                                    unit_label=temp_unit,
                                ),
                                width="stretch",
                                config=PLOT_CONFIG,
                                key="chart_weather_temperature_histogram",
                            )

                        st.markdown("#### Correlation meteo vs production PV")
                        _display_tmy_coherence(result_obj.tmy_coherence)

        with tab_market:
            st.markdown("### Analyse marché")
            if not isinstance(market_hourly, pd.DataFrame) or market_hourly.empty:
                st.info("Donnees de prix indisponibles.")
            else:
                mean_price = float(market_hourly["price_eur_per_mwh"].mean())
                neg_hours = int((market_hourly["price_eur_per_mwh"] < 0).sum())
                neg_share = 100.0 * neg_hours / max(1, len(market_hourly))
                primary_label_market = str(primary_row.get("config_label", primary_config_id))

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Prix moyen", f"{_fmt(mean_price, 1)} EUR/MWh")
                c2.metric("Prix capte PV seul", f"{_fmt(primary_row.get('capture_price_pv_only_eur_per_mwh'), 1)} EUR/MWh")
                c3.metric("Prix capte PV+BESS (solution retenue)", f"{_fmt(primary_row.get('capture_price_pv_bess_eur_per_mwh'), 1)} EUR/MWh")
                c4.metric("Heures prix negatifs", f"{neg_hours} ({_fmt(neg_share, 1)} %)")
                st.caption(
                    f"Origine: calcule sur le scenario retenu ({primary_label_market}). "
                    "Formule = recettes d'injection PV+BESS / energie injectee reseau "
                    "(PV direct + decharge batterie)."
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    st.plotly_chart(
                        _plot_typical_daily_profile(
                            market_hourly,
                            timestamp_col="timestamp",
                            value_col="price_eur_per_mwh",
                            title="Courbe journaliere typique du prix",
                            y_label="EUR/MWh",
                        ),
                        width="stretch",
                        config=PLOT_CONFIG,
                        key="chart_market_typical_daily_profile",
                    )
                with col_b:
                    st.plotly_chart(
                        _plot_time_heatmap(
                            market_hourly,
                            timestamp_col="timestamp",
                            value_col="price_eur_per_mwh",
                            title="Heatmap market price (mois x heure)",
                            color_label="EUR/MWh",
                            agg="mean",
                            color_scale="RdYlBu_r",
                        ),
                        width="stretch",
                        config=PLOT_CONFIG,
                        key="chart_market_heatmap_month_hour",
                    )

                market_tmp = market_hourly.copy()
                market_tmp["timestamp"] = pd.to_datetime(market_tmp["timestamp"], errors="coerce")
                market_tmp["month"] = market_tmp["timestamp"].dt.month
                monthly_neg = (
                    market_tmp.assign(is_neg=market_tmp["price_eur_per_mwh"] < 0)
                    .groupby("month", as_index=False)["is_neg"]
                    .sum()
                    .rename(columns={"is_neg": "negative_hours"})
                )
                fig_neg = px.bar(
                    monthly_neg,
                    x="month",
                    y="negative_hours",
                    title="Heures de prix negatifs par mois",
                    labels={"month": "Month", "negative_hours": "Hours"},
                )
                fig_neg.update_layout(height=360)
                st.plotly_chart(
                    fig_neg,
                    width="stretch",
                    config=PLOT_CONFIG,
                    key="chart_market_negative_hours_month",
                )

        with tab_detail:
            st.markdown("### Warnings")
            if result_obj.warnings:
                for w in result_obj.warnings:
                    st.warning(w)
            else:
                st.success(t("BESS_SIZING_WARNINGS_EMPTY"))

            st.markdown("### Hypotheses de simulation")
            st.json(result_obj.assumptions)

            st.markdown("### Tables detaillees")
            st.dataframe(summary_display_df, width="stretch")
            if isinstance(primary_dispatch, pd.DataFrame) and not primary_dispatch.empty:
                st.dataframe(primary_dispatch.head(200), width="stretch")
            if isinstance(aligned_df, pd.DataFrame) and not aligned_df.empty:
                st.dataframe(aligned_df.head(200), width="stretch")

            st.markdown("### Exports")
            summary_bytes = _df_to_csv_bytes(_summary_export_table(result_obj.summary_df))
            st.download_button(
                "Exporter synthese configurations (CSV)",
                data=summary_bytes,
                file_name="bess_sizing_summary.csv",
                mime="text/csv",
                width="stretch",
            )
            if isinstance(primary_dispatch, pd.DataFrame) and not primary_dispatch.empty:
                st.download_button(
                    "Exporter dispatch PV+BESS (CSV)",
                    data=_df_to_csv_bytes(primary_dispatch),
                    file_name=f"bess_dispatch_{primary_config_id}.csv",
                    mime="text/csv",
                    width="stretch",
                )
            if isinstance(aligned_df, pd.DataFrame) and not aligned_df.empty:
                st.download_button(
                    "Exporter donnees alignees PV + prix (CSV)",
                    data=_df_to_csv_bytes(aligned_df),
                    file_name="pv_market_aligned.csv",
                    mime="text/csv",
                    width="stretch",
                )
            if isinstance(pv_hourly, pd.DataFrame) and not pv_hourly.empty:
                st.download_button(
                    "Exporter production PV horaire (CSV)",
                    data=_df_to_csv_bytes(pv_hourly),
                    file_name="pv_hourly.csv",
                    mime="text/csv",
                    width="stretch",
                )
            if isinstance(market_hourly, pd.DataFrame) and not market_hourly.empty:
                st.download_button(
                    "Exporter prix electricite horaires (CSV)",
                    data=_df_to_csv_bytes(market_hourly),
                    file_name="market_hourly.csv",
                    mime="text/csv",
                    width="stretch",
                )
            if isinstance(tmy_hourly, pd.DataFrame) and not tmy_hourly.empty:
                st.download_button(
                    "Exporter signal meteo horaire (CSV)",
                    data=_df_to_csv_bytes(tmy_hourly),
                    file_name="tmy_hourly.csv",
                    mime="text/csv",
                    width="stretch",
                )
