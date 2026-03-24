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
    ANALYSIS_REGISTRY.clear()
    register_analysis("global_production", analyze_global_production)
    register_analysis("threshold", analyze_threshold)
    register_analysis("power_distribution", analyze_power_distribution)
    register_analysis("inverter_clipping", analyze_inverter_clipping)
    register_analysis("grid_limit", analyze_grid_limit)
    register_analysis("load_factor", analyze_load_factor)
    register_analysis("performance_monthly", analyze_performance_monthly)
    register_analysis("system_summary", analyze_system_summary)


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
# Helpers
# =============================================================================
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
    s = pd.to_numeric(s, errors="coerce").fillna(0.0)

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


def integrate_irradiance_to_kwh_m2(s: pd.Series, unit: str, dt_hours: float) -> float:
    u = (unit or "").strip()
    s = pd.to_numeric(s, errors="coerce").fillna(0.0)

    if "W/m²" in u or "W/m2" in u:
        return float(s.sum()) * float(dt_hours) / 1000.0
    if "kWh/m²" in u or "kWh/m2" in u:
        return float(s.sum())
    if "Wh/m²" in u or "Wh/m2" in u:
        return float(s.sum()) / 1000.0

    return float(s.sum()) * float(dt_hours) / 1000.0


def _safe_pct(num: float | int | None, den: float | int | None) -> float:
    try:
        num_f = float(num)
        den_f = float(den)
        if den_f <= 0:
            return 0.0
        return 100.0 * num_f / den_f
    except Exception:
        return 0.0


def _series_for_analysis(df: pd.DataFrame, col: str, night_disconnection: bool) -> pd.Series:
    s = pd.to_numeric(df[col], errors="coerce").fillna(0.0).copy()
    if night_disconnection:
        s = s.clip(lower=0)
    return s


def _positive_production_mask(df: pd.DataFrame, ref_col: str = "E_Grid") -> pd.Series:
    if ref_col in df.columns:
        return pd.to_numeric(df[ref_col], errors="coerce").fillna(0.0) > 0
    return pd.Series(False, index=df.index)


