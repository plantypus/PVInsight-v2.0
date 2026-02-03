# core/meteo/tmy_analysis.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union, Tuple, List

import math
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
from utils.readers.tmy_solargis import read_tmy_solargis  # <-- new reader

import logging

log = logging.getLogger(__name__)

TextSource = Union[str, Path, bytes]


# -----------------------------------------------------------------------------
# Result object
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class TMYAnalysisResult:
    dataset: TMYDataset
    stats: pd.DataFrame
    stats_pretty: pd.DataFrame
    ghi_distribution: pd.DataFrame  # always computed in W/m²
    energy: EnergySummary
    report_pdf: Path
    log_path: Path
    run_dir: Path


# -----------------------------------------------------------------------------
# Stats helpers
# -----------------------------------------------------------------------------
def compute_basic_stats(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["ghi", "dni", "dhi", "temp"] if c in df.columns]
    if not cols:
        return pd.DataFrame(columns=["Mean", "Min", "Max"])
    stats = df[cols].agg(["mean", "min", "max"]).transpose()
    stats = stats.rename(columns={"mean": "Mean", "min": "Min", "max": "Max"})
    return stats


def _human_label(col: str, units_by_col: Dict[str, str]) -> str:
    u = units_by_col.get(col, "") or ""
    if col == "ghi":
        return f"GHI ({u})".strip()
    if col == "dni":
        return f"DNI ({u})".strip()
    if col == "dhi":
        return f"DHI ({u})".strip()
    if col == "temp":
        return f"Température ({u})".strip()
    return f"{col} ({u})".strip()


