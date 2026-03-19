# core/production/hourly_analyzer.py
from __future__ import annotations

from typing import Callable, Dict, Tuple
import pandas as pd

from .hourly_models import AnalysisContext
from utils import check_required_columns, suggest_similar_columns

from .grid_limit import analyze_grid_limit
from .load_factor import analyze_load_factor


AnalysisFunc = Callable[[AnalysisContext], None]
ANALYSIS_REGISTRY: Dict[str, AnalysisFunc] = {}


def register_analysis(analysis_id: str, func: AnalysisFunc) -> None:
    ANALYSIS_REGISTRY[analysis_id] = func


def register_analyses() -> None:
    register_analysis("global_production", analyze_global_production)
    register_analysis("threshold", analyze_threshold)
    register_analysis("power_distribution", analyze_power_distribution)
    register_analysis("inverter_clipping", analyze_inverter_clipping)
    register_analysis("grid_limit", analyze_grid_limit)
    register_analysis("load_factor", analyze_load_factor)



def run_all_analyses(context: AnalysisContext) -> None:
    for func in ANALYSIS_REGISTRY.values():
        func(context)


def _month_map_en() -> dict[int, str]:
    return {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }


def _season_en(m: int) -> str:
    if m in (12, 1, 2):
        return "Winter"
    if m in (3, 4, 5):
        return "Spring"
    if m in (6, 7, 8):
        return "Summer"
    return "Autumn"


# =============================================================================
# Time step detection & integration helpers
# =============================================================================
def infer_timestep_hours(index: pd.DatetimeIndex) -> Tuple[float, dict]:
    """
    Detect dt (hours) from index deltas using median.
    Returns:
      dt_hours, meta
    meta includes:
      - n_deltas
      - dt_median_hours
      - dt_mode_hours (most frequent delta)
      - irregular_share (fraction of deltas != mode)
    """
    if index is None or len(index) < 2:
        return 1.0, {"n_deltas": 0, "irregular_share": 0.0, "dt_median_hours": 1.0, "dt_mode_hours": 1.0}

    diffs = index.to_series().diff().dropna()
    if diffs.empty:
        return 1.0, {"n_deltas": 0, "irregular_share": 0.0, "dt_median_hours": 1.0, "dt_mode_hours": 1.0}

    # convert to hours (float)
    hours = diffs.dt.total_seconds() / 3600.0
    dt_median = float(hours.median())

    # mode (most frequent) for irregularity estimate
    vc = hours.round(6).value_counts()
    dt_mode = float(vc.index[0]) if not vc.empty else dt_median
    irregular_share = float(1.0 - (vc.iloc[0] / vc.sum())) if vc.sum() > 0 else 0.0

    # safety clamp
    if dt_median <= 0 or not pd.notna(dt_median):
        dt_median = 1.0
    if dt_mode <= 0 or not pd.notna(dt_mode):
        dt_mode = dt_median

    # use mode if very dominant, else median
    dt = dt_mode if irregular_share < 0.10 else dt_median

    return float(dt), {
        "n_deltas": int(len(hours)),
        "dt_median_hours": dt_median,
        "dt_mode_hours": dt_mode,
        "irregular_share": irregular_share,
    }


def integrate_series_to_energy_kwh(s: pd.Series, unit: str, dt_hours: float) -> Tuple[float, str]:
    """
    Integrate a time series to kWh if it is power-like, or sum if already energy-like.

    Rules (best effort):
    - unit contains 'kW' (and not 'kWh'): treat as kW -> kWh = sum(kW)*dt_hours
    - unit contains 'W' (and not 'Wh'): treat as W -> kWh = sum(W)*dt_hours/1000
    - unit contains 'kWh': treat as kWh per step (PVSyst sometimes exports per step energy) -> kWh = sum
    - unit contains 'Wh': treat as Wh per step -> kWh = sum/1000
    - else: default assume "per step value" compatible with dt (treat like kW) -> sum*dt_hours
    Returns:
      value_kwh, "kWh"
    """
    u = (unit or "").strip()

    # ensure numeric
    s = pd.to_numeric(s, errors="coerce").fillna(0)

    if "kWh" in u:
        return float(s.sum()), "kWh"
    if "Wh" in u and "kWh" not in u:
        return float(s.sum()) / 1000.0, "kWh"
    if "kW" in u and "kWh" not in u:
        return float(s.sum()) * float(dt_hours), "kWh"
    if u == "W/m²" or "W/m" in u:
        # not an energy series
        return float("nan"), "kWh"

    if "W" in u and "Wh" not in u:
        return float(s.sum()) * float(dt_hours) / 1000.0, "kWh"

    # fallback (assume power-like)
    return float(s.sum()) * float(dt_hours), "kWh"


