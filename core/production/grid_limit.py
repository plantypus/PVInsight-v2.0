# core/production/grid_limit.py
from __future__ import annotations

from typing import Tuple, Optional
import pandas as pd

from .hourly_models import AnalysisContext
from utils import check_required_columns, suggest_similar_columns


# =============================================================================
# Helpers (local to avoid circular imports)
# =============================================================================
def _month_map_en() -> dict[int, str]:
    return {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }


def infer_timestep_hours(index: pd.DatetimeIndex) -> Tuple[float, dict]:
    if index is None or len(index) < 2:
        return 1.0, {"n_deltas": 0, "irregular_share": 0.0, "dt_median_hours": 1.0, "dt_mode_hours": 1.0}

    diffs = index.to_series().diff().dropna()
    if diffs.empty:
        return 1.0, {"n_deltas": 0, "irregular_share": 0.0, "dt_median_hours": 1.0, "dt_mode_hours": 1.0}

    hours = diffs.dt.total_seconds() / 3600.0
    dt_median = float(hours.median())

    vc = hours.round(6).value_counts()
    dt_mode = float(vc.index[0]) if not vc.empty else dt_median
    irregular_share = float(1.0 - (vc.iloc[0] / vc.sum())) if vc.sum() > 0 else 0.0

    if dt_median <= 0 or not pd.notna(dt_median):
        dt_median = 1.0
    if dt_mode <= 0 or not pd.notna(dt_mode):
        dt_mode = dt_median

    dt = dt_mode if irregular_share < 0.10 else dt_median

    return float(dt), {
        "n_deltas": int(len(hours)),
        "dt_median_hours": dt_median,
        "dt_mode_hours": dt_mode,
        "irregular_share": irregular_share,
    }


def integrate_series_to_energy_kwh(s: pd.Series, unit: str, dt_hours: float) -> Tuple[float, str]:
    """
    Best-effort integration to kWh.
    See hourly_analyzer.py for same logic.
    """
    u = (unit or "").strip()
    s = pd.to_numeric(s, errors="coerce").fillna(0)

    if "kWh" in u:
        return float(s.sum()), "kWh"
    if "Wh" in u and "kWh" not in u:
        return float(s.sum()) / 1000.0, "kWh"
    if "kW" in u and "kWh" not in u:
        return float(s.sum()) * float(dt_hours), "kWh"
    if u == "W/m²" or "W/m" in u:
        return float("nan"), "kWh"
    if "W" in u and "Wh" not in u:
        return float(s.sum()) * float(dt_hours) / 1000.0, "kWh"

    # fallback assume power-like per step
    return float(s.sum()) * float(dt_hours), "kWh"


def _as_optional_capacity_kw(context: AnalysisContext) -> Optional[float]:
    """
    Reads optional grid capacity from context.options if present.
    Will not crash if not defined in AnalysisOptions yet.
    """
    cap = getattr(context.options, "grid_capacity_kw", None)
    try:
        if cap is None:
            return None
        cap = float(cap)
        if cap <= 0:
            return None
        return cap
    except Exception:
        return None


def _to_power_kw(s: pd.Series, unit: str, dt_hours: float) -> pd.Series:
    """
    Convert a time series to power in kW (best-effort), assuming each row is one time step.
    Supported:
      - kW  -> unchanged
      - W   -> /1000
      - kWh -> /dt_hours
      - Wh  -> (/1000)/dt_hours
    Fallback: assume already kW-like.
    """
    u = (unit or "").strip()
    s = pd.to_numeric(s, errors="coerce").fillna(0.0)

    if dt_hours is None or dt_hours <= 0 or not pd.notna(dt_hours):
        dt_hours = 1.0

    if "kW" in u and "kWh" not in u:
        return s
    if ("kWh" in u) and ("kW" not in u):
        return s / float(dt_hours)
    if ("Wh" in u) and ("kWh" not in u):
        return (s / 1000.0) / float(dt_hours)
    if ("W" in u) and ("Wh" not in u):
        return s / 1000.0

    # fallback: assume power-like
    return s


