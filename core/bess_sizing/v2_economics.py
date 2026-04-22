from __future__ import annotations

from typing import Any, Dict

import numpy as np

from core.bess_sizing.v2_models import BessEconomicInputs


def annuity_factor(discount_rate: float, years: int) -> float:
    if years <= 0:
        raise ValueError("years must be > 0.")
    if discount_rate <= 0:
        return 1.0 / years
    x = (1.0 + discount_rate) ** years
    return discount_rate * x / (x - 1.0)


def compute_economic_kpis_for_config(
    *,
    power_mw: float,
    energy_nominal_mwh: float,
    gain_annual_abs_eur: float,
    throughput_mwh: float,
    degradation_cost_eur_per_mwh_throughput: float,
    economic_inputs: BessEconomicInputs,
) -> Dict[str, Any]:
    economic_inputs.validate()

    capex_total = (
        power_mw * 1000.0 * economic_inputs.capex_power_eur_per_kw
        + energy_nominal_mwh * 1000.0 * economic_inputs.capex_energy_eur_per_kwh
        + economic_inputs.capex_fixed_eur
    )

    opex_fixed = (
        economic_inputs.opex_fixed_pct_capex * capex_total
        + economic_inputs.opex_fixed_eur_per_year
    )
    opex_variable = throughput_mwh * economic_inputs.opex_variable_eur_per_mwh_throughput
    degradation_cost = throughput_mwh * degradation_cost_eur_per_mwh_throughput
    opex_total = opex_fixed + opex_variable + degradation_cost

    annual_net_revenue = gain_annual_abs_eur - opex_total
    af = annuity_factor(economic_inputs.discount_rate, economic_inputs.project_life_years)
    annualized_capex = capex_total * af
    annualized_cost_total = annualized_capex + opex_total
    annual_net_margin = gain_annual_abs_eur - annualized_cost_total

    simple_payback_years = (
        capex_total / annual_net_revenue
        if annual_net_revenue > 0
        else None
    )

    years = np.arange(1, economic_inputs.project_life_years + 1, dtype=float)
    discount = (1.0 + economic_inputs.discount_rate) ** years
    npv = -capex_total + float((annual_net_revenue / discount).sum())
    replacement_cost_npv = 0.0
    if economic_inputs.replacement_year is not None and economic_inputs.replacement_fraction_capex > 0:
        replacement_cost = capex_total * economic_inputs.replacement_fraction_capex
        replacement_cost_npv = replacement_cost / (
            (1.0 + economic_inputs.discount_rate) ** float(economic_inputs.replacement_year)
        )
        npv -= replacement_cost_npv

    return {
        "capex_total_eur": capex_total,
        "opex_fixed_annual_eur": opex_fixed,
        "opex_variable_annual_eur": opex_variable,
        "degradation_cost_annual_eur": degradation_cost,
        "opex_total_annual_eur": opex_total,
        "annualized_capex_eur": annualized_capex,
        "annualized_cost_total_eur": annualized_cost_total,
        "annual_net_revenue_eur": annual_net_revenue,
        "annual_net_margin_eur": annual_net_margin,
        "simple_payback_years": simple_payback_years,
        "npv_eur": npv,
        "replacement_cost_npv_eur": replacement_cost_npv,
    }
