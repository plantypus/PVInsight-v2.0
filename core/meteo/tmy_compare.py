# core/meteo/tmy_compare.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils.paths import RunPaths, make_run_folders
from utils.validation import DataQuality
from utils.run_log import write_run_log
from utils.energy import annual_irradiation, EnergySummary
from utils.units import convert_irradiance_units

# Readers (auto-detect)
from utils.readers.tmy_pvsyst import TMYDataset, read_tmy_pvsyst
from utils.readers.tmy_solargis import read_tmy_solargis

import logging
log = logging.getLogger(__name__)

TextSource = Union[str, Path, bytes]


# =============================================================================
# Result object
# =============================================================================
@dataclass(frozen=True)
class TMYCompareResult:
    ds_a: TMYDataset
    ds_b: TMYDataset

    native_step_a_min: int
    native_step_b_min: int
    used_step_min: int

    # Harmonized data used for comparison (hourly, common period, aligned)
    df_a: pd.DataFrame
    df_b: pd.DataFrame
    common_start: pd.Timestamp
    common_end: pd.Timestamp

    # Metrics per variable
    metrics: pd.DataFrame  # one row per variable

    # Energy (full-year) summaries (computed on original datasets)
    energy_a: EnergySummary
    energy_b: EnergySummary

    # Optional "common period" energy (computed on aligned common period)
    energy_a_common: EnergySummary
    energy_b_common: EnergySummary

    alert_flag: bool
    report_pdf: Path
    log_path: Path
    run_dir: Path


# =============================================================================
# Reader selection (auto)
# =============================================================================
def _read_tmy_auto(
    source: TextSource,
    source_name: str,
    target_irradiance_unit: str,
    resample_hourly_if_subhourly: bool,
) -> Tuple[TMYDataset, str]:
    """
    Tries PVSyst first, then SolarGIS.
    Detection failures are normal and silent.
    """
    last_error: Exception | None = None

    try:
        ds = read_tmy_pvsyst(
            source,
            source_name=source_name,
            target_irradiance_unit=target_irradiance_unit,
            resample_hourly_if_subhourly=resample_hourly_if_subhourly,
        )
        return ds, "3E"
    except Exception as e:
        last_error = e

    try:
        ds = read_tmy_solargis(
            source,
            source_name=source_name,
            target_irradiance_unit=target_irradiance_unit,
            resample_hourly_if_subhourly=resample_hourly_if_subhourly,
        )
        return ds, "solargis"
    except Exception as e:
        last_error = e

    msg = (
        "Unable to read TMY file with supported readers (PVSyst, SolarGIS).\n"
        f"Last error: {type(last_error).__name__}: {last_error}"
    )
    raise ValueError(msg)


