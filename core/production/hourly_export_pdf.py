# core/production/hourly_export_pdf.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import tempfile

import matplotlib.pyplot as plt

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

from .hourly_models import AnalysisContext
from config import APP_NAME
from utils import format_number


def _styled_table(data, col_widths):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _generate_bar_chart(categories, values, title: str, ylabel: str, output_png: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    ax.bar(categories, values)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=9)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_png, dpi=200)
    plt.close(fig)
    return output_png


def export_pdf(context: AnalysisContext, pdf_path: Path) -> None:
    """
    English-only PDF report:
    - General summary (global production + threshold + night consumption)
    - Threshold monthly table + chart
    - Monthly share above threshold
    - Power distribution (if available)
    """
    thr_res = context.results.get("threshold")
    if not thr_res or not thr_res.get("available", False):
        raise ValueError("Missing 'threshold' analysis — cannot generate PDF.")
    thr = thr_res["summary"]

    gp_res = context.results.get("global_production", {})
    gp = gp_res.get("summary", {}) if gp_res and gp_res.get("available", False) else {}

    monthly = thr_res.get("monthly")
    monthly_pct = thr_res.get("monthly_pct")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        chart_png = tmpdir / f"{pdf_path.stem}_monthly.png"

        if monthly is not None and not monthly.empty:
            _generate_bar_chart(
                categories=monthly["month_name"].tolist(),
                values=monthly["hours_above"].tolist(),
                title="Monthly distribution — hours above threshold",
                ylabel="Hours",
                output_png=chart_png,
            )
        else:
            # still create an empty image placeholder
            _generate_bar_chart([], [], "Monthly distribution — hours above threshold", "Hours", chart_png)

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        elems = []

        elems.append(Paragraph(f"<b>{APP_NAME}</b>", styles["Title"]))
        elems.append(Spacer(1, 10))

        # General summary
        elems.append(Paragraph("<b>General summary</b>", styles["Heading2"]))
        elems.append(Spacer(1, 6))

        synth = [
            ["PVSyst version", context.general_info.get("PVSyst_version", "")],
            ["Input file", context.input_file.name],
            ["Simulation date", context.general_info.get("Simulation_date", "")],
            ["Project", context.general_info.get("Project_name", "")],
            ["Variant", context.general_info.get("Variant_name", "")],

            ["Threshold column", thr.get("threshold_column", "")],
            ["Threshold value", format_number(thr.get("threshold_value", 0.0), 2)],
            ["Night disconnection", str(bool(thr.get("night_disconnection", False)))],

            # Global production
            ["Operating hours", format_number(gp.get("operating_hours", 0.0), 0) if gp else ""],
            ["Operating share (%)", f"{gp.get('operating_pct', 0.0):.1f}" if gp else ""],
            ["Net production (kWh)", format_number(gp.get("net_production_kwh", 0.0), 0) if gp else ""],
            ["Production w/o import (kWh)", format_number(gp.get("production_without_import_kwh", 0.0), 0) if gp else ""],
            ["Night consumption (kWh)", format_number(gp.get("night_consumption_kwh", 0.0), 0) if gp else ""],
            ["Import hours", format_number(gp.get("import_hours", 0.0), 0) if gp else ""],

            # Threshold
            ["Hours above threshold", format_number(thr.get("hours_above", 0.0), 0)],
            ["Share above threshold (%)", f"{thr.get('pct_above_operating_time', 0.0):.1f}"],
            ["Energy above threshold (kWh)", format_number(thr.get("energy_above_kwh", 0.0), 0)],
            ["Night import hours", format_number(thr.get("night_import_hours", 0.0), 0)],
            ["Night consumption (kWh)", format_number(thr.get("night_consumption_kwh", 0.0), 0)],
        ]

        elems.append(_styled_table(synth, [8.5 * cm, 5.5 * cm]))
        elems.append(Spacer(1, 10))

        # Monthly table
        elems.append(Paragraph("<b>Threshold — monthly</b>", styles["Heading2"]))
        elems.append(Spacer(1, 6))

        if monthly is not None and not monthly.empty:
            monthly_data = [["Month", "Hours above", "Energy above (kWh)"]]
            for _, row in monthly.iterrows():
                monthly_data.append([
                    row["month_name"],
                    format_number(row["hours_above"], 0),
                    format_number(row["energy_above_kwh"], 0),
                ])
            elems.append(_styled_table(monthly_data, [4.5 * cm, 4.5 * cm, 4.5 * cm]))
            elems.append(Spacer(1, 8))

        # Monthly share table
        if monthly_pct is not None and not monthly_pct.empty:
            elems.append(Paragraph("<b>Monthly share above threshold</b>", styles["Heading3"]))
            elems.append(Spacer(1, 6))

            pct_data = [["Month", "Share (%)"]]
            for _, row in monthly_pct.iterrows():
                pct_data.append([row["month_name"], f"{row['pct_above']:.1f} %"])
            elems.append(_styled_table(pct_data, [6.0 * cm, 6.0 * cm]))
            elems.append(Spacer(1, 8))

        # Chart
        elems.append(Image(str(chart_png), width=13.0 * cm, height=6.0 * cm))

        # Power distribution (optional)
        pd_res = context.results.get("power_distribution")
        if pd_res and pd_res.get("available", False) and not pd_res.get("empty", False):
            elems.append(Spacer(1, 10))
            elems.append(Paragraph("<b>Power distribution</b>", styles["Heading2"]))
            elems.append(Spacer(1, 6))

            dist = pd_res["summary"]
            dist_data = [["Class", "Hours", "Share", "Energy (kWh)"]]
            for _, row in dist.iterrows():
                dist_data.append([
                    str(row["class"]),
                    format_number(row["hours"], 0),
                    f"{row['pct_time']:.1f} %",
                    format_number(row["energy_kwh"], 0),
                ])
            elems.append(_styled_table(dist_data, [4.0 * cm, 3.0 * cm, 3.0 * cm, 4.0 * cm]))

        # Footer timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        def footer(canvas, _doc):
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.grey)
            canvas.drawRightString(19 * cm, 1.2 * cm, now)

        doc.build(elems, onFirstPage=footer, onLaterPages=footer)
