from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd

try:
    from scipy.optimize import linprog
    from scipy.sparse import lil_matrix

    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False
    linprog = None
    lil_matrix = None


@dataclass(frozen=True)
class BatteryParameters:
    p_charge_max_mw: float
    p_discharge_max_mw: float
    energy_nominal_mwh: float
    soc_min: float = 0.15
    soc_max: float = 0.95
    soc_initial: float = 0.50
    eta_charge: float = 0.922
    eta_discharge: float = 0.922

    @property
    def soc_min_mwh(self) -> float:
        return self.energy_nominal_mwh * self.soc_min

    @property
    def soc_max_mwh(self) -> float:
        return self.energy_nominal_mwh * self.soc_max

    @property
    def soc_initial_mwh(self) -> float:
        return self.energy_nominal_mwh * self.soc_initial

    @property
    def roundtrip_efficiency(self) -> float:
        return self.eta_charge * self.eta_discharge

    @property
    def usable_energy_mwh(self) -> float:
        return max(0.0, self.soc_max_mwh - self.soc_min_mwh)

    def validate(self) -> None:
        if self.p_charge_max_mw <= 0:
            raise ValueError("p_charge_max_mw must be > 0.")
        if self.p_discharge_max_mw <= 0:
            raise ValueError("p_discharge_max_mw must be > 0.")
        if self.energy_nominal_mwh <= 0:
            raise ValueError("energy_nominal_mwh must be > 0.")
        if not (0.0 <= self.soc_min < self.soc_max <= 1.0):
            raise ValueError("SOC bounds must satisfy 0 <= soc_min < soc_max <= 1.")
        if not (self.soc_min <= self.soc_initial <= self.soc_max):
            raise ValueError("soc_initial must be within [soc_min, soc_max].")
        if not (0.0 < self.eta_charge <= 1.0):
            raise ValueError("eta_charge must be in ]0, 1].")
        if not (0.0 < self.eta_discharge <= 1.0):
            raise ValueError("eta_discharge must be in ]0, 1].")


@dataclass
class DispatchOptimizationResult:
    dispatch_df: pd.DataFrame
    kpis: Dict[str, Any]
    warnings: List[str]
    solver: str
    solver_status: str


def _safe_div(num: float, den: float) -> float | None:
    if den is None or den == 0:
        return None
    return float(num) / float(den)


def _solve_lp_with_scipy(
    *,
    timestamps: pd.Series,
    pv_mwh: np.ndarray,
    prices: np.ndarray,
    params: BatteryParameters,
    enforce_terminal_soc: bool,
) -> tuple[pd.DataFrame, Dict[str, str]]:
    n = len(pv_mwh)
    n_vars = 3 * n

    idx_charge = np.arange(0, n, dtype=int)
    idx_discharge = np.arange(n, 2 * n, dtype=int)
    idx_soc = np.arange(2 * n, 3 * n, dtype=int)

    # Maximize sum(price * (-charge + discharge)).
    # scipy.linprog minimizes c @ x.
    c = np.zeros(n_vars, dtype=float)
    c[idx_charge] = prices
    c[idx_discharge] = -prices

    n_eq = n + (1 if enforce_terminal_soc else 0)
    a_eq = lil_matrix((n_eq, n_vars), dtype=float)
    b_eq = np.zeros(n_eq, dtype=float)

    for t in range(n):
        a_eq[t, idx_soc[t]] = 1.0
        a_eq[t, idx_charge[t]] = -params.eta_charge
        a_eq[t, idx_discharge[t]] = 1.0 / params.eta_discharge
        if t == 0:
            b_eq[t] = params.soc_initial_mwh
        else:
            a_eq[t, idx_soc[t - 1]] = -1.0

    if enforce_terminal_soc:
        last = n
        a_eq[last, idx_soc[-1]] = 1.0
        b_eq[last] = params.soc_initial_mwh

    bounds: list[tuple[float, float]] = []
    charge_upper = np.minimum(params.p_charge_max_mw, pv_mwh)
    for upper in charge_upper:
        bounds.append((0.0, float(max(0.0, upper))))
    for _ in range(n):
        bounds.append((0.0, float(params.p_discharge_max_mw)))
    for _ in range(n):
        bounds.append((float(params.soc_min_mwh), float(params.soc_max_mwh)))

    result = linprog(
        c=c,
        A_eq=a_eq.tocsc(),
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not result.success or result.x is None:
        raise RuntimeError(f"LP solver failed: {result.message}")

    x = result.x
    charge_from_pv = x[idx_charge]
    discharge_to_grid = x[idx_discharge]
    soc = x[idx_soc]

    dispatch = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps),
            "pv_mwh": pv_mwh,
            "price_eur_per_mwh": prices,
            "charge_from_pv_mwh": charge_from_pv,
            "discharge_to_grid_mwh": discharge_to_grid,
            "soc_mwh": soc,
        }
    )
    return dispatch, {"status": str(result.status), "message": str(result.message)}


