from __future__ import annotations

from dataclasses import replace
from typing import Dict

import numpy as np
import pandas as pd

from core.bess_sizing.v2_models import (
    BessEconomicInputs,
    BessTechnicalInputs,
    MarginalAnalysisInputs,
)
from core.bess_sizing.v2_runner import run_bess_sizing_v2


def _build_synthetic_dataset(days: int = 45, pv_peak_mw: float = 12.0) -> pd.DataFrame:
    n = days * 24
    ts = pd.date_range("2025-01-01", periods=n, freq="1h")
    hour = ts.hour.to_numpy(dtype=float)
    day = ts.dayofyear.to_numpy(dtype=float)

    pv_shape = np.sin((hour - 6.0) / 24.0 * 2.0 * np.pi)
    pv = np.maximum(0.0, pv_shape) * pv_peak_mw

    daily_wave = 20.0 * np.sin((hour - 15.0) / 24.0 * 2.0 * np.pi)
    seasonal = 6.0 * np.sin(day / 365.0 * 2.0 * np.pi)
    prices = 55.0 + daily_wave + seasonal

    return pd.DataFrame(
        {
            "timestamp": ts,
            "pv_mwh": pv,
            "price_eur_per_mwh": prices,
        }
    )


def run_v2_validation_scenarios() -> Dict[str, str]:
    df_base = _build_synthetic_dataset(days=45, pv_peak_mw=10.0)
    powers = [4.0, 8.0, 12.0, 16.0]
    durations = [2.0, 4.0, 6.0, 8.0]

    tech_base = BessTechnicalInputs(
        soc_min=0.15,
        soc_max=0.95,
        soc_initial=0.50,
        eta_charge=0.92,
        eta_discharge=0.92,
        enforce_terminal_soc=True,
        allow_grid_charging=False,
        pv_only_charging=True,
    )
    marginal = MarginalAnalysisInputs()

    res_c = run_bess_sizing_v2(
        aligned_hourly_df=df_base,
        powers_mw=powers,
        durations_h=durations,
        technical_inputs=tech_base,
        analysis_mode="mode_c_marginal",
        marginal_inputs=marginal,
        economic_inputs=None,
        prefer_lp=True,
    )

    brute_c = res_c.recommendations["brut_max"].config_id
    marginal_c = res_c.recommendations["marginal"].config_id
    assert brute_c is not None
    assert marginal_c is not None
    brute_energy = float(res_c.summary_df.loc[res_c.summary_df["config_id"] == brute_c, "energy_nominal_mwh"].iloc[0])
    marginal_energy = float(res_c.summary_df.loc[res_c.summary_df["config_id"] == marginal_c, "energy_nominal_mwh"].iloc[0])
    assert marginal_energy <= brute_energy

    econ_high = BessEconomicInputs(
        capex_power_eur_per_kw=500.0,
        capex_energy_eur_per_kwh=450.0,
        capex_fixed_eur=120000.0,
        opex_fixed_pct_capex=0.02,
        opex_fixed_eur_per_year=20000.0,
        opex_variable_eur_per_mwh_throughput=3.0,
        project_life_years=15,
        discount_rate=0.08,
    )
    res_a_high = run_bess_sizing_v2(
        aligned_hourly_df=df_base,
        powers_mw=powers,
        durations_h=durations,
        technical_inputs=tech_base,
        analysis_mode="mode_a_custom_costs",
        marginal_inputs=marginal,
        economic_inputs=econ_high,
        recommendation_metric="annual_net_margin_eur",
        prefer_lp=True,
    )
    techno_high = res_a_high.recommendations["techno"].config_id
    assert techno_high is None
    assert bool(res_a_high.meta.get("economic_viable")) is False

    econ_low = replace(
        econ_high,
        capex_power_eur_per_kw=0.0,
        capex_energy_eur_per_kwh=0.0,
        capex_fixed_eur=0.0,
        opex_fixed_pct_capex=0.0,
        opex_fixed_eur_per_year=0.0,
        opex_variable_eur_per_mwh_throughput=0.0,
    )
    res_a_low = run_bess_sizing_v2(
        aligned_hourly_df=df_base,
        powers_mw=powers,
        durations_h=durations,
        technical_inputs=tech_base,
        analysis_mode="mode_a_custom_costs",
        marginal_inputs=marginal,
        economic_inputs=econ_low,
        recommendation_metric="annual_net_margin_eur",
        prefer_lp=True,
    )
    techno_low = res_a_low.recommendations["techno"].config_id
    assert techno_low is not None
    techno_low_energy = float(
        res_a_low.summary_df.loc[
            res_a_low.summary_df["config_id"] == techno_low, "energy_nominal_mwh"
        ].iloc[0]
    )
    assert bool(res_a_low.meta.get("economic_viable")) is True
    assert techno_low_energy <= brute_energy

    df_limited_surplus = _build_synthetic_dataset(days=45, pv_peak_mw=6.0)
    res_limited = run_bess_sizing_v2(
        aligned_hourly_df=df_limited_surplus,
        powers_mw=powers,
        durations_h=durations,
        technical_inputs=tech_base,
        analysis_mode="mode_c_marginal",
        marginal_inputs=marginal,
        economic_inputs=None,
        prefer_lp=True,
    )
    envelope = (
        res_limited.summary_df.sort_values("gain_annual_abs_eur", ascending=False)
        .drop_duplicates(subset=["energy_nominal_mwh"], keep="first")
        .sort_values("energy_nominal_mwh")
    )
    deltas = envelope["gain_annual_abs_eur"].diff().dropna()
    if len(deltas) >= 2:
        assert float(deltas.iloc[-1]) <= float(deltas.iloc[0])

    tech_grid = replace(tech_base, grid_injection_limit_mw=4.0)
    res_grid = run_bess_sizing_v2(
        aligned_hourly_df=df_base,
        powers_mw=powers,
        durations_h=[2.0, 4.0, 6.0],
        technical_inputs=tech_grid,
        analysis_mode="mode_c_marginal",
        marginal_inputs=marginal,
        economic_inputs=None,
        prefer_lp=True,
    )
    assert float(res_grid.summary_df["power_saturation_rate_pct"].max()) > 0.0

    assert len(res_a_high.conclusions) > 0
    assert any("marginale" in line.lower() or "marginal" in line.lower() for line in res_a_high.conclusions)

    return {
        "scenario_1": "ok",
        "scenario_2": "ok",
        "scenario_3": "ok",
        "scenario_4": "ok",
        "scenario_5": "ok",
        "scenario_6": "ok",
    }


if __name__ == "__main__":
    print(run_v2_validation_scenarios())
