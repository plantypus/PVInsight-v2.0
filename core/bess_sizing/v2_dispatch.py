from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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
class BatteryDispatchV2Parameters:
    p_charge_max_mw: float
    p_discharge_max_mw: float
    energy_nominal_mwh: float
    soc_min: float = 0.15
    soc_max: float = 0.95
    soc_initial: float = 0.50
    eta_charge: float = 0.922
    eta_discharge: float = 0.922
    enforce_terminal_soc: bool = True
    allow_grid_charging: bool = False
    grid_injection_limit_mw: Optional[float] = None
    auxiliary_losses_mwh_per_h: float = 0.0

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
        if self.grid_injection_limit_mw is not None and self.grid_injection_limit_mw <= 0:
            raise ValueError("grid_injection_limit_mw must be > 0 when provided.")
        if self.auxiliary_losses_mwh_per_h < 0:
            raise ValueError("auxiliary_losses_mwh_per_h must be >= 0.")


@dataclass
class DispatchOptimizationV2Result:
    dispatch_df: pd.DataFrame
    kpis: Dict[str, Any]
    warnings: List[str]
    solver: str
    solver_status: str


def _safe_div(num: float, den: float) -> Optional[float]:
    if den is None or den == 0:
        return None
    return float(num) / float(den)


def _finalize_dispatch_df(
    dispatch_df: pd.DataFrame,
    *,
    params: BatteryDispatchV2Parameters,
) -> Tuple[pd.DataFrame, List[str]]:
    warnings: List[str] = []
    out = dispatch_df.copy()

    out["charge_total_mwh"] = out["charge_from_pv_mwh"] + out["charge_from_grid_mwh"]
    out["charge_to_battery_mwh"] = out["charge_total_mwh"] * params.eta_charge
    out["discharge_from_battery_mwh"] = out["discharge_to_grid_mwh"] / params.eta_discharge

    out["pv_direct_injection_mwh"] = (out["pv_mwh"] - out["charge_from_pv_mwh"]).clip(lower=0.0)

    if params.grid_injection_limit_mw is None:
        out["grid_injection_total_mwh"] = out["pv_direct_injection_mwh"] + out["discharge_to_grid_mwh"]
    else:
        raw_injection = out["pv_direct_injection_mwh"] + out["discharge_to_grid_mwh"]
        out["grid_injection_total_mwh"] = raw_injection.clip(upper=float(params.grid_injection_limit_mw))
        clipped = int((raw_injection > out["grid_injection_total_mwh"] + 1e-9).sum())
        if clipped > 0:
            warnings.append(
                f"Grid injection clipped on {clipped} row(s) by grid limit."
            )

    out["net_grid_export_mwh"] = out["grid_injection_total_mwh"] - out["charge_from_grid_mwh"]

    out["charge_losses_mwh"] = out["charge_total_mwh"] - out["charge_to_battery_mwh"]
    out["discharge_losses_mwh"] = out["discharge_from_battery_mwh"] - out["discharge_to_grid_mwh"]
    out["aux_losses_mwh"] = out["aux_losses_mwh"].clip(lower=0.0)
    out["losses_mwh"] = out["charge_losses_mwh"] + out["discharge_losses_mwh"] + out["aux_losses_mwh"]

    if params.grid_injection_limit_mw is None:
        out["revenue_pv_only_eur"] = out["pv_mwh"] * out["price_eur_per_mwh"]
    else:
        out["revenue_pv_only_eur"] = (
            np.minimum(out["pv_mwh"], float(params.grid_injection_limit_mw))
            * out["price_eur_per_mwh"]
        )

    out["revenue_pv_bess_eur"] = out["net_grid_export_mwh"] * out["price_eur_per_mwh"]

    out["is_power_saturated_charge"] = out["charge_total_mwh"] >= (params.p_charge_max_mw - 1e-6)
    out["is_power_saturated_discharge"] = out["discharge_to_grid_mwh"] >= (params.p_discharge_max_mw - 1e-6)
    out["is_energy_saturated_min"] = out["soc_mwh"] <= (params.soc_min_mwh + 1e-6)
    out["is_energy_saturated_max"] = out["soc_mwh"] >= (params.soc_max_mwh - 1e-6)

    return out, warnings


