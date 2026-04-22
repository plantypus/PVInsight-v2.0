from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.bess_sizing.v2_models import BessEconomicInputs, MarginalAnalysisInputs


DEFAULTS_PATH = Path(__file__).with_name("economic_defaults.json")


def _read_defaults_payload() -> Dict[str, Any]:
    if not DEFAULTS_PATH.exists():
        raise FileNotFoundError(
            f"Economic defaults file not found: {DEFAULTS_PATH}"
        )
    with DEFAULTS_PATH.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError("Economic defaults payload must be a JSON object.")
    return payload


def get_default_economic_inputs() -> BessEconomicInputs:
    payload = _read_defaults_payload()
    out = BessEconomicInputs(
        capex_power_eur_per_kw=float(payload.get("capex_power_eur_per_kw", 0.0)),
        capex_energy_eur_per_kwh=float(payload.get("capex_energy_eur_per_kwh", 0.0)),
        capex_fixed_eur=float(payload.get("capex_fixed_eur", 0.0)),
        opex_fixed_pct_capex=float(payload.get("opex_fixed_pct_capex", 0.0)),
        opex_fixed_eur_per_year=float(payload.get("opex_fixed_eur_per_year", 0.0)),
        opex_variable_eur_per_mwh_throughput=float(
            payload.get("opex_variable_eur_per_mwh_throughput", 0.0)
        ),
        project_life_years=int(payload.get("project_life_years", 1)),
        discount_rate=float(payload.get("discount_rate", 0.0)),
        replacement_year=(
            int(payload["replacement_year"])
            if payload.get("replacement_year") is not None
            else None
        ),
        replacement_fraction_capex=float(payload.get("replacement_fraction_capex", 0.0)),
    )
    out.validate()
    return out


def get_default_marginal_inputs() -> MarginalAnalysisInputs:
    out = MarginalAnalysisInputs()
    out.validate()
    return out
