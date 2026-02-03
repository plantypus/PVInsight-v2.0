# core/production/hourly_export_excel.py
from __future__ import annotations

from pathlib import Path
import pandas as pd

from .hourly_models import AnalysisContext
from utils import format_number


def export_excel(context: AnalysisContext, output: Path) -> None:
    """
    English-only Excel report:
    - Summary (Global production + Threshold + Night consumption)
    - Threshold tables (monthly, seasonal, monthly %)
    - Power distribution (if available)
    - Hourly raw data
    - Units
    """
    thr_res = context.results.get("threshold")
    if not thr_res or not thr_res.get("available", False):
        raise ValueError("Missing 'threshold' analysis — cannot export Excel.")

    gp_res = context.results.get("global_production", {})
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        _export_summary(writer, context, gp_res, thr_res)
        _export_threshold_excel(writer, workbook, thr_res)

        pd_res = context.results.get("power_distribution")
        if pd_res and pd_res.get("available", False) and not pd_res.get("empty", False):
            _export_power_distribution_excel(writer, pd_res)

        context.df_raw.to_excel(writer, sheet_name="Hourly data", index=True)
        _export_units(writer, context)


def _export_summary(writer, context: AnalysisContext, gp_res: dict, thr_res: dict) -> None:
    thr = thr_res["summary"]

    # Global production (optional)
    gp_summary = {}
    if gp_res and gp_res.get("available", False):
        gp_summary = gp_res.get("summary", {}) or {}

    df = pd.DataFrame({
        "Key": [
            "PVSyst version",
            "Input file",
            "Simulation date",
            "Project",
            "Variant",
            "Threshold column",
            "Threshold value",
            "Night disconnection",

            # Global production
            "Operating hours",
            "Operating share (%)",
            "Net production (kWh)",
            "Production without import (kWh)",
            "Night consumption (kWh)",
            "Import hours",

            # Threshold
            "Hours above threshold",
            "Share of operating time above threshold (%)",
            "Energy above threshold (kWh)",
        ],
        "Value": [
            context.general_info.get("PVSyst_version", ""),
            context.input_file.name,
            context.general_info.get("Simulation_date", ""),
            context.general_info.get("Project_name", ""),
            context.general_info.get("Variant_name", ""),
            thr.get("threshold_column", ""),
            format_number(thr.get("threshold_value", 0.0), 2),
            str(bool(thr.get("night_disconnection", False))),

            # Global production
            format_number(gp_summary.get("operating_hours", float("nan")), 0) if gp_summary else "",
            f"{gp_summary.get('operating_pct', float('nan')):.1f}" if gp_summary and gp_summary.get("operating_pct") is not None else "",
            format_number(gp_summary.get("net_production_kwh", float("nan")), 0) if gp_summary else "",
            format_number(gp_summary.get("production_without_import_kwh", float("nan")), 0) if gp_summary else "",
            format_number(gp_summary.get("night_consumption_kwh", float("nan")), 0) if gp_summary else "",
            format_number(gp_summary.get("import_hours", float("nan")), 0) if gp_summary else "",

            # Threshold
            format_number(thr.get("hours_above", float("nan")), 0),
            f"{thr.get('pct_above_operating_time', 0.0):.1f}",
            format_number(thr.get("energy_above_kwh", float("nan")), 0),
        ],
    })

    df.to_excel(writer, sheet_name="Summary", index=False)


def _export_threshold_excel(writer, workbook, res: dict) -> None:
    monthly = res.get("monthly")
    seasonal = res.get("seasonal")
    monthly_pct = res.get("monthly_pct")
    night_monthly = res.get("night_consumption_monthly")

    # Monthly
    if monthly is not None and not monthly.empty:
        sheet_month = "Threshold — Monthly"
        monthly.to_excel(writer, sheet_name=sheet_month, index=False)
        ws = writer.sheets[sheet_month]

        chart_month = workbook.add_chart({"type": "column"})
        chart_month.add_series({
            "name": "Hours above threshold",
            "categories": [sheet_month, 1, 0, monthly.shape[0], 0],
            "values":     [sheet_month, 1, 1, monthly.shape[0], 1],
        })
        chart_month.set_title({"name": "Monthly — Hours above threshold"})
        chart_month.set_x_axis({"name": "Month"})
        chart_month.set_y_axis({"name": "Hours"})
        ws.insert_chart("E2", chart_month)

    # Seasonal
    if seasonal is not None and not seasonal.empty:
        sheet_season = "Threshold — Seasonal"
        seasonal.to_excel(writer, sheet_name=sheet_season, index=False)
        ws = writer.sheets[sheet_season]

        chart_season = workbook.add_chart({"type": "column"})
        chart_season.add_series({
            "name": "Hours above threshold",
            "categories": [sheet_season, 1, 0, seasonal.shape[0], 0],
            "values":     [sheet_season, 1, 1, seasonal.shape[0], 1],
        })
        chart_season.set_title({"name": "Seasonal — Hours above threshold"})
        chart_season.set_x_axis({"name": "Season"})
        chart_season.set_y_axis({"name": "Hours"})
        ws.insert_chart("E2", chart_season)

    # Monthly share
    if monthly_pct is not None and not monthly_pct.empty:
        df_pct = monthly_pct.copy()
        df_pct["Share above threshold"] = df_pct["pct_above"].map(lambda x: f"{x:.1f} %")
        df_pct[["month_name", "Share above threshold"]].to_excel(
            writer, sheet_name="Threshold — Monthly share", index=False
        )

    # Night consumption monthly
    if night_monthly is not None and not night_monthly.empty:
        night_monthly.to_excel(writer, sheet_name="Night consumption — Monthly", index=False)


def _export_power_distribution_excel(writer, res: dict) -> None:
    df = res["summary"].copy()
    df_disp = pd.DataFrame({
        "Class": df["class"].astype(str),
        "Hours": df["hours"].map(lambda x: format_number(x, 0)),
        "Share of time": df["pct_time"].map(lambda x: f"{x:.1f} %"),
        "Energy (kWh)": df["energy_kwh"].map(lambda x: format_number(x, 0)),
    })
    df_disp.to_excel(writer, sheet_name="Power distribution", index=False)


def _export_units(writer, context: AnalysisContext) -> None:
    df_units = pd.DataFrame(
        [{"Parameter": k, "Unit": v} for k, v in context.units_map.items()]
    )
    df_units.to_excel(writer, sheet_name="Units", index=False)