def _series_for_analysis(df: pd.DataFrame, col: str, night_disconnection: bool) -> pd.Series:
    s = df[col].copy()
    if night_disconnection:
        s = s.clip(lower=0)
    return s


# =============================================================================
# Global production summary
# =============================================================================
def analyze_global_production(context: AnalysisContext) -> None:
    df = context.df_raw
    col = context.options.threshold_column
    night_disconnection = bool(context.options.night_disconnection)

    if col not in df.columns:
        context.results["global_production"] = {
            "available": False,
            "missing_columns": [col],
            "suggestions": suggest_similar_columns(df.columns.tolist(), [col]),
        }
        return

    dt_hours, dt_meta = infer_timestep_hours(df.index)
    unit = str(context.units_map.get(col, "")).strip()

    s_raw = df[col].copy()
    s_for_prod = _series_for_analysis(df, col, night_disconnection=night_disconnection)

    # Operating time is based on series used for studies (after optional clamp)
    operating_steps = int((s_for_prod > 0).sum())
    total_steps = int(len(df))
    operating_hours = float(operating_steps) * dt_hours
    total_hours = float(total_steps) * dt_hours
    operating_pct = 100.0 * operating_hours / total_hours if total_hours > 0 else 0.0

    # Production without import: integrate positive part (RAW or clamped doesn't matter for positive)
    pos = s_raw.clip(lower=0)
    prod_without_import_kwh, _ = integrate_series_to_energy_kwh(pos, unit, dt_hours)

    # Net production includes negative import
    net_kwh, _ = integrate_series_to_energy_kwh(s_raw, unit, dt_hours)

    # Import (night consumption) = integrate negative part as positive energy
    neg = (-s_raw.clip(upper=0))
    import_kwh, _ = integrate_series_to_energy_kwh(neg, unit, dt_hours)
    import_steps = int((s_raw < 0).sum())
    import_hours = float(import_steps) * dt_hours

    context.results["global_production"] = {
        "available": True,
        "summary": {
            "column": col,
            "unit": unit,
            "dt_hours": dt_hours,
            "dt_meta": dt_meta,
            "night_disconnection": night_disconnection,

            "total_hours": total_hours,
            "operating_hours": operating_hours,
            "operating_pct": operating_pct,

            "production_without_import_kwh": prod_without_import_kwh,
            "net_production_kwh": net_kwh,

            "import_hours": import_hours,
            "night_consumption_kwh": import_kwh,
        },
    }


