from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from core.bess_sizing.v2_conclusions import generate_auto_conclusions
from core.bess_sizing.v2_defaults import get_default_economic_inputs
from core.bess_sizing.v2_dispatch import (
    BatteryDispatchV2Parameters,
    DispatchOptimizationV2Result,
    optimize_dispatch_hourly_v2,
)
from core.bess_sizing.v2_economics import compute_economic_kpis_for_config
from core.bess_sizing.v2_marginal import run_marginal_analysis
from core.bess_sizing.v2_models import (
    AnalysisMode,
    BessCandidateConfig,
    BessEconomicInputs,
    BessRecommendation,
    BessSweepV2Result,
    BessTechnicalInputs,
    MarginalAnalysisInputs,
)


def build_power_grid_v2(
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


def _recommend_techno_config(
    summary_df: pd.DataFrame,
    recommendation_metric: str,
) -> BessRecommendation:
    if summary_df.empty:
        return BessRecommendation(
            mode="mode_a_custom_costs",
            config_id=None,
            config_label=None,
            criterion="not_applicable",
            score_value=None,
            reason="Technico-economic recommendation could not be computed (empty summary).",
        )

    work = summary_df.copy()
    metric = recommendation_metric if recommendation_metric in work.columns else "annual_net_margin_eur"
    valid = work[work[metric].notna()].copy()
    if valid.empty:
        return BessRecommendation(
            mode="mode_a_custom_costs",
            config_id=None,
            config_label=None,
            criterion=metric,
            score_value=None,
            reason=f"Technico-economic metric '{metric}' is not available.",
        )

    valid = valid.sort_values(
        by=[metric, "gain_annual_abs_eur", "power_mw", "duration_h"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)

    best_metric = float(valid.iloc[0][metric])
    if best_metric <= 0.0:
        return BessRecommendation(
            mode="mode_a_custom_costs",
            config_id=None,
            config_label=None,
            criterion=metric,
            score_value=best_metric,
            reason=(
                "Aucune configuration rentable dans le domaine teste "
                f"selon le critere '{metric}'."
            ),
        )

    row = valid.iloc[0]
    metric_reason = (
        "Configuration retenue car elle maximise la marge nette annualisee."
        if metric == "annual_net_margin_eur"
        else f"Configuration retenue car elle maximise '{metric}'."
    )
    return BessRecommendation(
        mode="mode_a_custom_costs",
        config_id=str(row["config_id"]),
        config_label=str(row["config_label"]),
        criterion=metric,
        score_value=float(row[metric]),
        reason=metric_reason,
    )


def _is_upper_boundary(row: pd.Series, max_power: float, max_energy: float) -> bool:
    return (
        abs(float(row["power_mw"]) - max_power) <= 1e-9
        and abs(float(row["energy_nominal_mwh"]) - max_energy) <= 1e-9
    )


def run_bess_sizing_v2(
    *,
    aligned_hourly_df: pd.DataFrame,
    powers_mw: List[float],
    durations_h: List[float],
    technical_inputs: BessTechnicalInputs,
    analysis_mode: AnalysisMode,
    marginal_inputs: MarginalAnalysisInputs,
    economic_inputs: Optional[BessEconomicInputs] = None,
    recommendation_metric: str = "annual_net_margin_eur",
    prefer_lp: bool = True,
    tmy_coherence: Optional[Dict[str, Any]] = None,
) -> BessSweepV2Result:
    technical_inputs.validate()
    marginal_inputs.validate()
    if analysis_mode not in ("mode_a_custom_costs", "mode_b_default_costs", "mode_c_marginal"):
        raise ValueError(f"Unsupported analysis_mode '{analysis_mode}'.")

    if aligned_hourly_df.empty:
        raise ValueError("aligned_hourly_df cannot be empty.")
    required_cols = {"timestamp", "pv_mwh", "price_eur_per_mwh"}
    missing = required_cols - set(aligned_hourly_df.columns)
    if missing:
        raise ValueError(
            "aligned_hourly_df missing required column(s): " + ", ".join(sorted(missing))
        )
    if not powers_mw:
        raise ValueError("powers_mw cannot be empty.")
    if not durations_h:
        raise ValueError("durations_h cannot be empty.")

    warnings: List[str] = []
    summary_rows: List[Dict[str, Any]] = []
    dispatch_by_config: Dict[str, pd.DataFrame] = {}

    eco_inputs = economic_inputs if economic_inputs is not None else get_default_economic_inputs()
    if economic_inputs is None:
        warnings.append(
            "No explicit CAPEX/OPEX provided; using default simplified economic assumptions from configuration."
        )

    max_power = max(float(x) for x in powers_mw)
    max_duration = max(float(x) for x in durations_h)
    max_energy = max_power * max_duration

    for power in sorted(set(float(x) for x in powers_mw)):
        if power <= 0:
            raise ValueError("All power values must be > 0.")

        for duration in sorted(set(float(x) for x in durations_h)):
            if duration <= 0:
                raise ValueError("All duration values must be > 0.")

            energy_nominal = power * duration
            config = BessCandidateConfig(
                power_mw=power,
                duration_h=duration,
                energy_nominal_mwh=energy_nominal,
                p_charge_max_mw=power,
                p_discharge_max_mw=power,
            )
            dispatch_params = BatteryDispatchV2Parameters(
                p_charge_max_mw=config.p_charge_max_mw,
                p_discharge_max_mw=config.p_discharge_max_mw,
                energy_nominal_mwh=config.energy_nominal_mwh,
                soc_min=technical_inputs.soc_min,
                soc_max=technical_inputs.soc_max,
                soc_initial=technical_inputs.soc_initial,
                eta_charge=technical_inputs.eta_charge,
                eta_discharge=technical_inputs.eta_discharge,
                enforce_terminal_soc=technical_inputs.enforce_terminal_soc,
                allow_grid_charging=technical_inputs.allow_grid_charging,
                grid_injection_limit_mw=technical_inputs.grid_injection_limit_mw,
                auxiliary_losses_mwh_per_h=technical_inputs.auxiliary_losses_mwh_per_h,
            )

            dispatch_result: DispatchOptimizationV2Result = optimize_dispatch_hourly_v2(
                aligned_hourly_df=aligned_hourly_df,
                battery_params=dispatch_params,
                prefer_lp=prefer_lp,
            )
            warnings.extend(dispatch_result.warnings)

            dispatch_by_config[config.config_id] = dispatch_result.dispatch_df
            row = {
                "config_id": config.config_id,
                "config_label": config.label,
                "power_mw": config.power_mw,
                "duration_h": config.duration_h,
                "energy_nominal_mwh": config.energy_nominal_mwh,
                "soc_min": technical_inputs.soc_min,
                "soc_max": technical_inputs.soc_max,
                "soc_initial": technical_inputs.soc_initial,
                "eta_charge": technical_inputs.eta_charge,
                "eta_discharge": technical_inputs.eta_discharge,
                "roundtrip_efficiency": technical_inputs.eta_charge * technical_inputs.eta_discharge,
                "grid_charging_allowed": technical_inputs.allow_grid_charging,
                "grid_injection_limit_mw": technical_inputs.grid_injection_limit_mw,
                "degradation_cost_eur_per_mwh_throughput": technical_inputs.degradation_cost_eur_per_mwh_throughput,
                "solver": dispatch_result.solver,
                "solver_status": dispatch_result.solver_status,
            }
            row.update(dispatch_result.kpis)

            if eco_inputs is not None:
                eco_kpis = compute_economic_kpis_for_config(
                    power_mw=config.power_mw,
                    energy_nominal_mwh=config.energy_nominal_mwh,
                    gain_annual_abs_eur=float(row["gain_annual_abs_eur"]),
                    throughput_mwh=float(row.get("throughput_mwh", 0.0)),
                    degradation_cost_eur_per_mwh_throughput=technical_inputs.degradation_cost_eur_per_mwh_throughput,
                    economic_inputs=eco_inputs,
                )
                row.update(eco_kpis)
            else:
                row.update(
                    {
                        "capex_total_eur": np.nan,
                        "opex_total_annual_eur": np.nan,
                        "annualized_cost_total_eur": np.nan,
                        "annual_net_revenue_eur": np.nan,
                        "annual_net_margin_eur": np.nan,
                        "simple_payback_years": np.nan,
                        "npv_eur": np.nan,
                    }
                )

            row["is_upper_boundary"] = int(_is_upper_boundary(pd.Series(row), max_power, max_energy))
            summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    if summary_df.empty:
        raise RuntimeError("BESS V2 sizing produced no scenario.")

    marginal = run_marginal_analysis(summary_df=summary_df, marginal_inputs=marginal_inputs)
    summary_df = marginal.summary_df

    summary_df = summary_df.sort_values(
        by=["gain_annual_abs_eur", "power_mw", "duration_h"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    brut_row = summary_df.iloc[0]
    brut_reco = BessRecommendation(
        mode=analysis_mode,
        config_id=str(brut_row["config_id"]),
        config_label=str(brut_row["config_label"]),
        criterion="gain_annual_abs_eur",
        score_value=float(brut_row["gain_annual_abs_eur"]),
        reason="Selected by maximum gross annual gain.",
    )

    techno_reco = _recommend_techno_config(
        summary_df=summary_df,
        recommendation_metric=recommendation_metric,
    )

    marginal_row = summary_df.loc[
        summary_df["config_id"] == marginal.marginal_recommended_config_id
    ]
    if marginal_row.empty:
        marginal_reco = BessRecommendation(
            mode=analysis_mode,
            config_id=None,
            config_label=None,
            criterion="marginal_compromise",
            score_value=None,
            reason="No marginal recommendation could be derived.",
        )
    else:
        r = marginal_row.iloc[0]
        knee_energy = (
            float(marginal.meta.get("knee_energy_mwh"))
            if isinstance(marginal.meta, dict) and marginal.meta.get("knee_energy_mwh") is not None
            else None
        )
        sat_energy = (
            float(marginal.meta.get("saturation_energy_mwh"))
            if isinstance(marginal.meta, dict) and marginal.meta.get("saturation_energy_mwh") is not None
            else None
        )
        if knee_energy is not None:
            reason = (
                "Configuration retenue via compromis marginal automatique "
                "(point de coude de la courbe gain/taille)."
            )
        elif sat_energy is not None:
            reason = (
                "Configuration retenue via compromis marginal automatique "
                "(debut de saturation des gains marginaux)."
            )
        else:
            reason = "Configuration retenue via compromis marginal automatique."
        marginal_reco = BessRecommendation(
            mode=analysis_mode,
            config_id=str(r["config_id"]),
            config_label=str(r["config_label"]),
            criterion="marginal_auto_compromise",
            score_value=float(r["gain_share_of_max_pct"]),
            reason=reason,
        )

    recommendations = {
        "brut_max": brut_reco,
        "techno": techno_reco,
        "marginal": marginal_reco,
    }

    n_on_upper = int(summary_df["is_upper_boundary"].sum())
    if n_on_upper > 0:
        warnings.append(
            f"{n_on_upper} configuration(s) lie on the upper search boundary."
        )
    if n_on_upper >= max(1, int(0.2 * len(summary_df))):
        warnings.append(
            "Many top candidates lie on upper bounds; consider extending the search domain."
        )

    sensitivity_warning = False
    metric = "annual_net_margin_eur" if "annual_net_margin_eur" in summary_df.columns else recommendation_metric
    metric_df = summary_df[summary_df[metric].notna()].sort_values(metric, ascending=False)
    if len(metric_df) >= 2:
        top = float(metric_df.iloc[0][metric])
        second = float(metric_df.iloc[1][metric])
        gap = abs(top - second)
        denom = max(1.0, abs(top))
        if gap / denom < 0.05:
            sensitivity_warning = True
            warnings.append(
                "Top techno-economic candidates are close; results are sensitive to CAPEX/OPEX assumptions."
            )

    conclusions = generate_auto_conclusions(
        summary_df=summary_df,
        mode=analysis_mode,
        recommendations=recommendations,
        sensitivity_warning=sensitivity_warning,
    )

    score_matrix_gain = (
        summary_df.pivot_table(
            index="power_mw",
            columns="duration_h",
            values="gain_annual_abs_eur",
            aggfunc="mean",
        )
        .sort_index(axis=0)
        .sort_index(axis=1)
    )
    score_matrix_net = (
        summary_df.pivot_table(
            index="power_mw",
            columns="duration_h",
            values="annual_net_margin_eur",
            aggfunc="mean",
        )
        .sort_index(axis=0)
        .sort_index(axis=1)
    )

    assumptions = {
        "analysis_mode": analysis_mode,
        "analysis_strategy": "always_marginal_plus_economic",
        "technical_inputs": asdict(technical_inputs),
        "economic_inputs": asdict(eco_inputs) if eco_inputs is not None else None,
        "marginal_inputs": asdict(marginal_inputs),
        "recommendation_metric": recommendation_metric,
        "solver_preference": "lp_if_available" if prefer_lp else "heuristic_only",
    }

    meta = {
        "marginal": marginal.meta,
        "knee_config_id": marginal.knee_config_id,
        "techno_knee_config_id": techno_reco.config_id,
        "techno_knee_criterion": techno_reco.criterion,
        "economic_viable": bool(techno_reco.config_id),
        "economic_metric": techno_reco.criterion,
        "economic_score_value": techno_reco.score_value,
        "n_candidates": int(len(summary_df)),
    }

    return BessSweepV2Result(
        aligned_hourly_df=aligned_hourly_df.copy(),
        summary_df=summary_df,
        dispatch_by_config=dispatch_by_config,
        score_matrix_gain_eur=score_matrix_gain,
        score_matrix_net_eur=score_matrix_net,
        recommendations=recommendations,
        warnings=list(dict.fromkeys(warnings)),
        conclusions=conclusions,
        assumptions=assumptions,
        tmy_coherence=tmy_coherence or {"available": False},
        meta=meta,
    )