# =============================================================================
# Global production
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

    s_raw = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    s_for_prod = _series_for_analysis(df, col, night_disconnection=night_disconnection)

    operating_steps = int((s_for_prod > 0).sum())
    total_steps = int(len(df))
    operating_hours = float(operating_steps) * dt_hours
    total_hours = float(total_steps) * dt_hours
    operating_pct = 100.0 * operating_hours / total_hours if total_hours > 0 else 0.0

    pos = s_raw.clip(lower=0)
    prod_without_import_kwh, _ = integrate_series_to_energy_kwh(pos, unit, dt_hours)

    net_kwh, _ = integrate_series_to_energy_kwh(s_raw, unit, dt_hours)

    neg = (-s_raw.clip(upper=0))
    import_kwh, _ = integrate_series_to_energy_kwh(neg, unit, dt_hours)
    import_steps = int((s_raw < 0).sum())
    import_hours = float(import_steps) * dt_hours

    # PR annual mean on positive-production hours only
    pr_mean_prod = None
    if "PR" in df.columns:
        prod_mask = _positive_production_mask(df, "E_Grid")
        pr_s = pd.to_numeric(df["PR"], errors="coerce")
        pr_s = pr_s.where(prod_mask)
        if pr_s.notna().any():
            pr_mean_prod = float(pr_s.mean())

    context.results["global_production"] = {
        "available": True,
        "summary": {
            "column": col,
            "unit": unit,
            "dt_hours": float(dt_hours),
            "dt_meta": dt_meta,
            "night_disconnection": night_disconnection,
            "total_hours": float(total_hours),
            "operating_hours": float(operating_hours),
            "operating_pct": float(operating_pct),
            "production_without_import_kwh": float(prod_without_import_kwh),
            "net_production_kwh": float(net_kwh),
            "import_hours": float(import_hours),
            "night_consumption_kwh": float(import_kwh),
            "pr_mean": pr_mean_prod,
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

    s_raw = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    s = _series_for_analysis(df, col, night_disconnection=night_disconnection)

    prod_mask = s > 0
    above_mask = s > thr

    hours_prod = float(int(prod_mask.sum())) * dt_hours
    hours_above = float(int(above_mask.sum())) * dt_hours
    pct_above_prod_time = 100.0 * hours_above / hours_prod if hours_prod > 0 else 0.0

    above_energy_kwh, _ = integrate_series_to_energy_kwh(s.where(above_mask, 0.0), unit, dt_hours)

    neg = (-s_raw.clip(upper=0))
    night_kwh, _ = integrate_series_to_energy_kwh(neg, unit, dt_hours)
    night_hours = float(int((s_raw < 0).sum())) * dt_hours

    summary = {
        "threshold_column": col,
        "threshold_value": float(thr),
        "unit": unit,
        "dt_hours": float(dt_hours),
        "dt_meta": dt_meta,
        "night_disconnection": night_disconnection,
        "operating_hours": float(hours_prod),
        "hours_above": float(hours_above),
        "pct_above_operating_time": float(pct_above_prod_time),
        "energy_above_kwh": float(above_energy_kwh),
        "night_import_hours": float(night_hours),
        "night_consumption_kwh": float(night_kwh),
    }

    month_map = _month_map_en()

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
    monthly["energy_above_kwh"] = monthly["sum_value"].astype(float).map(
        lambda v: float(v) * dt_hours if ("kW" in unit and "kWh" not in unit) else float(v)
    )
    monthly = monthly[["month_name", "hours_above", "energy_above_kwh"]]

    df_above["season"] = df_above.index.month.map(_season_en)
    seasonal = (
        df_above.groupby("season", observed=False)["_value"]
        .agg(steps_above="count", sum_value="sum")
        .reset_index()
    )
    seasonal["hours_above"] = seasonal["steps_above"].astype(float) * dt_hours
    seasonal["energy_above_kwh"] = seasonal["sum_value"].astype(float).map(
        lambda v: float(v) * dt_hours if ("kW" in unit and "kWh" not in unit) else float(v)
    )
    seasonal = seasonal[["season", "hours_above", "energy_above_kwh"]]

    df_prod = df.loc[prod_mask, :].copy()
    df_prod["month"] = df_prod.index.month
    monthly_pct = (
        df_above.groupby("month", observed=False).size()
        / df_prod.groupby("month", observed=False).size()
        * 100
    ).fillna(0).reset_index(name="pct_above")
    monthly_pct["month_name"] = monthly_pct["month"].map(month_map)
    monthly_pct = monthly_pct[["month_name", "pct_above"]]

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
        night_monthly["night_consumption_kwh"] = (-night_monthly["sum_raw"]).astype(float).map(
            lambda v: float(v) * dt_hours if ("kW" in unit and "kWh" not in unit) else float(v)
        )
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

    if "kW" in unit and "kWh" not in unit:
        summary["energy_kwh"] = summary["sum_value"].astype(float) * dt_hours
    else:
        summary["energy_kwh"] = summary["sum_value"].astype(float)

    summary["pct_time"] = summary["hours"] / summary["hours"].sum() * 100 if summary["hours"].sum() > 0 else 0.0

    context.results["power_distribution"] = {
        "available": True,
        "unit": unit,
        "dt_hours": float(dt_hours),
        "dt_meta": dt_meta,
        "max_value": float(v_max),
        "summary": summary[["class", "hours", "pct_time", "energy_kwh"]],
        "night_disconnection": night_disconnection,
    }


# =============================================================================
# Inverter clipping
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

    dt_hours, dt_meta = infer_timestep_hours(df.index)

    u_out = str(context.units_map.get("EOutInv", "")).strip()
    u_clip = str(context.units_map.get("IL_Pmax", "")).strip()
    u_egrid = str(context.units_map.get("E_Grid", "")).strip() if "E_Grid" in df.columns else ""

    df["EOutInv"] = pd.to_numeric(df["EOutInv"], errors="coerce").fillna(0.0)
    df["IL_Pmax"] = pd.to_numeric(df["IL_Pmax"], errors="coerce").fillna(0.0)

    if "E_Grid" in df.columns:
        egrid_pos = pd.to_numeric(df["E_Grid"], errors="coerce").fillna(0.0).clip(lower=0.0)
        energy_egrid_pos_kwh, _ = integrate_series_to_energy_kwh(egrid_pos, u_egrid, dt_hours)
    else:
        energy_egrid_pos_kwh = 0.0

    df_clip = df[(df["EOutInv"] > 0) | (df["IL_Pmax"] > 0)].copy()
    if df_clip.empty:
        context.results["inverter_clipping"] = {"available": True, "empty": True}
        return

    energy_out_kwh, _ = integrate_series_to_energy_kwh(df_clip["EOutInv"].clip(lower=0.0), u_out, dt_hours)
    energy_clipped_kwh, _ = integrate_series_to_energy_kwh(df_clip["IL_Pmax"].clip(lower=0.0), u_clip, dt_hours)

    potential_kwh = float(energy_out_kwh) + float(energy_clipped_kwh)
    pct_of_potential = _safe_pct(energy_clipped_kwh, potential_kwh)
    pct_of_egrid_pos = _safe_pct(energy_clipped_kwh, energy_egrid_pos_kwh)

    hours_clipping = float(int((df_clip["IL_Pmax"] > 0).sum())) * dt_hours
    max_clipping_value = float(df_clip["IL_Pmax"].max()) if not df_clip["IL_Pmax"].empty else 0.0

    month_map = _month_map_en()
    df_clip["month"] = df_clip.index.month

    def _monthly_energy(series: pd.Series, unit: str) -> float:
        value, _ = integrate_series_to_energy_kwh(series.clip(lower=0.0), unit, dt_hours)
        return float(value)

    monthly_clip = (
        df_clip.groupby("month", observed=False)["IL_Pmax"]
        .apply(lambda s: _monthly_energy(pd.to_numeric(s, errors="coerce").fillna(0.0), u_clip))
        .reset_index(name="energy_clipped_kwh")
    )

    monthly_out = (
        df_clip.groupby("month", observed=False)["EOutInv"]
        .apply(lambda s: _monthly_energy(pd.to_numeric(s, errors="coerce").fillna(0.0), u_out))
        .reset_index(name="energy_out_kwh")
    )

    monthly_hours = (
        df_clip.groupby("month", observed=False)["IL_Pmax"]
        .apply(lambda s: float(int((pd.to_numeric(s, errors="coerce").fillna(0.0) > 0).sum())) * dt_hours)
        .reset_index(name="hours_clipping")
    )

    monthly = monthly_clip.merge(monthly_out, on="month", how="outer").fillna(0.0)
    monthly = monthly.merge(monthly_hours, on="month", how="outer").fillna(0.0)
    monthly["potential_kwh"] = monthly["energy_out_kwh"] + monthly["energy_clipped_kwh"]
    monthly["pct_clipping"] = monthly.apply(
        lambda r: _safe_pct(r["energy_clipped_kwh"], r["potential_kwh"]),
        axis=1,
    )
    monthly["month_name"] = monthly["month"].map(month_map)
    monthly = monthly[["month_name", "energy_clipped_kwh", "hours_clipping", "pct_clipping"]]

    context.results["inverter_clipping"] = {
        "available": True,
        "summary": {
            "dt_hours": float(dt_hours),
            "dt_meta": dt_meta,
            "energy_out_kwh": float(energy_out_kwh),
            "energy_clipped_kwh": float(energy_clipped_kwh),
            "energy_egrid_pos_kwh": float(energy_egrid_pos_kwh),
            "potential_kwh": float(potential_kwh),
            "pct_of_egrid_pos": float(pct_of_egrid_pos),
            "pct_of_potential": float(pct_of_potential),
            "pct_reference_primary_label": "HOURLY_CLIP_REFERENCE_PROD_WO_NIGHT",
            "pct_reference_secondary_label": "HOURLY_CLIP_REFERENCE_POTENTIAL_AC",
            "hours_clipping": float(hours_clipping),
            "max_clipping_value": float(max_clipping_value),
            "clipping_unit": u_clip,
        },
        "monthly": monthly,
    }


# =============================================================================
# Monthly performance
# =============================================================================
def analyze_performance_monthly(context: AnalysisContext) -> None:
    df = context.df_raw.copy()
    dt_hours, dt_meta = infer_timestep_hours(df.index)

    month_map = _month_map_en()
    monthly = pd.DataFrame({"month": list(range(1, 13))})
    monthly["month_name"] = monthly["month"].map(month_map)

    prod_mask = _positive_production_mask(df, "E_Grid")

    # Operating hours
    op_tmp = pd.DataFrame({"month": df.index.month, "is_prod": prod_mask.astype(int)})
    op_month = op_tmp.groupby("month", observed=False)["is_prod"].sum().reset_index(name="operating_steps")
    op_month["operating_hours"] = op_month["operating_steps"].astype(float) * dt_hours
    monthly = monthly.merge(op_month[["month", "operating_hours"]], on="month", how="left")

    # E_Grid positive
    if "E_Grid" in df.columns:
        u_grid = str(context.units_map.get("E_Grid", "")).strip()
        tmp = pd.DataFrame({"month": df.index.month, "E_Grid": pd.to_numeric(df["E_Grid"], errors="coerce").fillna(0.0).clip(lower=0.0)})
        egrid_month = tmp.groupby("month", observed=False)["E_Grid"].apply(
            lambda s: integrate_series_to_energy_kwh(s, u_grid, dt_hours)[0]
        ).reset_index(name="e_grid_kwh")
        monthly = monthly.merge(egrid_month, on="month", how="left")
    else:
        monthly["e_grid_kwh"] = None

    # PR mean on positive-production hours only
    if "PR" in df.columns:
        pr_s = pd.to_numeric(df["PR"], errors="coerce").where(prod_mask)
        pr_tmp = pd.DataFrame({"month": df.index.month, "PR": pr_s})
        pr_month = pr_tmp.groupby("month", observed=False)["PR"].mean().reset_index(name="pr_mean_prod")
        monthly = monthly.merge(pr_month, on="month", how="left")
    else:
        monthly["pr_mean_prod"] = None

    # GlobHor integrated on positive-production hours only
    if "GlobHor" in df.columns:
        u_gh = str(context.units_map.get("GlobHor", "")).strip()
        gh_s = pd.to_numeric(df["GlobHor"], errors="coerce").fillna(0.0).where(prod_mask, 0.0)
        gh_tmp = pd.DataFrame({"month": df.index.month, "GlobHor": gh_s})
        gh_month = gh_tmp.groupby("month", observed=False)["GlobHor"].apply(
            lambda s: integrate_irradiance_to_kwh_m2(s, u_gh, dt_hours)
        ).reset_index(name="globhor_kwh_m2")
        monthly = monthly.merge(gh_month, on="month", how="left")
    else:
        monthly["globhor_kwh_m2"] = None

    # GlobInc integrated on positive-production hours only
    if "GlobInc" in df.columns:
        u_gi = str(context.units_map.get("GlobInc", "")).strip()
        gi_s = pd.to_numeric(df["GlobInc"], errors="coerce").fillna(0.0).where(prod_mask, 0.0)
        gi_tmp = pd.DataFrame({"month": df.index.month, "GlobInc": gi_s})
        gi_month = gi_tmp.groupby("month", observed=False)["GlobInc"].apply(
            lambda s: integrate_irradiance_to_kwh_m2(s, u_gi, dt_hours)
        ).reset_index(name="globinc_kwh_m2")
        monthly = monthly.merge(gi_month, on="month", how="left")
    else:
        monthly["globinc_kwh_m2"] = None

    # GlobEff integrated on positive-production hours only
    if "GlobEff" in df.columns:
        u_ge = str(context.units_map.get("GlobEff", "")).strip()
        ge_s = pd.to_numeric(df["GlobEff"], errors="coerce").fillna(0.0).where(prod_mask, 0.0)
        ge_tmp = pd.DataFrame({"month": df.index.month, "GlobEff": ge_s})
        ge_month = ge_tmp.groupby("month", observed=False)["GlobEff"].apply(
            lambda s: integrate_irradiance_to_kwh_m2(s, u_ge, dt_hours)
        ).reset_index(name="globeff_kwh_m2")
        monthly = monthly.merge(ge_month, on="month", how="left")
    else:
        monthly["globeff_kwh_m2"] = None

    monthly["globeff_over_globinc_pct"] = monthly.apply(
        lambda r: _safe_pct(r["globeff_kwh_m2"], r["globinc_kwh_m2"])
        if pd.notna(r["globinc_kwh_m2"]) and r["globinc_kwh_m2"] not in (None, 0)
        else None,
        axis=1,
    )

    monthly["tilt_gain_pct"] = monthly.apply(
        lambda r: _safe_pct(r["globinc_kwh_m2"], r["globhor_kwh_m2"]) - 100
        if pd.notna(r["globhor_kwh_m2"]) and r["globhor_kwh_m2"] not in (None, 0)
        else None,
        axis=1,
    )

    # Yf on positive-production hours only
    if "Yf" in df.columns:
        u_yf = str(context.units_map.get("Yf", "")).strip()
        yf_s = pd.to_numeric(df["Yf"], errors="coerce").fillna(0.0).where(prod_mask, 0.0)
        yf_tmp = pd.DataFrame({"month": df.index.month, "Yf": yf_s})

        def _yf_month(s: pd.Series) -> float:
            if "kWh/kWc/jour" in u_yf:
                return float(s.sum())
            return integrate_series_to_energy_kwh(s, u_yf, dt_hours)[0]

        yf_month = yf_tmp.groupby("month", observed=False)["Yf"].apply(_yf_month).reset_index(name="productible_specific")
        monthly = monthly.merge(yf_month, on="month", how="left")
    else:
        monthly["productible_specific"] = None

    # EArray positive
    if "EArray" in df.columns:
        u_arr = str(context.units_map.get("EArray", "")).strip()
        arr_s = pd.to_numeric(df["EArray"], errors="coerce").fillna(0.0).where(prod_mask, 0.0)
        arr_tmp = pd.DataFrame({"month": df.index.month, "EArray": arr_s})
        arr_month = arr_tmp.groupby("month", observed=False)["EArray"].apply(
            lambda s: integrate_series_to_energy_kwh(s, u_arr, dt_hours)[0]
        ).reset_index(name="earray_kwh")
        monthly = monthly.merge(arr_month, on="month", how="left")
    else:
        monthly["earray_kwh"] = None

    monthly = monthly.infer_objects(copy=False)

    annual = {
        "month_name": "Annual",

        "operating_hours": float(
            pd.to_numeric(monthly["operating_hours"], errors="coerce").fillna(0.0).sum()
        ) if "operating_hours" in monthly else None,

        "globhor_kwh_m2": float(
            pd.to_numeric(monthly["globhor_kwh_m2"], errors="coerce").fillna(0.0).sum()
        ) if "globhor_kwh_m2" in monthly else None,

        "globinc_kwh_m2": float(
            pd.to_numeric(monthly["globinc_kwh_m2"], errors="coerce").fillna(0.0).sum()
        ) if "globinc_kwh_m2" in monthly else None,

        "globeff_kwh_m2": float(
            pd.to_numeric(monthly["globeff_kwh_m2"], errors="coerce").fillna(0.0).sum()
        ) if "globeff_kwh_m2" in monthly else None,

        "globinc_over_globhor_pct": None,
        "globeff_over_globinc_pct": None,

        "pr_mean_prod": float(
            pd.to_numeric(monthly["pr_mean_prod"], errors="coerce").dropna().mean()
        ) if "pr_mean_prod" in monthly and pd.to_numeric(monthly["pr_mean_prod"], errors="coerce").notna().any() else None,

        "productible_specific": float(
            pd.to_numeric(monthly["productible_specific"], errors="coerce").fillna(0.0).sum()
        ) if "productible_specific" in monthly and pd.to_numeric(monthly["productible_specific"], errors="coerce").notna().any() else None,

        "e_grid_kwh": float(
            pd.to_numeric(monthly["e_grid_kwh"], errors="coerce").fillna(0.0).sum()
        ) if "e_grid_kwh" in monthly else None,

        "earray_kwh": float(
            pd.to_numeric(monthly["earray_kwh"], errors="coerce").fillna(0.0).sum()
        ) if "earray_kwh" in monthly else None,
    }

    if annual["globhor_kwh_m2"] not in (None, 0) and annual["globinc_kwh_m2"] is not None:
        annual["tilt_gain_pct"] = _safe_pct(annual["globinc_kwh_m2"], annual["globhor_kwh_m2"], ) -100

    if annual["globinc_kwh_m2"] not in (None, 0) and annual["globeff_kwh_m2"] is not None:
        annual["globeff_over_globinc_pct"] = _safe_pct(annual["globeff_kwh_m2"], annual["globinc_kwh_m2"], )

    context.results["performance_monthly"] = {
        "available": True,
        "summary": {
            "dt_hours": float(dt_hours),
            "dt_meta": dt_meta,
        },
        "monthly": monthly[
            [
                "month_name",
                "operating_hours",
                "globhor_kwh_m2",
                "globinc_kwh_m2",
                "globeff_kwh_m2",
                "tilt_gain_pct",
                "globeff_over_globinc_pct",
                "pr_mean_prod",
                "productible_specific",
                "e_grid_kwh",
                "earray_kwh",
            ]
        ].copy(),
        "annual": annual,
    }


# =============================================================================
# System summary
# =============================================================================
def analyze_system_summary(context: AnalysisContext) -> None:
    gp = context.results.get("global_production", {})
    clip = context.results.get("inverter_clipping", {})
    gl = context.results.get("grid_limit", {})
    thr = context.results.get("threshold", {})
    perf = context.results.get("performance_monthly", {})

    if not gp or not gp.get("available", False):
        context.results["system_summary"] = {"available": False}
        return

    gp_s = gp.get("summary", {})
    production_wo_night_kwh = float(gp_s.get("production_without_import_kwh", 0.0))
    night_kwh = float(gp_s.get("night_consumption_kwh", 0.0))
    pr_mean = gp_s.get("pr_mean", None)

    clipping_kwh = 0.0
    clipping_pct_of_production = 0.0
    clipping_pct_of_potential = 0.0
    if clip and clip.get("available", False) and not clip.get("empty", False):
        clip_s = clip.get("summary", {})
        clipping_kwh = float(clip_s.get("energy_clipped_kwh", 0.0))
        clipping_pct_of_production = _safe_pct(clipping_kwh, production_wo_night_kwh)
        clipping_pct_of_potential = float(clip_s.get("pct_of_potential", 0.0))

    night_pct_of_production = _safe_pct(night_kwh, production_wo_night_kwh)

    grid_limit_kwh = 0.0
    grid_limit_pct_of_production = 0.0
    has_grid_limit = False
    if gl and gl.get("available", False):
        gl_s = gl.get("summary", {})
        grid_limit_kwh = float(gl_s.get("lost_kwh", 0.0))
        grid_limit_pct_of_production = _safe_pct(grid_limit_kwh, production_wo_night_kwh)
        has_grid_limit = True

    loss_total_pct_of_production = (
        clipping_pct_of_production
        + night_pct_of_production
        + grid_limit_pct_of_production
    )

    if loss_total_pct_of_production < 1.0:
        system_state_level = "VERY_LOW_CONSTRAINT"
    elif loss_total_pct_of_production < 3.0:
        system_state_level = "LOW_CONSTRAINT"
    elif loss_total_pct_of_production < 6.0:
        system_state_level = "MODERATE_CONSTRAINT"
    else:
        system_state_level = "HIGH_CONSTRAINT"

    meteo_level = None
    optics_level = None
    productible_specific = None
    globhor_annual = None
    tilt_gain_pct = None
    globinc_annual = None
    globeff_ratio_annual = None

    if perf and perf.get("available", False):
        row = perf.get("annual", {}) or {}
        if row:
            globhor_annual = row.get("globhor_kwh_m2", None)
            globinc_annual = row.get("globinc_kwh_m2", None)
            tilt_gain_pct = row.get("tilt_gain_pct", None)
            globeff_ratio_annual = row.get("globeff_over_globinc_pct", None)
            productible_specific = row.get("productible_specific", None)

    if globinc_annual is not None:
        if globinc_annual < 1200:
            meteo_level = "MODEST"
        elif globinc_annual < 1600:
            meteo_level = "GOOD"
        else:
            meteo_level = "VERY_GOOD"

    if globeff_ratio_annual is not None:
        if globeff_ratio_annual >= 95:
            optics_level = "LOW_LOSSES"
        elif globeff_ratio_annual >= 90:
            optics_level = "MODERATE_LOSSES"
        else:
            optics_level = "MARKED_LOSSES"

    df = context.df_raw
    col = context.options.threshold_column
    productive_utilization_ratio = None
    capacity_reference_value = None
    productive_utilization_reference_label = "HOURLY_UTILIZATION_REFERENCE_P99"

    if col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        s_pos = s[s > 0]
        if not s_pos.empty:
            capacity_reference_value = float(s_pos.quantile(0.99))
            if capacity_reference_value > 0:
                productive_utilization_ratio = float(s_pos.mean() / capacity_reference_value)

    threshold_value = float(getattr(context.options, "threshold_value", 0.0) or 0.0)
    energy_above_limit_kwh = 0.0
    energy_above_limit_pct_of_production = 0.0
    bridging_recommendation_level = "NOT_AVAILABLE"

    dc_ac_review_recommendation_level = "NOT_AVAILABLE"
    clipping_pct = float(clipping_pct_of_production)

    if productive_utilization_ratio is not None:
        if clipping_pct < 0.5 and productive_utilization_ratio < 0.60:
            dc_ac_review_recommendation_level = "REVIEW_RELEVANT"
        elif clipping_pct < 1.0 and productive_utilization_ratio < 0.70:
            dc_ac_review_recommendation_level = "REVIEW_POSSIBLE"
        else:
            dc_ac_review_recommendation_level = "REVIEW_NOT_PRIORITY"

    if thr and thr.get("available", False):
        thr_s = thr.get("summary", {})
        energy_above_limit_kwh = float(thr_s.get("energy_above_kwh", 0.0))
        energy_above_limit_pct_of_production = _safe_pct(energy_above_limit_kwh, production_wo_night_kwh)

    if threshold_value > 0 and productive_utilization_ratio is not None:
        if energy_above_limit_pct_of_production < 1.0 and productive_utilization_ratio < 0.65:
            bridging_recommendation_level = "FAVORABLE"
        elif energy_above_limit_pct_of_production > 3.0 or productive_utilization_ratio > 0.80:
            bridging_recommendation_level = "NOT_RECOMMENDED"
        else:
            bridging_recommendation_level = "CAUTION"

    context.results["system_summary"] = {
        "available": True,
        "production_wo_night_kwh": float(production_wo_night_kwh),
        "night_kwh": float(night_kwh),
        "night_pct_of_production": float(night_pct_of_production),
        "clipping_kwh": float(clipping_kwh),
        "clipping_pct_of_production": float(clipping_pct_of_production),
        "clipping_pct_of_potential": float(clipping_pct_of_potential),
        "grid_limit_kwh": float(grid_limit_kwh),
        "grid_limit_pct_of_production": float(grid_limit_pct_of_production),
        "has_grid_limit": bool(has_grid_limit),
        "loss_total_pct_of_production": float(loss_total_pct_of_production),
        "system_state_level": system_state_level,
        "productive_utilization_ratio": productive_utilization_ratio,
        "capacity_reference_value": capacity_reference_value,
        "productive_utilization_reference_label": productive_utilization_reference_label,
        "energy_above_limit_kwh": float(energy_above_limit_kwh),
        "energy_above_limit_pct_of_production": float(energy_above_limit_pct_of_production),
        "bridging_recommendation_level": bridging_recommendation_level,
        "pr_mean": pr_mean,
        "globhor_annual": globhor_annual,
        "tilt_gain_pct": tilt_gain_pct,
        "optical_efficiency_pct": globeff_ratio_annual,
        "dc_ac_review_recommendation_level": dc_ac_review_recommendation_level,
        "globinc_annual": globinc_annual,
        "globeff_ratio_annual": globeff_ratio_annual,
        "productible_specific": productible_specific,
        "meteo_level": meteo_level,
        "optics_level": optics_level,
    }