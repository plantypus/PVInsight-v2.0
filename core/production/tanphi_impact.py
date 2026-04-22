from __future__ import annotations

import math
from typing import Optional, Tuple

import pandas as pd

from .hourly_models import AnalysisContext
from utils import suggest_similar_columns


# Engineering approximation note:
# This module intentionally provides a simplified estimate of tan(phi) impact.
# It is not a substitute for a dedicated PVsyst resimulation.


def _resolve_column(columns: list[str], candidates: list[str]) -> Optional[str]:
    by_lower = {c.lower(): c for c in columns}
    for cand in candidates:
        found = by_lower.get(cand.lower())
        if found is not None:
            return found
    return None


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


def _to_power_kw(s: pd.Series, unit: str, dt_hours: float) -> pd.Series:
    u = (unit or "").strip().lower().replace(" ", "")
    x = pd.to_numeric(s, errors="coerce").fillna(0.0)

    if dt_hours is None or dt_hours <= 0 or not pd.notna(dt_hours):
        dt_hours = 1.0

    # Power-like units (kW, kVA, kvar) -> unchanged numeric magnitude.
    if (("kw" in u) or ("kva" in u) or ("kvar" in u)) and not (("kwh" in u) or ("kvah" in u) or ("kvarh" in u)):
        return x
    # Energy-like units (kWh, kVAh, kvarh) -> convert to power-like via timestep.
    if ("kwh" in u) or ("kvah" in u) or ("kvarh" in u):
        return x / float(dt_hours)
    if ("wh" in u) and ("kwh" not in u) and ("kvah" not in u) and ("kvarh" not in u):
        return (x / 1000.0) / float(dt_hours)
    if ("w" in u) and ("wh" not in u):
        return x / 1000.0

    # Fallback assumption: series is already power-like (kW).
    return x


def _integrate_power_kw_to_kwh(power_kw: pd.Series, dt_hours: float) -> float:
    s = pd.to_numeric(power_kw, errors="coerce").fillna(0.0)
    return float(s.sum()) * float(dt_hours)


def _safe_pct(num: float | int | None, den: float | int | None) -> float:
    try:
        n = float(num)
        d = float(den)
        if d <= 0:
            return 0.0
        return 100.0 * n / d
    except Exception:
        return 0.0


def _estimate_scenario(
    *,
    tan_phi_target: float,
    tan_phi_ref: float,
    out_ref_kw: pd.Series,
    grid_ref_kw: pd.Series,
    has_il_pmax: bool,
    il_pmax_kw: pd.Series,
    has_eac_ohm: bool,
    eac_ohm_kw: pd.Series,
    other_explicit_losses_kw: pd.Series,
) -> dict:
    cos_phi_target = 1.0 / math.sqrt(1.0 + tan_phi_target * tan_phi_target)
    cos_phi_ref = 1.0 / math.sqrt(1.0 + tan_phi_ref * tan_phi_ref)

    r_cap = float(cos_phi_target / cos_phi_ref)
    k_loss = float((1.0 + tan_phi_target * tan_phi_target) / (1.0 + tan_phi_ref * tan_phi_ref))

    if has_il_pmax:
        p_potential_kw = (out_ref_kw + il_pmax_kw).clip(lower=0.0)
        p_cap_target_kw = float(p_potential_kw.max()) * r_cap if not p_potential_kw.empty else 0.0
        out_est_kw = p_potential_kw.clip(upper=p_cap_target_kw)
    else:
        p_cap_target_kw = float(out_ref_kw.max()) * r_cap if not out_ref_kw.empty else 0.0
        out_est_kw = out_ref_kw.clip(upper=p_cap_target_kw)

    out_est_kw = out_est_kw.clip(lower=0.0)

    if has_eac_ohm:
        eac_ohm_est_kw = eac_ohm_kw.clip(lower=0.0) * k_loss
        grid_est_kw = out_est_kw - eac_ohm_est_kw - other_explicit_losses_kw.clip(lower=0.0)
    else:
        loss_downstream_ref_kw = (out_ref_kw - grid_ref_kw).clip(lower=0.0)
        loss_downstream_est_kw = loss_downstream_ref_kw * k_loss
        grid_est_kw = out_est_kw - loss_downstream_est_kw

    grid_est_kw = grid_est_kw.clip(lower=0.0)
    grid_est_kw = pd.concat([grid_est_kw, out_est_kw], axis=1).min(axis=1)

    return {
        "tan_phi": float(tan_phi_target),
        "cos_phi": float(cos_phi_target),
        "r_cap": float(r_cap),
        "k_loss": float(k_loss),
        "out_est_kw": out_est_kw,
        "grid_est_kw": grid_est_kw,
        "p_cap_target_kw": float(p_cap_target_kw),
    }


