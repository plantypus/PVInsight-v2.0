# core/production/load_factor.py
from __future__ import annotations

import math
from typing import Optional, Tuple

import pandas as pd

from .hourly_models import AnalysisContext
from utils import suggest_similar_columns


# =============================================================================
# Helpers (local to avoid circular imports)
# =============================================================================
def _month_map_en() -> dict[int, str]:
    return {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }


def infer_timestep_hours(index: pd.DatetimeIndex) -> Tuple[float, dict]:
    if index is None or len(index) < 2:
        return 1.0, {
            "n_deltas": 0,
            "irregular_share": 0.0,
            "dt_median_hours": 1.0,
            "dt_mode_hours": 1.0,
        }

    diffs = index.to_series().diff().dropna()
    if diffs.empty:
        return 1.0, {
            "n_deltas": 0,
            "irregular_share": 0.0,
            "dt_median_hours": 1.0,
            "dt_mode_hours": 1.0,
        }

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

    return float(s.sum()) * float(dt_hours), "kWh"


def _to_power_kw(s: pd.Series, unit: str, dt_hours: float) -> pd.Series:
    """
    Convert a time series to power in kW (best-effort), assuming each row is one time step.
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

    return s


def _safe_pct(num: float | int | None, den: float | int | None) -> float:
    try:
        num_f = float(num)
        den_f = float(den)
        if den_f <= 0:
            return 0.0
        return 100.0 * num_f / den_f
    except Exception:
        return 0.0


def _as_optional_capacity_kw(context: AnalysisContext) -> Optional[float]:
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


# =============================================================================
# Main analysis
# =============================================================================
def analyze_load_factor(context: AnalysisContext) -> None:
    """
    Active / reactive network analysis with:
      - Full mode when EApGrid + EReGrid are available.
      - Complementary tan(phi) analysis always when E_Grid is available.

    Complementary tan(phi) analysis assumptions:
      - Reference declared injection power is used as the baseline apparent-capacity-like value.
      - If user provided grid_capacity_kw, this is used as reference.
      - Otherwise, observed active peak is used.
      - Cases analyzed: tan(phi)=0.25 (best) and tan(phi)=0.35 (worst).
    """
    df = context.df_raw
    cols = df.columns.tolist()

    has_ap = "EApGrid" in cols
    has_re = "EReGrid" in cols
    has_sq = has_ap and has_re
    has_p = "E_Grid" in cols

    if (not has_sq) and (not has_p):
        missing = [c for c in ["E_Grid", "EApGrid", "EReGrid"] if c not in cols]
        context.results["load_factor"] = {
            "available": False,
            "missing_columns": missing,
            "suggestions": suggest_similar_columns(cols, missing),
        }
        return

    dt_hours, dt_meta = infer_timestep_hours(df.index)
    total_hours = float(len(df)) * dt_hours
    cap_kw = _as_optional_capacity_kw(context)

    # Units
    u_s = str(context.units_map.get("EApGrid", "")).strip() if has_ap else ""
    u_q = str(context.units_map.get("EReGrid", "")).strip() if has_re else ""
    u_p = str(context.units_map.get("E_Grid", "")).strip() if has_p else ""

    # Series numeric
    s_ap = pd.to_numeric(df["EApGrid"], errors="coerce").fillna(0.0) if has_ap else None
    s_re = pd.to_numeric(df["EReGrid"], errors="coerce").fillna(0.0) if has_re else None
    s_p = pd.to_numeric(df["E_Grid"], errors="coerce").fillna(0.0) if has_p else None

    # Integrations (kWh as common reference unit)
    s_kwh = None
    q_kwh = None
    if s_ap is not None:
        s_kwh, _ = integrate_series_to_energy_kwh(s_ap, u_s, dt_hours)  # kVAh-like
    if s_re is not None:
        q_kwh, _ = integrate_series_to_energy_kwh(s_re, u_q, dt_hours)  # kvarh-like

    p_kwh = None
    p_pos = None
    if s_p is not None:
        p_pos = s_p.clip(lower=0.0)
        p_kwh, _ = integrate_series_to_energy_kwh(p_pos, u_p, dt_hours)

    # Annual indicators from integrated energies
    cosphi = None
    if p_kwh is not None and s_kwh is not None and s_kwh > 0:
        cosphi = float(p_kwh / s_kwh)

    q_share = None
    if q_kwh is not None and s_kwh is not None and s_kwh > 0:
        q_share = float(q_kwh / s_kwh)

    active_loss_due_pf_kwh = None
    active_loss_due_pf_pct = None
    if p_kwh is not None and s_kwh is not None and s_kwh > 0:
        active_loss_due_pf_kwh = max(float(s_kwh) - float(p_kwh), 0.0)
        active_loss_due_pf_pct = _safe_pct(active_loss_due_pf_kwh, s_kwh)

    # Monthly table
    tmp_cols = []
    if has_ap:
        tmp_cols.append("EApGrid")
    if has_re:
        tmp_cols.append("EReGrid")
    if has_p:
        tmp_cols.append("E_Grid")

    tmp = df[tmp_cols].copy()
    tmp["month"] = tmp.index.month
    month_map = _month_map_en()

    months = sorted(tmp["month"].dropna().astype(int).unique().tolist()) if not tmp.empty else []
    monthly = pd.DataFrame({"month": months}) if months else pd.DataFrame(columns=["month"])

    def _sum_energy(colname: str, unit: str, clamp_pos: bool = False) -> pd.Series:
        series = pd.to_numeric(tmp[colname], errors="coerce").fillna(0.0)
        if clamp_pos:
            series = series.clip(lower=0.0)
        grouped = pd.DataFrame({"month": tmp["month"], "value": series})
        return grouped.groupby("month", observed=False)["value"].apply(
            lambda s: integrate_series_to_energy_kwh(s, unit, dt_hours)[0]
        )

    if has_sq:
        monthly_s = _sum_energy("EApGrid", u_s, clamp_pos=True).reset_index(name="S_kWh_equiv")
        monthly_q = _sum_energy("EReGrid", u_q, clamp_pos=False).reset_index(name="Q_kWh_equiv")
        monthly = monthly.merge(monthly_s, on="month", how="outer")
        monthly = monthly.merge(monthly_q, on="month", how="outer")

    if has_p:
        monthly_p = _sum_energy("E_Grid", u_p, clamp_pos=True).reset_index(name="P_kWh")
        monthly = monthly.merge(monthly_p, on="month", how="outer")

    for c in ["S_kWh_equiv", "Q_kWh_equiv", "P_kWh"]:
        if c in monthly.columns:
            monthly[c] = pd.to_numeric(monthly[c], errors="coerce").fillna(0.0)

    if has_sq and "S_kWh_equiv" in monthly.columns and "Q_kWh_equiv" in monthly.columns:
        monthly["q_share"] = monthly.apply(
            lambda r: (r["Q_kWh_equiv"] / r["S_kWh_equiv"]) if r["S_kWh_equiv"] > 0 else 0.0,
            axis=1,
        )
    else:
        monthly["q_share"] = None

    monthly["month_name"] = monthly["month"].map(month_map) if "month" in monthly.columns else None

    monthly_cols = ["month_name"]
    if "S_kWh_equiv" in monthly.columns:
        monthly_cols.append("S_kWh_equiv")
    if "Q_kWh_equiv" in monthly.columns:
        monthly_cols.append("Q_kWh_equiv")
    if "P_kWh" in monthly.columns:
        monthly_cols.append("P_kWh")
    monthly_cols.append("q_share")

    if monthly.empty:
        monthly_out = pd.DataFrame(columns=monthly_cols)
    else:
        monthly_out = monthly[monthly_cols]

    # Relative saturation (based on EApGrid instantaneous values)
    if s_ap is not None:
        s_ap_pos = s_ap.clip(lower=0.0)
        s_max = float(s_ap_pos.max()) if not s_ap_pos.empty else 0.0
        if s_max > 0:
            ratio = s_ap_pos / s_max
            bins = [0, 0.5, 0.7, 0.9, 1.01]
            labels = ["< 50 %", "50-70 %", "70-90 %", "> 90 %"]
            cls = pd.cut(ratio, bins=bins, labels=labels)
            dist = pd.DataFrame({"class": cls}).groupby("class", observed=False).size().reset_index(name="steps")
            dist["hours"] = dist["steps"].astype(float) * dt_hours
            dist["pct_time"] = dist["hours"] / dist["hours"].sum() * 100 if dist["hours"].sum() > 0 else 0.0
        else:
            dist = pd.DataFrame(columns=["class", "steps", "hours", "pct_time"])
    else:
        s_max = 0.0
        dist = pd.DataFrame(columns=["class", "steps", "hours", "pct_time"])

    # Complementary tan(phi) analysis (always with E_Grid).
    tanphi_rows: list[dict] = []
    active_peak_kw_observed = None
    baseline_energy_no_pf_kwh = None
    reference_declared_power_kw = None
    reference_declared_power_source = None

    if p_pos is not None:
        p_pos_kw = _to_power_kw(p_pos, u_p, dt_hours).clip(lower=0.0)
        active_peak_kw_observed = float(p_pos_kw.max()) if not p_pos_kw.empty else 0.0

        if cap_kw is not None and cap_kw > 0:
            reference_declared_power_kw = float(cap_kw)
            reference_declared_power_source = "grid_capacity_input"
        else:
            reference_declared_power_kw = float(active_peak_kw_observed)
            reference_declared_power_source = "observed_active_peak"

        p_no_pf_kw = p_pos_kw.clip(upper=float(reference_declared_power_kw))
        baseline_energy_no_pf_kwh, _ = integrate_series_to_energy_kwh(p_no_pf_kw, "kW", dt_hours)
        baseline_peak_no_pf_kw = float(p_no_pf_kw.max()) if not p_no_pf_kw.empty else 0.0

        for case_name, tanphi in [("best", 0.25), ("worst", 0.35)]:
            cosphi_case = 1.0 / math.sqrt(1.0 + tanphi * tanphi)
            active_limit_kw = float(reference_declared_power_kw) * float(cosphi_case)

            p_with_tan_kw = p_no_pf_kw.clip(upper=active_limit_kw)
            lost_kw = (p_no_pf_kw - p_with_tan_kw).clip(lower=0.0)
            lost_kwh, _ = integrate_series_to_energy_kwh(lost_kw, "kW", dt_hours)
            lost_pct = _safe_pct(lost_kwh, baseline_energy_no_pf_kwh)
            # Minimum active power to declare so the tan(phi) constraint does not reduce
            # the baseline (no power-factor-constraint) production profile.
            min_declared_active_mw_no_impact = float(baseline_peak_no_pf_kw) / 1000.0

            tanphi_rows.append(
                {
                    "case": case_name,
                    "tanphi": float(tanphi),
                    "cosphi": float(cosphi_case),
                    "active_limit_kw": float(active_limit_kw),
                    "active_limit_mw": float(active_limit_kw) / 1000.0,
                    "lost_kwh": float(lost_kwh),
                    "lost_pct_vs_no_pf": float(lost_pct),
                    "min_declared_active_mw_no_impact": float(min_declared_active_mw_no_impact),
                }
            )

    tanphi_scenarios = pd.DataFrame(
        tanphi_rows,
        columns=[
            "case",
            "tanphi",
            "cosphi",
            "active_limit_kw",
            "active_limit_mw",
            "lost_kwh",
            "lost_pct_vs_no_pf",
            "min_declared_active_mw_no_impact",
        ],
    )

    # Optional: load factor from declared capacity
    annual_lf = None
    monthly_lf = None
    if cap_kw is not None and total_hours > 0 and p_kwh is not None:
        annual_lf = float(p_kwh / (cap_kw * total_hours))

        month_hours = tmp.groupby("month", observed=False).size().reset_index(name="steps")
        month_hours["hours"] = month_hours["steps"].astype(float) * dt_hours

        if "P_kWh" in monthly.columns:
            monthly_lf = monthly.merge(month_hours, on="month", how="left").fillna(0.0)
            monthly_lf["load_factor"] = monthly_lf.apply(
                lambda r: (r["P_kWh"] / (cap_kw * r["hours"])) if (r["hours"] > 0 and r["P_kWh"] is not None) else 0.0,
                axis=1,
            )
            monthly_lf = monthly_lf[["month_name", "load_factor", "P_kWh"]]

    context.results["load_factor"] = {
        "available": True,
        "summary": {
            "dt_hours": dt_hours,
            "dt_meta": dt_meta,
            "total_hours": total_hours,
            "grid_capacity_kw": cap_kw,
            "has_full_reactive_data": bool(has_sq),
            "S_kWh_equiv": float(s_kwh) if s_kwh is not None else None,
            "Q_kWh_equiv": float(q_kwh) if q_kwh is not None else None,
            "P_kWh": float(p_kwh) if p_kwh is not None else None,
            "cosphi": float(cosphi) if cosphi is not None else None,
            "q_share": float(q_share) if q_share is not None else None,
            "active_loss_due_pf_kwh": float(active_loss_due_pf_kwh) if active_loss_due_pf_kwh is not None else None,
            "active_loss_due_pf_pct": float(active_loss_due_pf_pct) if active_loss_due_pf_pct is not None else None,
            "active_peak_kw_observed": float(active_peak_kw_observed) if active_peak_kw_observed is not None else None,
            "baseline_energy_no_pf_kwh": float(baseline_energy_no_pf_kwh) if baseline_energy_no_pf_kwh is not None else None,
            "reference_declared_power_kw": float(reference_declared_power_kw) if reference_declared_power_kw is not None else None,
            "reference_declared_power_source": reference_declared_power_source,
            "annual_load_factor": float(annual_lf) if annual_lf is not None else None,
            "S_max": float(s_max),
        },
        "monthly": monthly_out,
        "saturation_distribution": dist,
        "monthly_load_factor": monthly_lf,
        "tanphi_scenarios": tanphi_scenarios,
    }