def make_pretty_stats_table(stats: pd.DataFrame, units_by_col: Dict[str, str]) -> pd.DataFrame:
    if stats.empty:
        return pd.DataFrame(columns=["Variable", "Moyenne", "Min", "Max"])

    out = stats.copy()
    out = out.rename(columns={"Mean": "Moyenne", "Min": "Min", "Max": "Max"})
    for c in ["Moyenne", "Min", "Max"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").round(2)

    out.insert(0, "Variable", [_human_label(idx, units_by_col) for idx in out.index])
    out = out.reset_index(drop=True)
    return out


# -----------------------------------------------------------------------------
# Distributions (always computed in W/m²)
# -----------------------------------------------------------------------------
def compute_ghi_distribution(
    df: pd.DataFrame,
    units_by_col: Dict[str, str],
    bin_width: int = 200,
) -> pd.DataFrame:
    if "ghi" not in df.columns:
        return pd.DataFrame(columns=["Classe", "N", "%"])

    s = pd.to_numeric(df["ghi"], errors="coerce")
    s = s[s > 0].dropna()
    if s.empty:
        return pd.DataFrame(columns=["Classe", "N", "%"])

    vmax = float(s.max())
    vmax = max(vmax, float(bin_width))
    upper = int(math.ceil(vmax / bin_width) * bin_width)

    bins = list(range(0, upper + bin_width, bin_width))
    labels = [f"{bins[i]}–{bins[i + 1]}" for i in range(len(bins) - 1)]

    cats = pd.cut(s, bins=bins, right=True, include_lowest=False, labels=labels)
    counts = cats.value_counts(dropna=False).reindex(labels, fill_value=0)

    total = int(counts.sum())
    pct = (counts / total * 100.0).round(1) if total > 0 else counts.astype(float)

    classe = [f"[{lab}] W/m²" for lab in labels]
    return pd.DataFrame({"Classe": classe, "N": counts.values, "%": pct.values})


def _df_irradiance_as_wm2(
    df: pd.DataFrame,
    units_by_col: Dict[str, str],
) -> Tuple[pd.DataFrame, Dict[str, str], List[str]]:
    conv = convert_irradiance_units(df, units_by_col, target_unit="W/m²")
    return conv.df, conv.units_by_col, conv.warnings


# -----------------------------------------------------------------------------
# Reader selection (auto)
# -----------------------------------------------------------------------------
def _read_tmy_auto(
    source: TextSource,
    source_name: str,
    target_irradiance_unit: str,
    resample_hourly_if_subhourly: bool,
) -> Tuple[TMYDataset, str, List[str]]:
    """
    Tries PVSyst first, then SolarGIS.

    Returns:
        (dataset, reader_name, warnings_extra)

    Design choice:
    - Reader detection failures are considered NORMAL and silent.
    - warnings_extra is only populated if ALL readers fail.
    """
    last_error: Exception | None = None

    # 1) Try PVSyst (silent on failure)
    try:
        ds = read_tmy_pvsyst(
            source,
            source_name=source_name,
            target_irradiance_unit=target_irradiance_unit,
            resample_hourly_if_subhourly=resample_hourly_if_subhourly,
        )
        return ds, "pvsyst", []
    except Exception as e:
        last_error = e

    # 2) Try SolarGIS (silent on failure)
    try:
        ds = read_tmy_solargis(
            source,
            source_name=source_name,
            target_irradiance_unit=target_irradiance_unit,
            resample_hourly_if_subhourly=resample_hourly_if_subhourly,
        )
        return ds, "solargis", []
    except Exception as e:
        last_error = e

    # 3) No reader succeeded → REAL error
    msg = (
        "Unable to read TMY file with supported readers (PVSyst, SolarGIS).\n"
        f"Last error: {type(last_error).__name__}: {last_error}"
    )
    raise ValueError(msg)


# -----------------------------------------------------------------------------
# PDF (more space between figures)
# -----------------------------------------------------------------------------
def generate_pdf_onepage(
    df: pd.DataFrame,
    stats: pd.DataFrame,
    energy: EnergySummary,
    units_by_col: Dict[str, str],
    quality: DataQuality,
    file_label: str,
    output_pdf: Path,
    source_kind: str = "TMY",
) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
    fig.suptitle(f"TMY Report ({source_kind})", fontsize=18, fontweight="bold", y=0.965)

    # --- File info ---
    ax0 = fig.add_axes([0.06, 0.87, 0.88, 0.075])
    ax0.axis("off")
    header = (
        f"File: {file_label}\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    ax0.text(0.0, 0.6, header, ha="left", va="center", fontsize=10, family="monospace")

    # --- Data quality ---
    ax1 = fig.add_axes([0.06, 0.71, 0.88, 0.16])
    ax1.axis("off")
    dq_text = "DATA QUALITY\n\n"
    dq_text += f"Rows: {quality.n_rows:,}\n"
    dq_text += f"Period: {quality.start}  →  {quality.end}\n"
    if quality.n_nan == 0 and quality.n_nat == 0:
        dq_text += "Missing values: none\n"
    else:
        dq_text += f"Missing values: {quality.n_nan} NaN, {quality.n_nat} NaT\n"
    if quality.warning:
        dq_text += f"\nWarning: {quality.warning}\n"
    ax1.text(0.0, 0.95, dq_text, ha="left", va="top", fontsize=10, family="monospace")

    # --- Stats + Energy ---
    ax2 = fig.add_axes([0.06, 0.60, 0.88, 0.16])
    ax2.axis("off")
    st_text = "STATISTICS (mean / min / max)\n\n"
    for var in ["ghi", "dni", "dhi", "temp"]:
        if var in stats.index:
            unit = units_by_col.get(var, "")
            mean, mn, mx = stats.loc[var, ["Mean", "Min", "Max"]]
            st_text += f"{var.upper():<6} {mean:>10.2f} {unit}   (min {mn:.2f}, max {mx:.2f})\n"

    st_text += "\nANNUAL IRRADIATION (integrated)\n"
    if energy.annual_ghi is not None:
        st_text += f"GHI: {energy.annual_ghi:.1f} {energy.unit}\n"
    if energy.annual_dni is not None:
        st_text += f"DNI: {energy.annual_dni:.1f} {energy.unit}\n"
    if energy.annual_dhi is not None:
        st_text += f"DHI: {energy.annual_dhi:.1f} {energy.unit}\n"
    ax2.text(0.0, 0.95, st_text, ha="left", va="top", fontsize=10, family="monospace")

    # --- Plot 1: GHI ---
    if "ghi" in df.columns and "datetime" in df.columns:
        ax3 = fig.add_axes([0.10, 0.36, 0.80, 0.16])  # a bit shorter
        ax3.set_title("Global Horizontal Irradiance (GHI)", fontsize=12, pad=10)
        ax3.plot(df["datetime"], df["ghi"], lw=1.0)
        ax3.xaxis.set_major_locator(mdates.MonthLocator())
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax3.set_xlabel("Month")
        ax3.set_ylabel(f"GHI ({units_by_col.get('ghi','')})")
        ax3.grid(True, linestyle="--", alpha=0.35)

    # --- Plot 2: Temperature (lower + extra title padding) ---
    if "temp" in df.columns and "datetime" in df.columns:
        ax4 = fig.add_axes([0.10, 0.10, 0.80, 0.16])  # moved down + more gap
        ax4.set_title("Ambient Temperature", fontsize=12, pad=16)
        ax4.plot(df["datetime"], df["temp"], lw=1.0)
        ax4.xaxis.set_major_locator(mdates.MonthLocator())
        ax4.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax4.set_xlabel("Month")
        ax4.set_ylabel(f"Temp ({units_by_col.get('temp','')})")
        ax4.grid(True, linestyle="--", alpha=0.35)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_pdf, dpi=250)
    plt.close(fig)


# -----------------------------------------------------------------------------
# Main entry
# -----------------------------------------------------------------------------
def analyze_tmy_source(
    source: TextSource,
    source_name: str,
    outputs_dir: Path,
    output_mode: str = "flat",
    target_irradiance_unit: str = "kW/m²",
    energy_unit: str = "kWh/m²",
    resample_hourly_if_subhourly: bool = True,
    add_timestamp_to_outputs: bool = True,
) -> TMYAnalysisResult:
    tool_name = "TMY_Analysis"
    run: RunPaths = make_run_folders(outputs_dir, tool_name=tool_name, mode=output_mode)

    # Auto-detect reader, but keep user's irradiance unit for the main dataset (stats/curves/PDF)
    dataset, reader_name, reader_warnings = _read_tmy_auto(
        source=source,
        source_name=source_name,
        target_irradiance_unit=target_irradiance_unit,
        resample_hourly_if_subhourly=resample_hourly_if_subhourly,
    )
    # INFO INTERNE (debug uniquement)
    log.debug("TMY reader selected: %s", reader_name)

    stats = compute_basic_stats(dataset.df)
    stats_pretty = make_pretty_stats_table(stats, dataset.units_by_col)

    energy = annual_irradiation(
        dataset.df,
        units_by_col=dataset.units_by_col,
        step_minutes=dataset.time_step_minutes,
        energy_unit=energy_unit,
    )

    # Distribution must be computed in W/m² only (bins meaningful)
    df_wm2, units_wm2, conv_warn = _df_irradiance_as_wm2(dataset.df, dataset.units_by_col)
    ghi_distribution = compute_ghi_distribution(df_wm2, units_wm2, bin_width=200)

    dataset_warnings = (
        dataset.warnings
        + energy.warnings
        + conv_warn
    )

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") if add_timestamp_to_outputs else ""
    suffix = f"__{ts}" if ts else ""

    pdf_path = run.reports_dir / f"{Path(source_name).stem}__TMY_Report{suffix}.pdf"
    generate_pdf_onepage(
        dataset.df,
        stats,
        energy,
        dataset.units_by_col,
        dataset.quality,
        file_label=dataset.source_name,
        output_pdf=pdf_path,
        source_kind=reader_name.upper(),
    )

    log_path = run.logs_dir / f"{Path(source_name).stem}__TMY_Analysis{suffix}.log"
    write_run_log(
        log_path=log_path,
        tool_name=tool_name,
        sources=[source_name],
        header_info=dataset.header_info,
        units_by_col=dataset.units_by_col,
        time_step_minutes=dataset.time_step_minutes,
        quality=dataset.quality,
        warnings=dataset_warnings,
    )

    dataset_out = TMYDataset(
        df=dataset.df,
        header_info=dataset.header_info,
        units_by_col=dataset.units_by_col,
        time_step_minutes=dataset.time_step_minutes,
        quality=dataset.quality,
        source_name=dataset.source_name,
        warnings=dataset_warnings,
    )

    return TMYAnalysisResult(
        dataset=dataset_out,
        stats=stats,
        stats_pretty=stats_pretty,
        ghi_distribution=ghi_distribution,
        energy=energy,
        report_pdf=pdf_path,
        log_path=log_path,
        run_dir=run.run_dir,
    )
