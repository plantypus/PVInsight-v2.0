# BESS Sizing V2 - Functional Notes

## Objective
V2 shifts from "max gross value" to "most relevant configuration by analysis mode":
- Mode A: techno-economic with user CAPEX/OPEX.
- Mode B: techno-economic with default CAPEX/OPEX from `economic_defaults.json`.
- Mode C: marginal optimization without CAPEX/OPEX.

## Main modules
- `v2_models.py`: dataclasses for technical, economic, marginal inputs and sweep outputs.
- `v2_defaults.py`: default economic assumptions loader (no hardcoded costs in business logic).
- `v2_dispatch.py`: hourly dispatch engine (LP with heuristic fallback), PV/grid charging options, export limit.
- `v2_economics.py`: CAPEX/OPEX, annualized costs, net metrics, simple payback, simplified NPV.
- `v2_marginal.py`: gain share, marginal gain per MW/MWh, knee-point proxy, marginal recommendation.
- `v2_conclusions.py`: KPI-driven automatic conclusions.
- `v2_runner.py`: orchestrates candidate sweep, KPIs, recommendations and warnings.

## Recommendation logic
- Gross recommendation: max `gain_annual_abs_eur`.
- Techno-economic recommendation (A/B): best selected metric (`annual_net_margin_eur`, `npv_eur`, or minimum `simple_payback_years`).
- Marginal recommendation (C and also computed in A/B): smallest configuration reaching target share of max gross gain, with optional marginal thresholds.

## Guardrails
- Technical parameter validation (SOC, efficiencies, bounds).
- Domain boundary warnings (best solutions at upper bounds).
- Sensitivity warning when top techno-economic candidates are very close.
- Explicit warning in Mode B for default-cost dependency.

## Validation scenarios
Run:
```bash
python -m core.bess_sizing.v2_validation_scenarios
```
Scenarios cover:
- gross vs marginal recommendation behavior,
- high vs low cost impact on techno-economic recommendation,
- saturation behavior on limited PV surplus,
- grid-constraint effect,
- consistency of automatic conclusions.