# =============================================================================
# Main analysis
# =============================================================================
def analyze_grid_limit(context: AnalysisContext) -> None:
    """
    Grid limitation analysis.

    Preferred (measured) mode:
      - Requires EGrdLim + E_Grid
      - lost_kwh computed from EGrdLim (>=0)
      - injected_kwh computed from E_Grid (>=0)

    Intelligent fallback (estimated) mode:
      - If EGrdLim is missing AND grid_capacity_kw is provided:
        estimates losses by "capping" E_Grid at capacity (POI limitation assumption).
        This assumes E_Grid represents an unconstrained injection signal (or at least can exceed capacity).
        If E_Grid is already limited, estimated losses will be 0 (not observable).

    Outputs:
      context.results["grid_limit"] = {
        available, summary, monthly, monthly_load_factor
      }
    """
    df = context.df_raw
    cols = df.columns.tolist()

    # Always need E_Grid (baseline injection signal)
    required = ["E_Grid"]
    ok, missing = check_required_columns(cols, required)
    if not ok:
        context.results["grid_limit"] = {
            "available": False,
            "missing_columns": missing,
            "suggestions": suggest_similar_columns(cols, missing),
        }
        return

    dt_hours, dt_meta = infer_timestep_hours(df.index)

    # Units
    u_grid = str(context.units_map.get("E_Grid", "")).strip()
    u_lim = str(context.units_map.get("EGrdLim", "")).strip()

    # Series
    s_grid_raw = pd.to_numeric(df["E_Grid"], errors="coerce").fillna(0.0)

    # Only positive injection counts (ignore import / negative values)
    s_grid_pos = s_grid_raw.clip(lower=0.0)

    # Decide mode
    has_egrdlim = "EGrdLim" in cols
    cap_kw = _as_optional_capacity_kw(context)

    method = None  # "measured" | "estimated_from_capacity"
    note = None

    if has_egrdlim:
        # -----------------------------
        # MEASURED MODE (preferred)
        # -----------------------------
        method = "measured"
        s_lim_raw = pd.to_numeric(df["EGrdLim"], errors="coerce").fillna(0.0)

        lost_kwh, _ = integrate_series_to_energy_kwh(s_lim_raw.clip(lower=0.0), u_lim, dt_hours)
        injected_kwh, _ = integrate_series_to_energy_kwh(s_grid_pos, u_grid, dt_hours)

        hours_limited = float(int((s_lim_raw > 0).sum())) * dt_hours

        # Monthly breakdown (measured)
        tmp = df[["E_Grid", "EGrdLim"]].copy()
        tmp["month"] = tmp.index.month

        def _monthly_energy(series: pd.Series, unit: str) -> float:
            v, _ = integrate_series_to_energy_kwh(series, unit, dt_hours)
            return float(v)

        monthly_lost = (
            tmp.groupby("month", observed=False)["EGrdLim"]
            .apply(lambda s: _monthly_energy(pd.to_numeric(s, errors="coerce").fillna(0.0).clip(lower=0.0), u_lim))
            .reset_index(name="lost_kwh")
        )
        monthly_inj = (
            tmp.groupby("month", observed=False)["E_Grid"]
            .apply(lambda s: _monthly_energy(pd.to_numeric(s, errors="coerce").fillna(0.0).clip(lower=0.0), u_grid))
            .reset_index(name="injected_kwh")
        )

        monthly_hours_limited = (
            tmp.groupby("month", observed=False)["EGrdLim"]
            .apply(lambda s: float(int((pd.to_numeric(s, errors="coerce").fillna(0.0) > 0).sum())) * dt_hours)
            .reset_index(name="hours_limited")
        )

    else:
        # -----------------------------
        # ESTIMATED MODE (fallback)
        # -----------------------------
        if cap_kw is None:
            # No measured losses and no capacity to estimate -> not available
            context.results["grid_limit"] = {
                "available": False,
                "missing_columns": ["EGrdLim"],
                "suggestions": suggest_similar_columns(cols, ["EGrdLim"]),
            }
            return

        method = "estimated_from_capacity"
        note = "estimated_losses_from_capacity"

        # Convert E_Grid to power in kW (best-effort), then cap at capacity
        p_grid_kw = _to_power_kw(s_grid_pos, u_grid, dt_hours)
        p_inj_kw = p_grid_kw.clip(upper=float(cap_kw))
        p_lost_kw = (p_grid_kw - float(cap_kw)).clip(lower=0.0)

        # Integrate in kWh using kW * dt
        lost_kwh, _ = integrate_series_to_energy_kwh(p_lost_kw, "kW", dt_hours)
        injected_kwh, _ = integrate_series_to_energy_kwh(p_inj_kw, "kW", dt_hours)

        hours_limited = float(int((p_lost_kw > 0).sum())) * dt_hours

        # Monthly breakdown (estimated)
        tmp = pd.DataFrame(
            {
                "P_inj_kW": p_inj_kw,
                "P_lost_kW": p_lost_kw,
            },
            index=df.index,
        )
        tmp["month"] = tmp.index.month

        def _monthly_energy_kw(series_kw: pd.Series) -> float:
            v, _ = integrate_series_to_energy_kwh(pd.to_numeric(series_kw, errors="coerce").fillna(0.0), "kW", dt_hours)
            return float(v)

        monthly_lost = (
            tmp.groupby("month", observed=False)["P_lost_kW"]
            .apply(lambda s: _monthly_energy_kw(s))
            .reset_index(name="lost_kwh")
        )
        monthly_inj = (
            tmp.groupby("month", observed=False)["P_inj_kW"]
            .apply(lambda s: _monthly_energy_kw(s))
            .reset_index(name="injected_kwh")
        )

        monthly_hours_limited = (
            tmp.groupby("month", observed=False)["P_lost_kW"]
            .apply(lambda s: float(int((pd.to_numeric(s, errors="coerce").fillna(0.0) > 0).sum())) * dt_hours)
            .reset_index(name="hours_limited")
        )

    # Common annual metrics
    potential_kwh = float(injected_kwh) + float(lost_kwh)
    lost_pct = 100.0 * float(lost_kwh) / potential_kwh if potential_kwh > 0 else 0.0
    total_hours = float(len(df)) * dt_hours

    # Merge monthly tables (common)
    month_map = _month_map_en()
    monthly = monthly_lost.merge(monthly_inj, on="month", how="outer").fillna(0.0)
    monthly["potential_kwh"] = monthly["lost_kwh"] + monthly["injected_kwh"]
    monthly["lost_pct"] = monthly.apply(
        lambda r: (100.0 * r["lost_kwh"] / r["potential_kwh"]) if r["potential_kwh"] > 0 else 0.0, axis=1
    )
    monthly = monthly.merge(monthly_hours_limited, on="month", how="left").fillna(0.0)
    monthly["month_name"] = monthly["month"].map(month_map)
    monthly = monthly[["month_name", "lost_kwh", "lost_pct", "hours_limited", "injected_kwh"]]

    # Optional: load factor from capacity (works for both modes; injected_kwh is "actual injected" in each mode)
    annual_lf = None
    monthly_lf = None
    if cap_kw is not None and total_hours > 0:
        annual_lf = float(injected_kwh) / (float(cap_kw) * float(total_hours))  # unitless

        # compute hours per month (robust: uses tmp["month"])
        month_hours = (
            tmp.groupby("month", observed=False)
            .size()
            .reset_index(name="steps")
        )
        month_hours["hours"] = month_hours["steps"].astype(float) * dt_hours

        monthly_lf = (
            monthly_inj.merge(month_hours, on="month", how="left")
            .fillna(0.0)
        )
        monthly_lf["load_factor"] = monthly_lf.apply(
            lambda r: (r["injected_kwh"] / (float(cap_kw) * r["hours"])) if r["hours"] > 0 else 0.0, axis=1
        )
        monthly_lf["month_name"] = monthly_lf["month"].map(month_map)
        monthly_lf = monthly_lf[["month_name", "load_factor", "injected_kwh"]]

    context.results["grid_limit"] = {
        "available": True,
        "summary": {
            "method": method,
            "note": note,  # i18n key (optional), e.g. "estimated_losses_from_capacity"
            "dt_hours": dt_hours,
            "dt_meta": dt_meta,
            "lost_kwh": float(lost_kwh),
            "injected_kwh": float(injected_kwh),
            "potential_kwh": float(potential_kwh),
            "lost_pct": float(lost_pct),
            "hours_limited": float(hours_limited),
            "total_hours": float(total_hours),
            "grid_capacity_kw": cap_kw,
            "annual_load_factor": float(annual_lf) if annual_lf is not None else None,
        },
        "monthly": monthly,
        "monthly_load_factor": monthly_lf,
    }