def _compute_kpis(dispatch_df: pd.DataFrame, *, params: BatteryDispatchV2Parameters) -> Dict[str, Any]:
    revenue_pv_only = float(dispatch_df["revenue_pv_only_eur"].sum())
    revenue_pv_bess = float(dispatch_df["revenue_pv_bess_eur"].sum())
    gain_abs = revenue_pv_bess - revenue_pv_only
    gain_rel_pct = 100.0 * gain_abs / abs(revenue_pv_only) if abs(revenue_pv_only) > 1e-9 else None

    pv_energy = float(dispatch_df["pv_mwh"].sum())
    grid_energy = float(dispatch_df["grid_injection_total_mwh"].sum())

    energy_charged_pv = float(dispatch_df["charge_from_pv_mwh"].sum())
    energy_charged_grid = float(dispatch_df["charge_from_grid_mwh"].sum())
    energy_charged_total = float(dispatch_df["charge_total_mwh"].sum())
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

    n_rows = max(1, len(dispatch_df))
    hours_power_saturated = int(
        dispatch_df["is_power_saturated_charge"].sum()
        + dispatch_df["is_power_saturated_discharge"].sum()
    )
    hours_energy_saturated = int(
        dispatch_df["is_energy_saturated_min"].sum()
        + dispatch_df["is_energy_saturated_max"].sum()
    )
    max_soc = float(dispatch_df["soc_mwh"].max())
    used_window = max(0.0, max_soc - params.soc_min_mwh)
    usable = max(1e-9, params.usable_energy_mwh)
    used_capacity_share_pct = 100.0 * used_window / usable
    underutilized_capacity_share_pct = 100.0 - min(100.0, used_capacity_share_pct)

    return {
        "revenue_pv_only_eur": revenue_pv_only,
        "revenue_pv_bess_eur": revenue_pv_bess,
        "gain_annual_abs_eur": gain_abs,
        "gain_annual_rel_pct": gain_rel_pct,
        "capture_price_pv_only_eur_per_mwh": _safe_div(revenue_pv_only, pv_energy),
        "capture_price_pv_bess_eur_per_mwh": _safe_div(revenue_pv_bess, grid_energy),
        "energy_charged_mwh": energy_charged_total,
        "energy_charged_from_pv_mwh": energy_charged_pv,
        "energy_charged_from_grid_mwh": energy_charged_grid,
        "energy_discharged_mwh": energy_discharged,
        "losses_mwh": losses,
        "throughput_mwh": throughput,
        "equivalent_cycles": equivalent_cycles,
        "utilization_rate_pct": utilization_rate_pct,
        "hours_power_saturated": hours_power_saturated,
        "hours_energy_saturated": hours_energy_saturated,
        "power_saturation_rate_pct": 100.0 * hours_power_saturated / n_rows,
        "energy_saturation_rate_pct": 100.0 * hours_energy_saturated / n_rows,
        "used_capacity_share_pct": min(100.0, max(0.0, used_capacity_share_pct)),
        "underutilized_capacity_share_pct": min(100.0, max(0.0, underutilized_capacity_share_pct)),
        "share_charge_from_grid_pct": 100.0 * _safe_div(energy_charged_grid, energy_charged_total)
        if energy_charged_total > 0
        else 0.0,
        "share_charge_from_pv_pct": 100.0 * _safe_div(energy_charged_pv, energy_charged_total)
        if energy_charged_total > 0
        else 0.0,
    }


