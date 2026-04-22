from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

from core.bess_sizing.v2_models import MarginalAnalysisInputs


@dataclass
class MarginalAnalysisOutcome:
    summary_df: pd.DataFrame
    marginal_recommended_config_id: Optional[str]
    knee_config_id: Optional[str]
    knee_energy_mwh: Optional[float]
    meta: Dict[str, float | str | None]


def _compute_knee_energy(envelope_df: pd.DataFrame) -> Optional[float]:
    if envelope_df is None or len(envelope_df) < 3:
        return None
    x = envelope_df["energy_nominal_mwh"].to_numpy(dtype=float)
    y = envelope_df["gain_annual_abs_eur"].to_numpy(dtype=float)
    if np.allclose(y, y[0]):
        return None

    x_n = (x - x.min()) / max(1e-9, (x.max() - x.min()))
    y_n = (y - y.min()) / max(1e-9, (y.max() - y.min()))

    line = y_n[0] + (y_n[-1] - y_n[0]) * x_n
    distances = y_n - line
    idx = int(np.argmax(distances))
    if idx <= 0 or idx >= len(x) - 1:
        return None
    return float(x[idx])


def _compute_saturation_energy(envelope_df: pd.DataFrame) -> Optional[float]:
    if envelope_df is None or len(envelope_df) < 2:
        return None
    work = envelope_df.sort_values("energy_nominal_mwh").copy()
    delta_gain = work["gain_annual_abs_eur"].diff()
    delta_energy = work["energy_nominal_mwh"].diff().replace(0.0, np.nan)
    marginal_gain = (delta_gain / delta_energy).dropna()
    if marginal_gain.empty:
        return float(work.iloc[0]["energy_nominal_mwh"])

    positive = marginal_gain[marginal_gain > 0.0]
    if positive.empty:
        return float(work.iloc[0]["energy_nominal_mwh"])

    peak_positive_marginal = float(positive.max())
    threshold = 0.2 * peak_positive_marginal
    first_saturated_idx = marginal_gain[marginal_gain <= threshold].index
    if len(first_saturated_idx) > 0:
        return float(work.loc[first_saturated_idx[0], "energy_nominal_mwh"])
    return float(work.iloc[-1]["energy_nominal_mwh"])


def _compute_marginal_per_mw(df: pd.DataFrame) -> pd.Series:
    out = pd.Series(index=df.index, dtype=float)
    for _, grp in df.groupby("energy_nominal_mwh"):
        g = (
            grp.sort_values("power_mw")
            .drop_duplicates(subset=["power_mw"], keep="first")
            .copy()
        )
        prev_gain = g["gain_annual_abs_eur"].shift(1)
        prev_power = g["power_mw"].shift(1)
        marginal = (g["gain_annual_abs_eur"] - prev_gain) / (
            g["power_mw"] - prev_power
        )
        out.loc[g.index] = marginal
    return out


def _compute_marginal_per_mwh(df: pd.DataFrame) -> pd.Series:
    out = pd.Series(index=df.index, dtype=float)
    for _, grp in df.groupby("power_mw"):
        g = (
            grp.sort_values("energy_nominal_mwh")
            .drop_duplicates(subset=["energy_nominal_mwh"], keep="first")
            .copy()
        )
        prev_gain = g["gain_annual_abs_eur"].shift(1)
        prev_energy = g["energy_nominal_mwh"].shift(1)
        marginal = (g["gain_annual_abs_eur"] - prev_gain) / (
            g["energy_nominal_mwh"] - prev_energy
        )
        out.loc[g.index] = marginal
    return out


def _closest_config_for_energy(work: pd.DataFrame, target_energy_mwh: float) -> pd.Series:
    ranked = (
        work.assign(
            _energy_gap=(work["energy_nominal_mwh"] - float(target_energy_mwh)).abs()
        )
        .sort_values(
            by=["_energy_gap", "gain_annual_abs_eur", "power_mw", "duration_h"],
            ascending=[True, False, True, True],
        )
        .reset_index(drop=True)
    )
    return ranked.iloc[0]


def run_marginal_analysis(
    summary_df: pd.DataFrame,
    marginal_inputs: MarginalAnalysisInputs,
) -> MarginalAnalysisOutcome:
    marginal_inputs.validate()
    if summary_df is None or summary_df.empty:
        return MarginalAnalysisOutcome(
            summary_df=pd.DataFrame(),
            marginal_recommended_config_id=None,
            knee_config_id=None,
            knee_energy_mwh=None,
            meta={"note": "empty_summary"},
        )

    work = summary_df.copy()
    gain_max = float(work["gain_annual_abs_eur"].max())
    work["gain_share_of_max_pct"] = (
        100.0 * work["gain_annual_abs_eur"] / gain_max
        if abs(gain_max) > 1e-9
        else 0.0
    )

    work["marginal_gain_per_mw_eur"] = _compute_marginal_per_mw(work)
    work["marginal_gain_per_mwh_eur"] = _compute_marginal_per_mwh(work)

    work = work.sort_values(
        by=["power_mw", "duration_h", "energy_nominal_mwh"]
    ).reset_index(drop=True)

    envelope = (
        work.sort_values("gain_annual_abs_eur", ascending=False)
        .drop_duplicates(subset=["energy_nominal_mwh"], keep="first")
        .sort_values("energy_nominal_mwh")
        .reset_index(drop=True)
    )

    knee_energy = _compute_knee_energy(envelope)
    saturation_energy = _compute_saturation_energy(envelope)
    reference_energy = knee_energy if knee_energy is not None else saturation_energy
    if reference_energy is None and not envelope.empty:
        reference_energy = float(envelope.iloc[0]["energy_nominal_mwh"])

    marginal_recommended_config_id: Optional[str] = None
    rec_row: Optional[pd.Series] = None
    if reference_energy is not None:
        rec_row = _closest_config_for_energy(work, reference_energy)
        marginal_recommended_config_id = str(rec_row["config_id"])

    knee_config_id = None
    if knee_energy is not None:
        knee_row = _closest_config_for_energy(work, knee_energy)
        knee_config_id = str(knee_row["config_id"])

    selected_gain_share = (
        float(rec_row.get("gain_share_of_max_pct"))
        if rec_row is not None and pd.notna(rec_row.get("gain_share_of_max_pct"))
        else None
    )
    meta = {
        "gain_max_eur": gain_max,
        "auto_method": str(marginal_inputs.auto_method),
        "knee_energy_mwh": knee_energy,
        "saturation_energy_mwh": saturation_energy,
        "selected_reference_energy_mwh": reference_energy,
        "marginal_recommended_gain_share_pct": selected_gain_share,
    }
    return MarginalAnalysisOutcome(
        summary_df=work,
        marginal_recommended_config_id=marginal_recommended_config_id,
        knee_config_id=knee_config_id,
        knee_energy_mwh=knee_energy,
        meta=meta,
    )
