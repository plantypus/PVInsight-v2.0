# core/production/load_factor.py
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
    Network load / power factor analysis based on:
      - EApGrid: apparent energy injected (kVAh-like)
      - EReGrid: reactive energy injected (kvarh-like)
    Optional:
      - E_Grid  : active energy injected (kWh-like) to compute cos(phi) = P/S

    If grid_capacity_kw is provided (optional), computes annual & monthly load factor:
      LF = P_kWh / (Pcap_kW * total_hours)
    (Best effort: assumes capacity is compatible with the active series.)
    """
    df = context.df_raw
    cols = df.columns.tolist()

    # Minimal required for this module:
    required = ["EApGrid", "EReGrid"]
    ok, missing = check_required_columns(cols, required)
    if not ok:
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
    u_s = str(context.units_map.get("EApGrid", "")).strip()
    u_q = str(context.units_map.get("EReGrid", "")).strip()
    u_p = str(context.units_map.get("E_Grid", "")).strip() if "E_Grid" in cols else ""

    # Series numeric
    s_ap = pd.to_numeric(df["EApGrid"], errors="coerce").fillna(0.0)
    s_re = pd.to_numeric(df["EReGrid"], errors="coerce").fillna(0.0)
    s_p = pd.to_numeric(df["E_Grid"], errors="coerce").fillna(0.0) if "E_Grid" in cols else None

    # Integrations (kWh as common reference unit)
    s_kwh, _ = integrate_series_to_energy_kwh(s_ap, u_s, dt_hours)  # actually kVAh, but normalized to kWh-scale
    q_kwh, _ = integrate_series_to_energy_kwh(s_re, u_q, dt_hours)  # kvarh-like
    p_kwh = None
    if s_p is not None:
        p_pos = s_p.clip(lower=0.0)
        p_kwh, _ = integrate_series_to_energy_kwh(p_pos, u_p, dt_hours)

    # "Energy power factor" (best effort)
    cosphi = None
    if p_kwh is not None and s_kwh and s_kwh > 0:
        cosphi = float(p_kwh / s_kwh)

    q_share = None
    if s_kwh and s_kwh > 0:
        q_share = float(q_kwh / s_kwh)

    # Monthly tables
    month_map = _month_map_en()
    tmp = df[required + (["E_Grid"] if "E_Grid" in cols else [])].copy()
    tmp["month"] = tmp.index.month

    def _sum_energy(colname: str, unit: str, clamp_pos: bool = False) -> pd.Series:
        ser = pd.to_numeric(tmp[colname], errors="coerce").fillna(0.0)
        if clamp_pos:
            ser = ser.clip(lower=0.0)
        # group apply integration per month
        return tmp.groupby("month", observed=False)[colname].apply(
            lambda s: integrate_series_to_energy_kwh(
                pd.to_numeric(s, errors="coerce").fillna(0.0).clip(lower=0.0) if clamp_pos else pd.to_numeric(s, errors="coerce").fillna(0.0),
                unit,
                dt_hours,
            )[0]
        )

    monthly_s = _sum_energy("EApGrid", u_s, clamp_pos=True).reset_index(name="S_kWh_equiv")
    monthly_q = _sum_energy("EReGrid", u_q, clamp_pos=False).reset_index(name="Q_kWh_equiv")

    monthly = monthly_s.merge(monthly_q, on="month", how="outer").fillna(0.0)

    if "E_Grid" in cols:
        monthly_p = _sum_energy("E_Grid", u_p, clamp_pos=True).reset_index(name="P_kWh")
        monthly = monthly.merge(monthly_p, on="month", how="left").fillna(0.0)
        monthly["cosphi"] = monthly.apply(lambda r: (r["P_kWh"] / r["S_kWh_equiv"]) if r["S_kWh_equiv"] > 0 else 0.0, axis=1)
    else:
        monthly["P_kWh"] = None
        monthly["cosphi"] = None

    monthly["q_share"] = monthly.apply(lambda r: (r["Q_kWh_equiv"] / r["S_kWh_equiv"]) if r["S_kWh_equiv"] > 0 else 0.0, axis=1)
    monthly["month_name"] = monthly["month"].map(month_map)

    # Relative saturation (based on EApGrid instantaneous values)
    s_ap_pos = s_ap.clip(lower=0.0)
    s_max = float(s_ap_pos.max()) if not s_ap_pos.empty else 0.0
    if s_max > 0:
        ratio = s_ap_pos / s_max
        bins = [0, 0.5, 0.7, 0.9, 1.01]
        labels = ["< 50 %", "50–70 %", "70–90 %", "> 90 %"]
        cls = pd.cut(ratio, bins=bins, labels=labels)
        dist = pd.DataFrame({"class": cls}).groupby("class", observed=False).size().reset_index(name="steps")
        dist["hours"] = dist["steps"].astype(float) * dt_hours
        dist["pct_time"] = dist["hours"] / dist["hours"].sum() * 100 if dist["hours"].sum() > 0 else 0.0
    else:
        dist = pd.DataFrame(columns=["class", "steps", "hours", "pct_time"])

    # Optional: load factor based on capacity
    annual_lf = None
    monthly_lf = None
    if cap_kw is not None and total_hours > 0 and p_kwh is not None:
        annual_lf = float(p_kwh / (cap_kw * total_hours))

        # hours per month
        month_hours = tmp.groupby("month", observed=False).size().reset_index(name="steps")
        month_hours["hours"] = month_hours["steps"].astype(float) * dt_hours

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

            "S_kWh_equiv": float(s_kwh),
            "Q_kWh_equiv": float(q_kwh),
            "P_kWh": float(p_kwh) if p_kwh is not None else None,
            "cosphi": float(cosphi) if cosphi is not None else None,
            "q_share": float(q_share) if q_share is not None else None,

            "annual_load_factor": float(annual_lf) if annual_lf is not None else None,
            "S_max": float(s_max),
        },
        "monthly": monthly[["month_name", "S_kWh_equiv", "Q_kWh_equiv", "P_kWh", "cosphi", "q_share"]],
        "saturation_distribution": dist,
        "monthly_load_factor": monthly_lf,
    }