def analyze_tanphi_impact(context: AnalysisContext) -> None:
    df = context.df_raw
    cols = df.columns.tolist()

    col_out = _resolve_column(cols, ["EOutInv"])
    col_grid = _resolve_column(cols, ["E_Grid"])

    missing = []
    if col_out is None:
        missing.append("EOutInv")
    if col_grid is None:
        missing.append("E_Grid")

    if missing:
        context.results["tanphi_impact"] = {
            "available": False,
            "missing_columns": missing,
            "suggestions": suggest_similar_columns(cols, missing),
        }
        return

    dt_hours, dt_meta = infer_timestep_hours(df.index)

    col_il = _resolve_column(cols, ["IL_Pmax"])
    col_eac = _resolve_column(cols, ["EacOhmL", "EAcOhmL"])
    col_egrdlim = _resolve_column(cols, ["EGrdLim"])
    col_apparent = _resolve_column(cols, ["EApGrid"])
    col_reactive = _resolve_column(cols, ["EReGrid", "ERegrid"])

    has_il = col_il is not None
    has_eac = col_eac is not None
    has_egrdlim = col_egrdlim is not None
    has_richer_set = any([has_il, has_eac, has_egrdlim, col_apparent is not None, col_reactive is not None])
    mode_used = "enhanced" if has_richer_set else "fallback"

    u_out = str(context.units_map.get(col_out, "")).strip()
    u_grid = str(context.units_map.get(col_grid, "")).strip()
    u_il = str(context.units_map.get(col_il, "")).strip() if has_il else ""
    u_eac = str(context.units_map.get(col_eac, "")).strip() if has_eac else ""
    u_lim = str(context.units_map.get(col_egrdlim, "")).strip() if has_egrdlim else ""

    out_ref_kw = _to_power_kw(df[col_out], u_out, dt_hours).clip(lower=0.0)
    grid_ref_kw = _to_power_kw(df[col_grid], u_grid, dt_hours).clip(lower=0.0)

    if has_il:
        il_pmax_kw = _to_power_kw(df[col_il], u_il, dt_hours).clip(lower=0.0)
    else:
        il_pmax_kw = pd.Series(0.0, index=df.index, dtype=float)

    if has_eac:
        eac_ohm_kw = _to_power_kw(df[col_eac], u_eac, dt_hours).clip(lower=0.0)
    else:
        eac_ohm_kw = pd.Series(0.0, index=df.index, dtype=float)

    # Optional explicit downstream losses (engineering approximation).
    # Only a conservative list of candidates is considered.
    other_loss_candidates = [
        "EAcCblL",
        "EacCblL",
        "EAcTrfL",
        "EacTrfL",
        "ETrfLss",
        "EACLoss",
    ]
    other_loss_cols = []
    for cand in other_loss_candidates:
        found = _resolve_column(cols, [cand])
        if found is not None and found not in [col_out, col_grid, col_il, col_eac]:
            other_loss_cols.append(found)
    other_loss_cols = sorted(set(other_loss_cols))

    if other_loss_cols:
        other_explicit_losses_kw = pd.Series(0.0, index=df.index, dtype=float)
        for c in other_loss_cols:
            uc = str(context.units_map.get(c, "")).strip()
            other_explicit_losses_kw = other_explicit_losses_kw + _to_power_kw(df[c], uc, dt_hours).clip(lower=0.0)
    else:
        other_explicit_losses_kw = pd.Series(0.0, index=df.index, dtype=float)

    tan_phi_ref = 0.0
    cos_phi_ref = 1.0 / math.sqrt(1.0 + tan_phi_ref * tan_phi_ref)
    assumed_tan_phi_ref_default = True
    tan_phi_ref_source = "assumed_zero"

    if col_apparent is not None and col_reactive is not None:
        u_app = str(context.units_map.get(col_apparent, "")).strip()
        u_re = str(context.units_map.get(col_reactive, "")).strip()
        s_app_kw = _to_power_kw(df[col_apparent], u_app, dt_hours).clip(lower=0.0)
        q_re_kw = _to_power_kw(df[col_reactive], u_re, dt_hours).abs()

        s_app_kwh = _integrate_power_kw_to_kwh(s_app_kw, dt_hours)
        q_re_kwh = _integrate_power_kw_to_kwh(q_re_kw, dt_hours)

        if s_app_kwh > 0:
            q_over_s = min(max(float(q_re_kwh) / float(s_app_kwh), 0.0), 0.999999)
            cos_candidate = math.sqrt(max(1.0 - q_over_s * q_over_s, 0.0))
            if cos_candidate > 1e-6:
                tan_candidate = q_over_s / cos_candidate
                tan_phi_ref = float(tan_candidate)
                cos_phi_ref = float(cos_candidate)
                assumed_tan_phi_ref_default = False
                tan_phi_ref_source = "computed_from_apparent_reactive"

    ref_scenario = _estimate_scenario(
        tan_phi_target=tan_phi_ref,
        tan_phi_ref=tan_phi_ref,
        out_ref_kw=out_ref_kw,
        grid_ref_kw=grid_ref_kw,
        has_il_pmax=has_il,
        il_pmax_kw=il_pmax_kw,
        has_eac_ohm=has_eac,
        eac_ohm_kw=eac_ohm_kw,
        other_explicit_losses_kw=other_explicit_losses_kw if has_eac else pd.Series(0.0, index=df.index, dtype=float),
    )
    annual_ref_kwh = _integrate_power_kw_to_kwh(ref_scenario["grid_est_kw"], dt_hours)
    annual_ref_mwh = annual_ref_kwh / 1000.0

    tan_values = [round(0.25 + i * 0.01, 2) for i in range(11)]

    warnings_common: list[str] = [
        "engineering_estimate_only",
        "assumed_inverter_kva_model",
    ]
    if assumed_tan_phi_ref_default:
        warnings_common.append("assumed_tanphi_ref_0")
    else:
        warnings_common.append("tanphi_ref_computed_from_apparent_reactive")
    if not has_il:
        warnings_common.append("missing_il_pmax_simple_upstream_cap")
    if not has_eac:
        warnings_common.append("missing_eacohml_downstream_losses_from_out_minus_grid")
    if has_egrdlim:
        warnings_common.append("egrdlim_propagated_not_recomputed")
    if other_loss_cols:
        warnings_common.append("other_explicit_downstream_losses_subtracted_if_identified")
    warnings_common.append("prefer_export_eacohml_and_il_pmax_for_higher_fidelity")

    rows = []
    for tan_target in tan_values:
        scen = _estimate_scenario(
            tan_phi_target=float(tan_target),
            tan_phi_ref=tan_phi_ref,
            out_ref_kw=out_ref_kw,
            grid_ref_kw=grid_ref_kw,
            has_il_pmax=has_il,
            il_pmax_kw=il_pmax_kw,
            has_eac_ohm=has_eac,
            eac_ohm_kw=eac_ohm_kw,
            other_explicit_losses_kw=other_explicit_losses_kw if has_eac else pd.Series(0.0, index=df.index, dtype=float),
        )

        annual_est_kwh = _integrate_power_kw_to_kwh(scen["grid_est_kw"], dt_hours)
        annual_est_mwh = annual_est_kwh / 1000.0
        delta_mwh = annual_est_mwh - annual_ref_mwh
        delta_pct = _safe_pct(delta_mwh, annual_ref_mwh)

        peak_out_mw = (float(scen["out_est_kw"].max()) / 1000.0) if not scen["out_est_kw"].empty else 0.0
        peak_grid_mw = (float(scen["grid_est_kw"].max()) / 1000.0) if not scen["grid_est_kw"].empty else 0.0

        rows.append(
            {
                "tan_phi": float(tan_target),
                "cos_phi": float(scen["cos_phi"]),
                "mode_used": mode_used,
                "annual_EGrid_est_MWh": float(annual_est_mwh),
                "delta_vs_ref_MWh": float(delta_mwh),
                "delta_vs_ref_pct": float(delta_pct),
                "P_decl_opt_MW": float(peak_grid_mw),
                "peak_EOutInv_est_MW": float(peak_out_mw),
                "peak_EGrid_est_MW": float(peak_grid_mw),
                "warnings": "; ".join(warnings_common),
            }
        )

    scenarios = pd.DataFrame(
        rows,
        columns=[
            "tan_phi",
            "cos_phi",
            "mode_used",
            "annual_EGrid_est_MWh",
            "delta_vs_ref_MWh",
            "delta_vs_ref_pct",
            "P_decl_opt_MW",
            "peak_EOutInv_est_MW",
            "peak_EGrid_est_MW",
            "warnings",
        ],
    )
    # Signed convention:
    #   > 0 => loss versus reference
    #   < 0 => potential gain versus reference
    scenarios["annual_energy_loss_MWh"] = -scenarios["delta_vs_ref_MWh"]

    annual_egrdlim_mwh = None
    if has_egrdlim:
        egrdlim_kw = _to_power_kw(df[col_egrdlim], u_lim, dt_hours).clip(lower=0.0)
        annual_egrdlim_mwh = _integrate_power_kw_to_kwh(egrdlim_kw, dt_hours) / 1000.0

    context.results["tanphi_impact"] = {
        "available": True,
        "summary": {
            "dt_hours": float(dt_hours),
            "dt_meta": dt_meta,
            "mode_used": mode_used,
            "tan_phi_ref": float(tan_phi_ref),
            "cos_phi_ref": float(cos_phi_ref),
            "assumed_tan_phi_ref_default": bool(assumed_tan_phi_ref_default),
            "tan_phi_ref_source": tan_phi_ref_source,
            "out_column": col_out,
            "grid_column": col_grid,
            "has_il_pmax": bool(has_il),
            "has_eac_ohml": bool(has_eac),
            "has_egrdlim": bool(has_egrdlim),
            "has_apparent_reactive_pair": bool(col_apparent is not None and col_reactive is not None),
            "other_explicit_loss_columns": other_loss_cols,
            "annual_ref_EGrid_MWh": float(annual_ref_mwh),
            "annual_ref_EGrdLim_MWh": float(annual_egrdlim_mwh) if annual_egrdlim_mwh is not None else None,
            "warning_codes": warnings_common,
        },
        "scenarios": scenarios,
    }