# =============================================================================
# Time-step harmonization
# =============================================================================
def _add_climatology_key(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a key independent of year, suitable for TMY comparison.
    Key = (month, day, hour). Also rebuild a synthetic datetime for plotting.
    """
    df = _ensure_datetime(df).copy()
    dt = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"]).copy()
    dt = pd.to_datetime(df["datetime"], errors="coerce")

    df["month"] = dt.dt.month
    df["day"] = dt.dt.day
    df["hour"] = dt.dt.hour

    # Synthetic year for display (2001: non-leap)
    df["datetime_plot"] = pd.to_datetime(
        dict(year=2001, month=df["month"], day=df["day"], hour=df["hour"]),
        errors="coerce",
    )
    return df


def align_climatology_hourly(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    vars_keep: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]:
    """
    Align by (month, day, hour) instead of datetime.
    This fixes TMY files using different reference years.
    """
    a = _add_climatology_key(df_a)
    b = _add_climatology_key(df_b)

    common_vars = [v for v in vars_keep if v in a.columns and v in b.columns]
    if not common_vars:
        return (
            pd.DataFrame(columns=["datetime"] + vars_keep),
            pd.DataFrame(columns=["datetime"] + vars_keep),
            pd.Timestamp("2001-01-01"),
            pd.Timestamp("2001-12-31 23:00:00"),
        )

    cols = ["month", "day", "hour"] + common_vars
    m = a[cols + ["datetime_plot"]].merge(
        b[cols],
        on=["month", "day", "hour"],
        how="inner",
        suffixes=("_a", "_b"),
    )

    # Build aligned dataframes on synthetic datetime for plotting
    m = m.sort_values("datetime_plot").reset_index(drop=True)

    out_a = pd.DataFrame({"datetime": m["datetime_plot"]})
    out_b = pd.DataFrame({"datetime": m["datetime_plot"]})
    for v in common_vars:
        out_a[v] = pd.to_numeric(m[f"{v}_a"], errors="coerce")
        out_b[v] = pd.to_numeric(m[f"{v}_b"], errors="coerce")

    start = out_a["datetime"].min()
    end = out_a["datetime"].max()
    return out_a, out_b, pd.Timestamp(start), pd.Timestamp(end)


def _ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    if "datetime" not in df.columns:
        raise ValueError("TMY dataframe must contain a 'datetime' column.")
    out = df.copy()
    out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce")
    out = out.dropna(subset=["datetime"]).reset_index(drop=True)
    return out


def to_hourly_bins(
    df: pd.DataFrame,
    how_map: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Robust hourly harmonization:
    - parse datetime
    - floor to hour (datetime_hour)
    - aggregate numeric columns by hour

    This avoids strict timestamp mismatches (:30 vs :00).
    """
    df = _ensure_datetime(df)
    how_map = how_map or {}

    out = df.copy()
    out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce")
    out = out.dropna(subset=["datetime"])

    # Hour bin key
    out["datetime_hour"] = out["datetime"].dt.floor("h")  # <-- 'h' not 'H'

    numeric_cols = [c for c in out.columns if c not in ["datetime", "datetime_hour"]
                    and pd.api.types.is_numeric_dtype(out[c])]

    if not numeric_cols:
        return out[["datetime_hour"]].drop_duplicates().rename(columns={"datetime_hour": "datetime"}).reset_index(drop=True)

    agg = {c: how_map.get(c, "mean") for c in numeric_cols}

    g = out.groupby("datetime_hour", as_index=False).agg(agg)
    g = g.rename(columns={"datetime_hour": "datetime"}).sort_values("datetime").reset_index(drop=True)
    return g


def align_common_period_hourly(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    vars_keep: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]:
    """
    - Keep common period [max(start), min(end)]
    - Merge on datetime to ensure perfect alignment
    - Keep only vars_keep present in both
    """
    df_a = _ensure_datetime(df_a)
    df_b = _ensure_datetime(df_b)

    start = max(df_a["datetime"].min(), df_b["datetime"].min())
    end = min(df_a["datetime"].max(), df_b["datetime"].max())

    a = df_a[(df_a["datetime"] >= start) & (df_a["datetime"] <= end)].copy()
    b = df_b[(df_b["datetime"] >= start) & (df_b["datetime"] <= end)].copy()

    common_vars = [v for v in vars_keep if v in a.columns and v in b.columns]
    cols_a = ["datetime"] + common_vars
    cols_b = ["datetime"] + common_vars

    m = a[cols_a].merge(
        b[cols_b],
        on="datetime",
        how="inner",
        suffixes=("_a", "_b"),
    ).sort_values("datetime")

    # Rebuild aligned dfs
    out_a = pd.DataFrame({"datetime": m["datetime"]})
    out_b = pd.DataFrame({"datetime": m["datetime"]})
    for v in common_vars:
        out_a[v] = pd.to_numeric(m[f"{v}_a"], errors="coerce")
        out_b[v] = pd.to_numeric(m[f"{v}_b"], errors="coerce")

    # Drop rows where all compared vars are NaN (rare but possible)
    if common_vars:
        mask_any = ~(out_a[common_vars].isna().all(axis=1) | out_b[common_vars].isna().all(axis=1))
        out_a = out_a[mask_any].reset_index(drop=True)
        out_b = out_b[mask_any].reset_index(drop=True)

    return out_a, out_b, pd.Timestamp(start), pd.Timestamp(end)


# =============================================================================
# Metrics
# =============================================================================
def _safe_pct(a: np.ndarray, b: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    """
    Percent difference |a-b|/|b| * 100 with protection against near-zero denominator.
    """
    denom = np.where(np.abs(b) > eps, np.abs(b), np.nan)
    return (np.abs(a - b) / denom) * 100.0


def compute_metrics(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    vars_to_compare: List[str],
    threshold_mean_pct: float = 5.0,
) -> Tuple[pd.DataFrame, bool]:
    """
    Metrics per variable, computed on aligned hourly series.
    """
    rows = []
    alert = False

    for v in vars_to_compare:
        if v not in df_a.columns or v not in df_b.columns:
            continue

        a = pd.to_numeric(df_a[v], errors="coerce").to_numpy(dtype=float)
        b = pd.to_numeric(df_b[v], errors="coerce").to_numpy(dtype=float)

        # Pairwise valid
        mask = np.isfinite(a) & np.isfinite(b)
        if mask.sum() == 0:
            rows.append({
                "variable": v,
                "n": 0,
                "mean_a": np.nan,
                "mean_b": np.nan,
                "bias_mean": np.nan,      # mean(a-b)
                "mae": np.nan,
                "rmse": np.nan,
                "mean_pct": np.nan,       # mean(|a-b|/|b|*100)
                "max_pct": np.nan,
                "max_abs": np.nan,
            })
            continue

        aa = a[mask]
        bb = b[mask]
        diff = aa - bb
        absdiff = np.abs(diff)
        pct = _safe_pct(aa, bb)

        mae = float(np.nanmean(absdiff))
        rmse = float(np.sqrt(np.nanmean(diff ** 2)))
        mean_pct = float(np.nanmean(pct))
        max_pct = float(np.nanmax(pct))
        max_abs = float(np.nanmax(absdiff))
        bias_mean = float(np.nanmean(diff))

        if np.isfinite(mean_pct) and mean_pct > threshold_mean_pct:
            alert = True

        rows.append({
            "variable": v,
            "n": int(mask.sum()),
            "mean_a": float(np.nanmean(aa)),
            "mean_b": float(np.nanmean(bb)),
            "bias_mean": bias_mean,
            "mae": mae,
            "rmse": rmse,
            "mean_pct": mean_pct,
            "max_pct": max_pct,
            "max_abs": max_abs,
        })

    metrics = pd.DataFrame(rows)
    if not metrics.empty:
        metrics = metrics.sort_values("variable").reset_index(drop=True)

    return metrics, alert


# =============================================================================
# PDF report (simple 1 page)
# =============================================================================
def generate_compare_pdf_onepage(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    label_a: str,
    label_b: str,
    reader_a: str,
    reader_b: str,
    step_a_min: int,
    step_b_min: int,
    used_step_min: int,
    units_a: Dict[str, str],
    units_b: Dict[str, str],
    metrics: pd.DataFrame,
    energy_a: EnergySummary,
    energy_b: EnergySummary,
    energy_a_common: EnergySummary,
    energy_b_common: EnergySummary,
    alert_flag: bool,
    output_pdf: Path,
) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.suptitle("TMY Comparison Report", fontsize=16, fontweight="bold", y=0.97)

    # --- Header block
    ax0 = fig.add_axes([0.06, 0.83, 0.88, 0.12])
    ax0.axis("off")

    txt = ""
    txt += f"A: {label_a}\n"
    txt += f"B: {label_b}\n"
    txt += f"Readers: {reader_a.upper()} vs {reader_b.upper()}\n"
    txt += f"Time steps: A={step_a_min} min, B={step_b_min} min → used {used_step_min} min\n"
    txt += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    txt += "\n"

    # Energy summary (full datasets)
    if energy_a.annual_ghi is not None and energy_b.annual_ghi is not None:
        txt += f"Annual GHI (full): {energy_a.annual_ghi:.1f} vs {energy_b.annual_ghi:.1f} {energy_a.unit}\n"
    if energy_a.annual_dni is not None and energy_b.annual_dni is not None:
        txt += f"Annual DNI (full): {energy_a.annual_dni:.1f} vs {energy_b.annual_dni:.1f} {energy_a.unit}\n"
    if energy_a.annual_dhi is not None and energy_b.annual_dhi is not None:
        txt += f"Annual DHI (full): {energy_a.annual_dhi:.1f} vs {energy_b.annual_dhi:.1f} {energy_a.unit}\n"

    # # Energy summary (common period)
    # if energy_a_common.annual_ghi is not None and energy_b_common.annual_ghi is not None:
    #     txt += f"Annual GHI (common): {energy_a_common.annual_ghi:.1f} vs {energy_b_common.annual_ghi:.1f} {energy_a_common.unit}\n"

    txt += "\n"
    txt += "ALERT: Significant discrepancies detected.\n" if alert_flag else "OK: Differences look consistent.\n"

    ax0.text(0.0, 1.0, txt, ha="left", va="top", fontsize=10, family="monospace")

    # --- Plot section (stacked) : keep only 3 plots (more space, no DHI)
    # Remove DHI to avoid crowding and give room for titles
    vars_to_plot = [v for v in ["ghi", "dni", "temp"] if v in df_a.columns and v in df_b.columns]

    # Layout tuned to avoid title overlap with the first plot:
    # - header block ends around y=0.83
    # - we start plots lower (top plot max y ~ 0.72)
    n = len(vars_to_plot)
    if n > 0:
        left = 0.10
        width = 0.80
        height = 0.17
        gap = 0.055
        top = 0.72  # keeps clear space under the header

        for i, var in enumerate(vars_to_plot):
            # i=0 is top plot
            bottom = top - (i + 1) * height - i * gap
            ax = fig.add_axes([left, bottom, width, height])

            ax.plot(df_a["datetime"], df_a[var], lw=0.9, alpha=0.9, label="A")
            ax.plot(df_b["datetime"], df_b[var], lw=0.9, alpha=0.9, label="B")

            u_a = units_a.get(var, "")
            u_b = units_b.get(var, "")
            u = u_a if u_a == u_b else f"{u_a} / {u_b}".strip(" /")

            ax.set_title(f"{var.upper()} ({u})", fontsize=11, pad=10)  # more pad = avoids overlap
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
            ax.grid(True, linestyle="--", alpha=0.35)
            ax.legend(loc="upper right", fontsize=8)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_pdf, dpi=250)
    plt.close(fig)


# =============================================================================
# Main entry
# =============================================================================
def compare_tmy_sources(
    source_a: TextSource,
    name_a: str,
    source_b: TextSource,
    name_b: str,
    outputs_dir: Path,
    output_mode: str = "runs",
    target_irradiance_unit: str = "kW/m²",
    energy_unit: str = "kWh/m²",
    resample_hourly_if_subhourly: bool = True,
    threshold_mean_pct: float = 5.0,
    force_hourly_step_minutes: int = 60,
) -> TMYCompareResult:
    tool_name = "TMY_Compare"
    run: RunPaths = make_run_folders(outputs_dir, tool_name=tool_name, mode=output_mode)

    # --- Read NATIF (sans resample) uniquement pour récupérer le pas de temps
    ds_a_native, _ = _read_tmy_auto(
        source=source_a,
        source_name=name_a,
        target_irradiance_unit=target_irradiance_unit,
        resample_hourly_if_subhourly=False,
    )
    ds_b_native, _ = _read_tmy_auto(
        source=source_b,
        source_name=name_b,
        target_irradiance_unit=target_irradiance_unit,
        resample_hourly_if_subhourly=False,
    )

    native_step_a_min = int(ds_a_native.time_step_minutes)
    native_step_b_min = int(ds_b_native.time_step_minutes)

    # --- Read both (auto)
    ds_a, reader_a = _read_tmy_auto(
        source=source_a,
        source_name=name_a,
        target_irradiance_unit=target_irradiance_unit,
        resample_hourly_if_subhourly=resample_hourly_if_subhourly,
    )
    ds_b, reader_b = _read_tmy_auto(
        source=source_b,
        source_name=name_b,
        target_irradiance_unit=target_irradiance_unit,
        resample_hourly_if_subhourly=resample_hourly_if_subhourly,
    )
    log.debug("TMY compare readers: A=%s, B=%s", reader_a, reader_b)

    used_step_min = 60 if resample_hourly_if_subhourly else min(native_step_a_min, native_step_b_min)

    # --- Force hourly (even if already)
    # Default aggregation rules (if you want sums for precipitation later, add a how_map)
    how_map = {"ghi": "mean", "dni": "mean", "dhi": "mean", "temp": "mean", "wind_speed": "mean"}
    df_a_hour = to_hourly_bins(ds_a.df, how_map=how_map)
    df_b_hour = to_hourly_bins(ds_b.df, how_map=how_map)

    # --- Align to common period and ensure time alignment
    vars_keep = ["ghi", "dni", "dhi", "temp", "wind_speed"]
    df_a_aligned, df_b_aligned, start, end = align_common_period_hourly(
        df_a_hour, df_b_hour, vars_keep=vars_keep
    )

    # Fallback: if no overlap in real datetime, compare using climatology keys (month/day/hour)
    if len(df_a_aligned) == 0 or len(df_b_aligned) == 0:
        log.warning("No overlap on datetime; falling back to climatological alignment (month/day/hour).")
        df_a_aligned, df_b_aligned, start, end = align_climatology_hourly(
            df_a_hour, df_b_hour, vars_keep=vars_keep
        )

    # If still empty, THEN it's a real problem
    if len(df_a_aligned) == 0 or len(df_b_aligned) == 0:
        raise ValueError(
            "No common timestamps found (even with climatological alignment). "
            "Check that both files contain comparable time series and variables."
        )

    # --- Metrics
    common_vars = [v for v in vars_keep if v in df_a_aligned.columns and v in df_b_aligned.columns]
    metrics, alert_flag = compute_metrics(
        df_a_aligned, df_b_aligned,
        vars_to_compare=common_vars,
        threshold_mean_pct=threshold_mean_pct,
    )

    # --- Energy (full datasets)
    energy_a = annual_irradiation(
        ds_a.df,
        units_by_col=ds_a.units_by_col,
        step_minutes=ds_a.time_step_minutes,
        energy_unit=energy_unit,
    )
    energy_b = annual_irradiation(
        ds_b.df,
        units_by_col=ds_b.units_by_col,
        step_minutes=ds_b.time_step_minutes,
        energy_unit=energy_unit,
    )

    # --- Energy (common aligned period) -> use hourly step
    # (Units: keep dataset's units_by_col; step is 60)
    energy_a_common = annual_irradiation(
        df_a_aligned,
        units_by_col=ds_a.units_by_col,
        step_minutes=force_hourly_step_minutes,
        energy_unit=energy_unit,
    )
    energy_b_common = annual_irradiation(
        df_b_aligned,
        units_by_col=ds_b.units_by_col,
        step_minutes=force_hourly_step_minutes,
        energy_unit=energy_unit,
    )

    # --- Warnings (keep it clean)
    warnings_all = (
        ds_a.warnings
        + ds_b.warnings
        + energy_a.warnings
        + energy_b.warnings
        + energy_a_common.warnings
        + energy_b_common.warnings
    )

    # --- PDF
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pdf_path = run.reports_dir / f"TMY_Comparison__{Path(name_a).stem}__VS__{Path(name_b).stem}__{ts}.pdf"
    generate_compare_pdf_onepage(
        df_a=df_a_aligned,
        df_b=df_b_aligned,
        label_a=ds_a.source_name,
        label_b=ds_b.source_name,
        reader_a=reader_a,
        reader_b=reader_b,
        step_a_min=int(ds_a_native.time_step_minutes),
        step_b_min=int(ds_b_native.time_step_minutes),
        used_step_min=force_hourly_step_minutes,
        units_a=ds_a.units_by_col,
        units_b=ds_b.units_by_col,
        metrics=metrics,
        energy_a=energy_a,
        energy_b=energy_b,
        energy_a_common=energy_a_common,
        energy_b_common=energy_b_common,
        alert_flag=alert_flag,
        output_pdf=pdf_path,
    )

    # --- Log
    log_path = run.logs_dir / f"TMY_Compare__{Path(name_a).stem}__VS__{Path(name_b).stem}__{ts}.log"
    write_run_log(
        log_path=log_path,
        tool_name=tool_name,
        sources=[name_a, name_b],
        header_info={
            "reader_a": reader_a,
            "reader_b": reader_b,
            "file_a": ds_a.source_name,
            "file_b": ds_b.source_name,
            "step_a_min": int(ds_a.time_step_minutes),
            "step_b_min": int(ds_b.time_step_minutes),
            "used_step_min": force_hourly_step_minutes,
            "common_start": str(start),
            "common_end": str(end),
        },
        units_by_col={
            "A": ds_a.units_by_col,
            "B": ds_b.units_by_col,
        },
        time_step_minutes=force_hourly_step_minutes,
        quality=None,
        warnings=warnings_all,
    )

    # --- Dataset out (attach merged warnings so UI sees everything)
    ds_a_out = TMYDataset(
        df=ds_a.df,
        header_info=ds_a.header_info,
        units_by_col=ds_a.units_by_col,
        time_step_minutes=ds_a.time_step_minutes,
        quality=ds_a.quality,
        source_name=ds_a.source_name,
        warnings=warnings_all,
    )
    ds_b_out = TMYDataset(
        df=ds_b.df,
        header_info=ds_b.header_info,
        units_by_col=ds_b.units_by_col,
        time_step_minutes=ds_b.time_step_minutes,
        quality=ds_b.quality,
        source_name=ds_b.source_name,
        warnings=warnings_all,
    )

    return TMYCompareResult(
        ds_a=ds_a_out,
        ds_b=ds_b_out,
        native_step_a_min=native_step_a_min,
        native_step_b_min=native_step_b_min,
        used_step_min=int(used_step_min),
        df_a=df_a_aligned,
        df_b=df_b_aligned,
        common_start=start,
        common_end=end,
        metrics=metrics,
        energy_a=energy_a,
        energy_b=energy_b,
        energy_a_common=energy_a_common,
        energy_b_common=energy_b_common,
        alert_flag=alert_flag,
        report_pdf=pdf_path,
        log_path=log_path,
        run_dir=run.run_dir,
    )
