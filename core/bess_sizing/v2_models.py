from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

import pandas as pd


AnalysisMode = Literal[
    "mode_a_custom_costs",
    "mode_b_default_costs",
    "mode_c_marginal",
]


@dataclass(frozen=True)
class BessTechnicalInputs:
    soc_min: float = 0.15
    soc_max: float = 0.95
    soc_initial: float = 0.50
    eta_charge: float = 0.922
    eta_discharge: float = 0.922
    enforce_terminal_soc: bool = True
    allow_grid_charging: bool = False
    pv_only_charging: bool = True
    grid_injection_limit_mw: Optional[float] = None
    degradation_cost_eur_per_mwh_throughput: float = 0.0
    auxiliary_losses_mwh_per_h: float = 0.0
    time_step_hours: float = 1.0

    def validate(self) -> None:
        if not (0.0 <= self.soc_min < self.soc_max <= 1.0):
            raise ValueError("SOC bounds must satisfy 0 <= soc_min < soc_max <= 1.")
        if not (self.soc_min <= self.soc_initial <= self.soc_max):
            raise ValueError("soc_initial must be within [soc_min, soc_max].")
        if not (0.0 < self.eta_charge <= 1.0):
            raise ValueError("eta_charge must be in ]0, 1].")
        if not (0.0 < self.eta_discharge <= 1.0):
            raise ValueError("eta_discharge must be in ]0, 1].")
        if self.grid_injection_limit_mw is not None and self.grid_injection_limit_mw <= 0:
            raise ValueError("grid_injection_limit_mw must be > 0 when provided.")
        if self.degradation_cost_eur_per_mwh_throughput < 0:
            raise ValueError("degradation_cost_eur_per_mwh_throughput must be >= 0.")
        if self.auxiliary_losses_mwh_per_h < 0:
            raise ValueError("auxiliary_losses_mwh_per_h must be >= 0.")
        if self.time_step_hours <= 0:
            raise ValueError("time_step_hours must be > 0.")
        if self.pv_only_charging and self.allow_grid_charging:
            raise ValueError("pv_only_charging cannot be True when allow_grid_charging is True.")


@dataclass(frozen=True)
class BessEconomicInputs:
    capex_power_eur_per_kw: float
    capex_energy_eur_per_kwh: float
    capex_fixed_eur: float
    opex_fixed_pct_capex: float
    opex_fixed_eur_per_year: float
    opex_variable_eur_per_mwh_throughput: float
    project_life_years: int
    discount_rate: float
    replacement_year: Optional[int] = None
    replacement_fraction_capex: float = 0.0

    def validate(self) -> None:
        if self.capex_power_eur_per_kw < 0:
            raise ValueError("capex_power_eur_per_kw must be >= 0.")
        if self.capex_energy_eur_per_kwh < 0:
            raise ValueError("capex_energy_eur_per_kwh must be >= 0.")
        if self.capex_fixed_eur < 0:
            raise ValueError("capex_fixed_eur must be >= 0.")
        if self.opex_fixed_pct_capex < 0:
            raise ValueError("opex_fixed_pct_capex must be >= 0.")
        if self.opex_fixed_eur_per_year < 0:
            raise ValueError("opex_fixed_eur_per_year must be >= 0.")
        if self.opex_variable_eur_per_mwh_throughput < 0:
            raise ValueError("opex_variable_eur_per_mwh_throughput must be >= 0.")
        if self.project_life_years <= 0:
            raise ValueError("project_life_years must be > 0.")
        if self.discount_rate < 0:
            raise ValueError("discount_rate must be >= 0.")
        if self.replacement_year is not None and (
            self.replacement_year <= 0 or self.replacement_year > self.project_life_years
        ):
            raise ValueError("replacement_year must be in [1, project_life_years].")
        if not (0.0 <= self.replacement_fraction_capex <= 1.0):
            raise ValueError("replacement_fraction_capex must be in [0, 1].")


@dataclass(frozen=True)
class MarginalAnalysisInputs:
    auto_method: Literal["knee_then_saturation"] = "knee_then_saturation"

    def validate(self) -> None:
        if self.auto_method != "knee_then_saturation":
            raise ValueError("Unsupported marginal auto_method.")


@dataclass(frozen=True)
class BessCandidateConfig:
    power_mw: float
    duration_h: float
    energy_nominal_mwh: float
    p_charge_max_mw: float
    p_discharge_max_mw: float

    @property
    def config_id(self) -> str:
        return f"{self.power_mw:g}MW_{self.energy_nominal_mwh:g}MWh"

    @property
    def label(self) -> str:
        return f"{self.power_mw:g} MW / {self.energy_nominal_mwh:g} MWh"


@dataclass
class BessRecommendation:
    mode: AnalysisMode
    config_id: Optional[str]
    config_label: Optional[str]
    criterion: str
    score_value: Optional[float]
    reason: str


@dataclass
class BessSweepV2Result:
    aligned_hourly_df: pd.DataFrame
    summary_df: pd.DataFrame
    dispatch_by_config: Dict[str, pd.DataFrame]
    score_matrix_gain_eur: pd.DataFrame
    score_matrix_net_eur: pd.DataFrame
    recommendations: Dict[str, BessRecommendation]
    warnings: list[str]
    conclusions: list[str]
    assumptions: Dict[str, Any]
    tmy_coherence: Dict[str, Any]
    meta: Dict[str, Any] = field(default_factory=dict)