def _solve_lp_with_scipy(
    *,
    timestamps: pd.Series,
    pv_mwh: np.ndarray,
    prices: np.ndarray,
    params: BatteryDispatchV2Parameters,
) -> tuple[pd.DataFrame, Dict[str, str]]:
    n = len(pv_mwh)
    n_vars = 4 * n

    idx_charge_pv = np.arange(0, n, dtype=int)
    idx_charge_grid = np.arange(n, 2 * n, dtype=int)
    idx_discharge = np.arange(2 * n, 3 * n, dtype=int)
    idx_soc = np.arange(3 * n, 4 * n, dtype=int)

    c = np.zeros(n_vars, dtype=float)
    c[idx_charge_pv] = prices
    c[idx_charge_grid] = prices
    c[idx_discharge] = -prices

    n_eq = n + (1 if params.enforce_terminal_soc else 0)
    a_eq = lil_matrix((n_eq, n_vars), dtype=float)
    b_eq = np.zeros(n_eq, dtype=float)

    for t in range(n):
        a_eq[t, idx_soc[t]] = 1.0
        a_eq[t, idx_charge_pv[t]] = -params.eta_charge
        a_eq[t, idx_charge_grid[t]] = -params.eta_charge
        a_eq[t, idx_discharge[t]] = 1.0 / params.eta_discharge
        if t == 0:
            b_eq[t] = params.soc_initial_mwh - params.auxiliary_losses_mwh_per_h
        else:
            a_eq[t, idx_soc[t - 1]] = -1.0
            b_eq[t] = -params.auxiliary_losses_mwh_per_h

    if params.enforce_terminal_soc:
        last = n
        a_eq[last, idx_soc[-1]] = 1.0
        b_eq[last] = params.soc_initial_mwh

    n_ub = n
    if params.grid_injection_limit_mw is not None:
        n_ub += n
    a_ub = lil_matrix((n_ub, n_vars), dtype=float)
    b_ub = np.zeros(n_ub, dtype=float)

    row = 0
    for t in range(n):
        a_ub[row, idx_charge_pv[t]] = 1.0
        a_ub[row, idx_charge_grid[t]] = 1.0
        b_ub[row] = params.p_charge_max_mw
        row += 1

    if params.grid_injection_limit_mw is not None:
        limit = float(params.grid_injection_limit_mw)
        for t in range(n):
            a_ub[row, idx_charge_pv[t]] = -1.0
            a_ub[row, idx_discharge[t]] = 1.0
            b_ub[row] = limit - pv_mwh[t]
            row += 1

    bounds: list[tuple[float, float]] = []
    charge_pv_upper = np.minimum(params.p_charge_max_mw, pv_mwh)
    for upper in charge_pv_upper:
        bounds.append((0.0, float(max(0.0, upper))))
    grid_upper = params.p_charge_max_mw if params.allow_grid_charging else 0.0
    for _ in range(n):
        bounds.append((0.0, float(grid_upper)))
    for _ in range(n):
        bounds.append((0.0, float(params.p_discharge_max_mw)))
    for _ in range(n):
        bounds.append((float(params.soc_min_mwh), float(params.soc_max_mwh)))

    result = linprog(
        c=c,
        A_ub=a_ub.tocsc(),
        b_ub=b_ub,
        A_eq=a_eq.tocsc(),
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )
    if not result.success or result.x is None:
        raise RuntimeError(f"LP solver failed: {result.message}")

    x = result.x
    charge_from_pv = x[idx_charge_pv]
    charge_from_grid = x[idx_charge_grid]
    discharge_to_grid = x[idx_discharge]
    soc = x[idx_soc]

    dispatch = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps),
            "pv_mwh": pv_mwh,
            "price_eur_per_mwh": prices,
            "charge_from_pv_mwh": charge_from_pv,
            "charge_from_grid_mwh": charge_from_grid,
            "discharge_to_grid_mwh": discharge_to_grid,
            "soc_mwh": soc,
            "aux_losses_mwh": np.full(n, params.auxiliary_losses_mwh_per_h, dtype=float),
        }
    )
    return dispatch, {"status": str(result.status), "message": str(result.message)}