# =============================================================================
# Threshold analysis
# =============================================================================
def analyze_threshold(context: AnalysisContext) -> None:
    df = context.df_raw.copy()
    col = context.options.threshold_column
    thr = float(context.options.threshold_value)
    night_disconnection = bool(context.options.night_disconnection)

    if col not in df.columns:
        context.results["threshold"] = {
            "available": False,
            "missing_columns": [col],
            "suggestions": suggest_similar_columns(df.columns.tolist(), [col]),
        }
        return

    dt_hours, dt_meta = infer_timestep_hours(df.index)
    unit = str(context.units_map.get(col, "")).strip()

    s_raw = df[col].copy()
    s = _series_for_analysis(df, col, night_disconnection=night_disconnection)

    prod_mask = s > 0
    above_mask = s > thr

    hours_prod = float(int(prod_mask.sum())) * dt_hours
    hours_above = float(int(above_mask.sum())) * dt_hours
    pct_above_prod_time = 100.0 * hours_above / hours_prod if hours_prod > 0 else 0.0

    above_energy_kwh, _ = integrate_series_to_energy_kwh(s.where(above_mask, 0.0), unit, dt_hours)

    # Night consumption (from raw negative values)
    neg = (-s_raw.clip(upper=0))
    night_kwh, _ = integrate_series_to_energy_kwh(neg, unit, dt_hours)
    night_hours = float(int((s_raw < 0).sum())) * dt_hours

    summary = {
        "threshold_column": col,
        "threshold_value": thr,
        "unit": unit,
        "dt_hours": dt_hours,
        "dt_meta": dt_meta,
        "night_disconnection": night_disconnection,

        "operating_hours": hours_prod,
        "hours_above": hours_above,
        "pct_above_operating_time": pct_above_prod_time,
        "energy_above_kwh": above_energy_kwh,

        "night_import_hours": night_hours,
        "night_consumption_kwh": night_kwh,
    }

    month_map = _month_map_en()

    # Monthly above threshold (energy)
    df_above = df.loc[above_mask, :].copy()
    df_above["_value"] = s.loc[above_mask]

    df_above["month"] = df_above.index.month
    monthly = (
        df_above.groupby("month", observed=False)["_value"]
        .agg(steps_above="count", sum_value="sum")
        .reset_index()
    )
    monthly["month_name"] = monthly["month"].map(month_map)
    monthly["hours_above"] = monthly["steps_above"].astype(float) * dt_hours
    # integrate energy per month
    monthly["energy_above_kwh"] = monthly["sum_value"].astype(float) * dt_hours if ("kW" in unit and "kWh" not in unit) else monthly["sum_value"].astype(float)
    monthly = monthly[["month_name", "hours_above", "energy_above_kwh"]]

    # Seasonal
    df_above["season"] = df_above.index.month.map(_season_en)
    seasonal = (
        df_above.groupby("season", observed=False)["_value"]
        .agg(steps_above="count", sum_value="sum")
        .reset_index()
    )
    seasonal["hours_above"] = seasonal["steps_above"].astype(float) * dt_hours
    seasonal["energy_above_kwh"] = seasonal["sum_value"].astype(float) * dt_hours if ("kW" in unit and "kWh" not in unit) else seasonal["sum_value"].astype(float)
    seasonal = seasonal[["season", "hours_above", "energy_above_kwh"]]

    # Monthly share (based on operating hours)
    df_prod = df.loc[prod_mask, :].copy()
    df_prod["month"] = df_prod.index.month
    monthly_pct = (
        df_above.groupby("month", observed=False).size()
        / df_prod.groupby("month", observed=False).size()
        * 100
    ).fillna(0).reset_index(name="pct_above")
    monthly_pct["month_name"] = monthly_pct["month"].map(month_map)
    monthly_pct = monthly_pct[["month_name", "pct_above"]]

    # Night import monthly (energy)
    df_imp = df.loc[s_raw < 0, [col]].copy()
    if df_imp.empty:
        night_monthly = pd.DataFrame(columns=["month_name", "import_hours", "night_consumption_kwh"])
    else:
        df_imp["month"] = df_imp.index.month
        night_monthly = (
            df_imp.groupby("month", observed=False)[col]
            .agg(steps_import="count", sum_raw="sum")
            .reset_index()
        )
        night_monthly["month_name"] = night_monthly["month"].map(month_map)
        night_monthly["import_hours"] = night_monthly["steps_import"].astype(float) * dt_hours
        # negative sums -> convert to positive energy
        night_monthly["night_consumption_kwh"] = (-night_monthly["sum_raw"]).astype(float) * dt_hours if ("kW" in unit and "kWh" not in unit) else (-night_monthly["sum_raw"]).astype(float)
        night_monthly = night_monthly[["month_name", "import_hours", "night_consumption_kwh"]]

    context.results["threshold"] = {
        "available": True,
        "summary": summary,
        "monthly": monthly,
        "seasonal": seasonal,
        "monthly_pct": monthly_pct,
        "night_consumption_monthly": night_monthly,
    }