def _solve_with_greedy_heuristic(
    *,
    timestamps: pd.Series,
    pv_mwh: np.ndarray,
    prices: np.ndarray,
    params: BatteryParameters,
    enforce_terminal_soc: bool,
) -> tuple[pd.DataFrame, Dict[str, str], List[str]]:
    n = len(pv_mwh)
    warnings: List[str] = []

    suffix_max = np.maximum.accumulate(prices[::-1])[::-1]

    charge_from_pv = np.zeros(n, dtype=float)
    discharge_to_grid = np.zeros(n, dtype=float)
    soc = np.zeros(n, dtype=float)

    state_soc = params.soc_initial_mwh
    rt_eff = params.roundtrip_efficiency

    for t in range(n):
        price_t = float(prices[t])
        pv_t = float(max(0.0, pv_mwh[t]))
        future_best = float(suffix_max[t + 1]) if t + 1 < n else price_t

        discharge_limit = min(
            params.p_discharge_max_mw,
            max(0.0, state_soc - params.soc_min_mwh) * params.eta_discharge,
        )

        charge_limit = min(
            params.p_charge_max_mw,
            pv_t,
            max(0.0, params.soc_max_mwh - state_soc) / params.eta_charge,
        )

        should_discharge = (t == n - 1) or (price_t >= future_best * 0.995)
        should_charge = (future_best * rt_eff) > price_t

        discharge = discharge_limit if should_discharge else 0.0
        charge = charge_limit if (not should_discharge and should_charge) else 0.0

        state_soc = (
            state_soc
            + params.eta_charge * charge
            - discharge / params.eta_discharge
        )
        state_soc = min(max(state_soc, params.soc_min_mwh), params.soc_max_mwh)

        charge_from_pv[t] = charge
        discharge_to_grid[t] = discharge
        soc[t] = state_soc

    if enforce_terminal_soc:
        delta = abs(float(soc[-1] - params.soc_initial_mwh))
        if delta > 1e-3:
            warnings.append(
                "Terminal SOC equality requested but not enforced in heuristic solver."
            )

    dispatch = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps),
            "pv_mwh": pv_mwh,
            "price_eur_per_mwh": prices,
            "charge_from_pv_mwh": charge_from_pv,
            "discharge_to_grid_mwh": discharge_to_grid,
            "soc_mwh": soc,
        }
    )
    return dispatch, {"status": "heuristic", "message": "greedy_lookahead"}, warnings


def _finalize_dispatch_df(
    dispatch_df: pd.DataFrame,
    *,
    params: BatteryParameters,
) -> pd.DataFrame:
    out = dispatch_df.copy()
    out["charge_to_battery_mwh"] = out["charge_from_pv_mwh"] * params.eta_charge
    out["discharge_from_battery_mwh"] = out["discharge_to_grid_mwh"] / params.eta_discharge

    out["pv_direct_injection_mwh"] = (out["pv_mwh"] - out["charge_from_pv_mwh"]).clip(lower=0.0)
    out["grid_injection_total_mwh"] = out["pv_direct_injection_mwh"] + out["discharge_to_grid_mwh"]

    out["charge_losses_mwh"] = out["charge_from_pv_mwh"] - out["charge_to_battery_mwh"]
    out["discharge_losses_mwh"] = out["discharge_from_battery_mwh"] - out["discharge_to_grid_mwh"]
    out["losses_mwh"] = out["charge_losses_mwh"] + out["discharge_losses_mwh"]

    out["revenue_pv_only_eur"] = out["pv_mwh"] * out["price_eur_per_mwh"]
    out["revenue_pv_bess_eur"] = out["grid_injection_total_mwh"] * out["price_eur_per_mwh"]

    out["is_power_saturated_charge"] = out["charge_from_pv_mwh"] >= (params.p_charge_max_mw - 1e-6)
    out["is_power_saturated_discharge"] = out["discharge_to_grid_mwh"] >= (params.p_discharge_max_mw - 1e-6)
    out["is_energy_saturated_min"] = out["soc_mwh"] <= (params.soc_min_mwh + 1e-6)
    out["is_energy_saturated_max"] = out["soc_mwh"] >= (params.soc_max_mwh - 1e-6)
    return out