def _solve_with_greedy_heuristic(
    *,
    timestamps: pd.Series,
    pv_mwh: np.ndarray,
    prices: np.ndarray,
    params: BatteryDispatchV2Parameters,
) -> tuple[pd.DataFrame, Dict[str, str], List[str]]:
    n = len(pv_mwh)
    warnings: List[str] = []

    suffix_max = np.maximum.accumulate(prices[::-1])[::-1]

    charge_from_pv = np.zeros(n, dtype=float)
    charge_from_grid = np.zeros(n, dtype=float)
    discharge_to_grid = np.zeros(n, dtype=float)
    soc = np.zeros(n, dtype=float)
    aux_losses_applied = np.zeros(n, dtype=float)

    state_soc = params.soc_initial_mwh
    rt_eff = params.roundtrip_efficiency

    for t in range(n):
        state_soc = max(params.soc_min_mwh, state_soc - params.auxiliary_losses_mwh_per_h)
        aux_losses_applied[t] = params.auxiliary_losses_mwh_per_h

        price_t = float(prices[t])
        pv_t = float(max(0.0, pv_mwh[t]))
        future_best = float(suffix_max[t + 1]) if t + 1 < n else price_t

        should_discharge = (t == n - 1) or (price_t >= future_best * 0.995)
        should_charge = (future_best * rt_eff) > price_t

        charge_cap = min(
            params.p_charge_max_mw,
            max(0.0, params.soc_max_mwh - state_soc) / params.eta_charge,
        )

        pv_charge = 0.0
        grid_charge = 0.0

        if not should_discharge and should_charge:
            pv_charge = min(charge_cap, pv_t)
            remaining = max(0.0, charge_cap - pv_charge)
            if params.allow_grid_charging and remaining > 0:
                grid_charge = remaining

        pv_after_charge = max(0.0, pv_t - pv_charge)
        discharge_cap = min(
            params.p_discharge_max_mw,
            max(0.0, state_soc - params.soc_min_mwh) * params.eta_discharge,
        )
        if params.grid_injection_limit_mw is not None:
            discharge_cap = min(
                discharge_cap,
                max(0.0, float(params.grid_injection_limit_mw) - pv_after_charge),
            )
        discharge = discharge_cap if should_discharge else 0.0

        state_soc = (
            state_soc
            + params.eta_charge * (pv_charge + grid_charge)
            - discharge / params.eta_discharge
        )
        state_soc = min(max(state_soc, params.soc_min_mwh), params.soc_max_mwh)

        charge_from_pv[t] = pv_charge
        charge_from_grid[t] = grid_charge
        discharge_to_grid[t] = discharge
        soc[t] = state_soc

    if params.enforce_terminal_soc:
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
            "charge_from_grid_mwh": charge_from_grid,
            "discharge_to_grid_mwh": discharge_to_grid,
            "soc_mwh": soc,
            "aux_losses_mwh": aux_losses_applied,
        }
    )
    return dispatch, {"status": "heuristic", "message": "greedy_lookahead_v2"}, warnings


def optimize_dispatch_hourly_v2(
    *,
    aligned_hourly_df: pd.DataFrame,
    battery_params: BatteryDispatchV2Parameters,
    prefer_lp: bool = True,
) -> DispatchOptimizationV2Result:
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
            )
            solver = "lp_highs"
        except Exception as exc:
            warnings.append(f"LP solver failed, fallback to heuristic solver: {exc}")
            dispatch, solver_meta, heuristic_warnings = _solve_with_greedy_heuristic(
                timestamps=timestamps,
                pv_mwh=pv,
                prices=prices,
                params=battery_params,
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
        )
        warnings.extend(heuristic_warnings)

    finalized, finalize_warnings = _finalize_dispatch_df(dispatch, params=battery_params)
    warnings.extend(finalize_warnings)
    kpis = _compute_kpis(finalized, params=battery_params)

    return DispatchOptimizationV2Result(
        dispatch_df=finalized,
        kpis=kpis,
        warnings=warnings,
        solver=solver,
        solver_status=f"{solver_meta.get('status', '')}: {solver_meta.get('message', '')}",
    )