# =============================================================================
# Power distribution
# =============================================================================
def analyze_power_distribution(context: AnalysisContext) -> None:
    df = context.df_raw.copy()
    col = context.options.threshold_column
    night_disconnection = bool(context.options.night_disconnection)

    if col not in df.columns:
        context.results["power_distribution"] = {
            "available": False,
            "missing_columns": [col],
            "suggestions": suggest_similar_columns(df.columns.tolist(), [col]),
        }
        return

    dt_hours, dt_meta = infer_timestep_hours(df.index)
    unit = str(context.units_map.get(col, "")).strip()

    s = _series_for_analysis(df, col, night_disconnection=night_disconnection)
    s_prod = s[s > 0]
    if s_prod.empty:
        context.results["power_distribution"] = {"available": True, "empty": True}
        return

    v_max = float(s_prod.max())
    if v_max <= 0:
        context.results["power_distribution"] = {"available": True, "empty": True}
        return

    ratio = s_prod / v_max
    bins = [0, 0.5, 0.7, 0.9, 1.01]
    labels = ["< 50 %", "50–70 %", "70–90 %", "> 90 %"]
    cls = pd.cut(ratio, bins=bins, labels=labels)

    tmp = pd.DataFrame({"class": cls, "value": s_prod})
    summary = (
        tmp.groupby("class", observed=False)["value"]
        .agg(steps=("count"), sum_value=("sum"))
        .reset_index()
    )
    summary["hours"] = summary["steps"].astype(float) * dt_hours

    # Energy for each class (kWh)
    if "kW" in unit and "kWh" not in unit:
        summary["energy_kwh"] = summary["sum_value"].astype(float) * dt_hours
    else:
        summary["energy_kwh"] = summary["sum_value"].astype(float)

    summary["pct_time"] = summary["hours"] / summary["hours"].sum() * 100 if summary["hours"].sum() > 0 else 0.0

    context.results["power_distribution"] = {
        "available": True,
        "unit": unit,
        "dt_hours": dt_hours,
        "dt_meta": dt_meta,
        "max_value": v_max,
        "summary": summary[["class", "hours", "pct_time", "energy_kwh"]],
        "night_disconnection": night_disconnection,
    }


# =============================================================================
# Inverter clipping (unchanged logic, but dt can be added later if needed)
# =============================================================================
def analyze_inverter_clipping(context: AnalysisContext) -> None:
    df = context.df_raw.copy()
    required_cols = ["EOutInv", "IL_Pmax"]

    ok, missing = check_required_columns(df.columns.tolist(), required_cols)
    if not ok:
        context.results["inverter_clipping"] = {
            "available": False,
            "missing_columns": missing,
            "suggestions": suggest_similar_columns(df.columns.tolist(), missing),
        }
        return

    df = df[(df["EOutInv"] > 0) | (df["IL_Pmax"] > 0)].copy()
    if df.empty:
        context.results["inverter_clipping"] = {"available": True, "empty": True}
        return

    df["potential"] = df["EOutInv"] + df["IL_Pmax"]
    total_potential = float(df["potential"].sum())
    total_clipped = float(df["IL_Pmax"].sum())
    pct_clipping = 100.0 * total_clipped / total_potential if total_potential > 0 else 0.0
    hours_clipping = int((df["IL_Pmax"] > 0).sum())

    month_map = _month_map_en()
    df["month"] = df.index.month
    monthly = (
        df.groupby("month", observed=False)[["IL_Pmax", "potential"]]
        .sum()
        .reset_index()
    )
    monthly["month_name"] = monthly["month"].map(month_map)
    monthly["pct_clipping"] = (monthly["IL_Pmax"] / monthly["potential"] * 100).fillna(0)
    monthly = monthly[["month_name", "IL_Pmax", "pct_clipping"]]

    context.results["inverter_clipping"] = {
        "available": True,
        "summary": {
            "energy_clipped": total_clipped,
            "pct_of_potential": pct_clipping,
            "hours_clipping": hours_clipping,
        },
        "monthly": monthly,
    }