def _compute_kpis(dispatch_df: pd.DataFrame, *, params: BatteryParameters) -> Dict[str, Any]:
    revenue_pv_only = float(dispatch_df["revenue_pv_only_eur"].sum())
    revenue_pv_bess = float(dispatch_df["revenue_pv_bess_eur"].sum())
    gain_abs = revenue_pv_bess - revenue_pv_only
    gain_rel_pct = (
        100.0 * gain_abs / abs(revenue_pv_only)
        if abs(revenue_pv_only) > 1e-9
        else None
    )

    pv_energy = float(dispatch_df["pv_mwh"].sum())
    grid_energy = float(dispatch_df["grid_injection_total_mwh"].sum())

    energy_charged = float(dispatch_df["charge_from_pv_mwh"].sum())
    energy_discharged = float(dispatch_df["discharge_to_grid_mwh"].sum())
    losses = float(dispatch_df["losses_mwh"].sum())
    throughput = float(
        dispatch_df["charge_to_battery_mwh"].sum()
        + dispatch_df["discharge_from_battery_mwh"].sum()
    )

    equivalent_cycles = None
    if params.energy_nominal_mwh > 0:
        equivalent_cycles = throughput / (2.0 * params.energy_nominal_mwh)

    utilization_rate_pct = (
        100.0 * equivalent_cycles / 365.0
        if equivalent_cycles is not None
        else None
    )

    return {
        "revenue_pv_only_eur": revenue_pv_only,
        "revenue_pv_bess_eur": revenue_pv_bess,
        "gain_annual_abs_eur": gain_abs,
        "gain_annual_rel_pct": gain_rel_pct,
        "capture_price_pv_only_eur_per_mwh": _safe_div(revenue_pv_only, pv_energy),
        "capture_price_pv_bess_eur_per_mwh": _safe_div(revenue_pv_bess, grid_energy),
        "energy_charged_mwh": energy_charged,
        "energy_discharged_mwh": energy_discharged,
        "losses_mwh": losses,
        "throughput_mwh": throughput,
        "equivalent_cycles": equivalent_cycles,
        "utilization_rate_pct": utilization_rate_pct,
        "hours_power_saturated": int(
            dispatch_df["is_power_saturated_charge"].sum()
            + dispatch_df["is_power_saturated_discharge"].sum()
        ),
        "hours_energy_saturated": int(
            dispatch_df["is_energy_saturated_min"].sum()
            + dispatch_df["is_energy_saturated_max"].sum()
        ),
        "hours_soc_at_min": int(dispatch_df["is_energy_saturated_min"].sum()),
        "hours_soc_at_max": int(dispatch_df["is_energy_saturated_max"].sum()),
    }


def optimize_dispatch_hourly(
    *,
    aligned_hourly_df: pd.DataFrame,
    battery_params: BatteryParameters,
    enforce_terminal_soc: bool = True,
    prefer_lp: bool = True,
) -> DispatchOptimizationResult:
    battery_params.validate()

    required_cols = {"timestamp", "pv_mwh", "price_eur_per_mwh"}
    missing = required_cols - set(aligned_hourly_df.columns)
    if missing:
        raise ValueError(
            "aligned_hourly_df missing required column(s): "
            + ", ".join(sorted(missing))
        )

    work = aligned_hourly_df[["timestamp", "pv_mwh", "price_eur_per_mwh"]].copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    work["pv_mwh"] = pd.to_numeric(work["pv_mwh"], errors="coerce")
    work["price_eur_per_mwh"] = pd.to_numeric(work["price_eur_per_mwh"], errors="coerce")
    work = work.dropna(subset=["timestamp", "pv_mwh", "price_eur_per_mwh"]).copy()
    work["pv_mwh"] = work["pv_mwh"].clip(lower=0.0)
    work = work.sort_values("timestamp").reset_index(drop=True)

    if work.empty:
        raise ValueError("No valid aligned rows available for dispatch optimization.")

    warnings: List[str] = []
    timestamps = work["timestamp"]
    pv = work["pv_mwh"].to_numpy(dtype=float)
    prices = work["price_eur_per_mwh"].to_numpy(dtype=float)

    solver = "heuristic"
    solver_meta = {"status": "", "message": ""}

    if prefer_lp and SCIPY_AVAILABLE:
        try:
            dispatch, solver_meta = _solve_lp_with_scipy(
                timestamps=timestamps,
                pv_mwh=pv,
                prices=prices,
                params=battery_params,
                enforce_terminal_soc=enforce_terminal_soc,
            )
            solver = "lp_highs"
        except Exception as exc:
            warnings.append(f"LP solver failed, fallback to heuristic solver: {exc}")
            dispatch, solver_meta, heuristic_warnings = _solve_with_greedy_heuristic(
                timestamps=timestamps,
                pv_mwh=pv,
                prices=prices,
                params=battery_params,
                enforce_terminal_soc=enforce_terminal_soc,
            )
            warnings.extend(heuristic_warnings)
    else:
        if prefer_lp and not SCIPY_AVAILABLE:
            warnings.append("SciPy not available: heuristic solver used.")
        dispatch, solver_meta, heuristic_warnings = _solve_with_greedy_heuristic(
            timestamps=timestamps,
            pv_mwh=pv,
            prices=prices,
            params=battery_params,
            enforce_terminal_soc=enforce_terminal_soc,
        )
        warnings.extend(heuristic_warnings)

    finalized = _finalize_dispatch_df(dispatch, params=battery_params)
    kpis = _compute_kpis(finalized, params=battery_params)

    return DispatchOptimizationResult(
        dispatch_df=finalized,
        kpis=kpis,
        warnings=warnings,
        solver=solver,
        solver_status=f"{solver_meta.get('status', '')}: {solver_meta.get('message', '')}",
    )
