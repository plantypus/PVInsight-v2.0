from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

import calendar
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.bootstrap import configure_page, bootstrap
from ui.tool_layout import tool_header, section
from ui.tool_state import init_tool_state, get, set_
from ui.i18n import t

from core.production.hourly_pipeline import analyze_hourly_source
from core.production.hourly_export_excel import export_excel
from core.production.hourly_export_pdf import export_pdf

from config import REPORTS_SUBDIR, LOGS_SUBDIR
from utils import format_number


configure_page(page_title="Hourly Results Analysis", page_icon="📈", layout="wide")

TOOL_ID = "hourly_results_analysis"

paths = bootstrap(render_sidebar_ui=True)
OUTPUTS_DIR = paths.outputs

REPORTS_DIR = OUTPUTS_DIR / REPORTS_SUBDIR
LOGS_DIR = OUTPUTS_DIR / LOGS_SUBDIR
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

init_tool_state(
    TOOL_ID,
    defaults={
        "add_timestamp_to_outputs": True,
        "threshold_column": "E_Grid",
        "threshold_value": 0.0,
        "night_disconnection": True,
        "grid_capacity_kw": 0.0,
        "last_excel": "",
        "last_pdf": "",
        "last_log": "",
        "has_context": False,
    },
)

tool_header(
    icon="📈",
    title_key="TOOL_HOURLY_RESULTS_TITLE",
    desc_key="TOOL_HOURLY_RESULTS_DESC",
    badge="NEW",
)


@dataclass
class ToolResult:
    ok: bool
    message: str = ""
    meta: Optional[dict[str, Any]] = None
    context: Any = None


def _download_from_path(label: str, path: Path, mime: str) -> None:
    if not path.exists():
        st.warning(f"{label}: {path}")
        return
    st.download_button(
        label=label,
        data=path.read_bytes(),
        file_name=path.name,
        mime=mime,
        width="stretch",
    )


def _ts_suffix(enabled: bool) -> str:
    if not enabled:
        return ""
    return pd.Timestamp.now().strftime("_%Y%m%d_%H%M%S")


def _write_log(path: Path, lines: list[str]) -> None:
    try:
        path.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def _get_ctx() -> Any | None:
    return st.session_state.get(f"tool.{TOOL_ID}.context") if bool(get(TOOL_ID, "has_context", False)) else None


def _fmt_num(v: Any, digits: int = 0, suffix: str = "") -> str:
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "—"
        txt = format_number(v, digits)
        return f"{txt}{suffix}" if suffix else txt
    except Exception:
        return "—"


def _fmt_pct(v: Any, digits: int = 1) -> str:
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "—"
        return f"{float(v):.{digits}f} %"
    except Exception:
        return "—"


def _fmt_mwh_from_kwh(v: Any, digits: int = 1) -> str:
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "—"
        return format_number(float(v) / 1000.0, digits)
    except Exception:
        return "—"


def _centered_plot(fig, *, key: str | None = None, ratio=(1, 3, 1), height: int | None = None) -> None:
    c1, c2, c3 = st.columns(ratio)
    with c2:
        if height is not None:
            fig.update_layout(height=height)
        st.plotly_chart(fig, width="stretch", key=key)


def _subheader_with_help(title_key: str, help_key: str | None = None) -> None:
    cols = st.columns([20, 1])
    with cols[0]:
        st.subheader(t(title_key))
    if help_key:
        with cols[1]:
            with st.popover("❓"):
                st.markdown(t(help_key))


def _month_order_full_en() -> list[str]:
    return [calendar.month_name[m] for m in range(1, 13)] + ["Annual"]


def _sort_month_name(df: pd.DataFrame, col: str = "month_name") -> pd.DataFrame:
    if df is None or df.empty or col not in df.columns:
        return df
    out = df.copy()
    out[col] = pd.Categorical(out[col], categories=_month_order_full_en(), ordered=True)
    return out.sort_values(col)

def _build_performance_display_table(perf: dict[str, Any]) -> pd.DataFrame:
    pm = _sort_month_name(perf.get("monthly", pd.DataFrame()))
    annual = perf.get("annual", {}) or {}

    pm_disp = pd.DataFrame({
        t("HOURLY_COL_MONTH"): pm["month_name"],
        t("HOURLY_COL_GLOBHOR"): pm["globhor_kwh_m2"].map(lambda v: _fmt_num(v, 1)),
        t("HOURLY_COL_GLOBINC"): pm["globinc_kwh_m2"].map(lambda v: _fmt_num(v, 1)),
        t("HOURLY_COL_TILT_GAIN"): pm["globinc_over_globhor_pct"].map(lambda v: _fmt_pct(v, 1)),
        t("HOURLY_COL_GLOBEFF"): pm["globeff_kwh_m2"].map(lambda v: _fmt_num(v, 1)),
        t("HOURLY_COL_GLOBEFF_RATIO"): pm["globeff_over_globinc_pct"].map(lambda v: _fmt_pct(v, 1)),
        t("HOURLY_COL_PR"): pm["pr_mean_prod"].map(lambda v: _fmt_pct(None if v is None else 100.0 * float(v), 1)),
        t("HOURLY_COL_PRODUCTIBLE"): pm["productible_specific"].map(lambda v: _fmt_num(v, 1)),
        t("HOURLY_COL_EGRID_MWH"): pm["e_grid_kwh"].map(lambda v: _fmt_mwh_from_kwh(v, 1)),
    })

    if annual:
        annual_disp = pd.DataFrame([{
            t("HOURLY_COL_MONTH"): annual.get("month_name", "Annual"),
            t("HOURLY_COL_GLOBHOR"): _fmt_num(annual.get("globhor_kwh_m2"), 1),
            t("HOURLY_COL_GLOBINC"): _fmt_num(annual.get("globinc_kwh_m2"), 1),
            t("HOURLY_COL_TILT_GAIN"): _fmt_pct(annual.get("globinc_over_globhor_pct"), 1),
            t("HOURLY_COL_GLOBEFF"): _fmt_num(annual.get("globeff_kwh_m2"), 1),
            t("HOURLY_COL_GLOBEFF_RATIO"): _fmt_pct(annual.get("globeff_over_globinc_pct"), 1),
            t("HOURLY_COL_PR"): _fmt_pct(
                None if annual.get("pr_mean_prod") is None else 100.0 * float(annual.get("pr_mean_prod")),
                1,
            ),
            t("HOURLY_COL_PRODUCTIBLE"): _fmt_num(annual.get("productible_specific"), 1),
            t("HOURLY_COL_EGRID_MWH"): _fmt_mwh_from_kwh(annual.get("e_grid_kwh"), 1),
        }])
        pm_disp = pd.concat([pm_disp, annual_disp], ignore_index=True)

    return pm_disp

def _build_availability_rows(ctx: Any) -> pd.DataFrame:
    cols = set(ctx.df_raw.columns.tolist())
    results = ctx.results

    gp = results.get("global_production", {})
    clip = results.get("inverter_clipping", {})

    has_egrid = "E_Grid" in cols
    has_egrdlim = "EGrdLim" in cols
    has_load_factor_full = {"EApGrid", "EReGrid"}.issubset(cols)
    has_perf = any(c in cols for c in ["PR", "GlobInc", "GlobEff", "Yf", "EArray"])

    if has_load_factor_full:
        lf_status = t("HOURLY_STATUS_AVAILABLE")
    elif has_egrid:
        lf_status = t("HOURLY_STATUS_PARTIAL")
    else:
        lf_status = t("HOURLY_STATUS_MISSING")

    rows = [
        {
            t("HOURLY_AVAIL_STUDY"): t("HOURLY_AVAIL_GLOBAL_RESULTS"),
            t("HOURLY_AVAIL_STATUS"): t("HOURLY_STATUS_AVAILABLE") if gp.get("available", False) else t("HOURLY_STATUS_MISSING"),
            t("HOURLY_AVAIL_DETAIL"): t("HOURLY_AVAIL_GLOBAL_RESULTS_DETAIL"),
        },
        {
            t("HOURLY_AVAIL_STUDY"): t("HOURLY_AVAIL_PERFORMANCE"),
            t("HOURLY_AVAIL_STATUS"): t("HOURLY_STATUS_AVAILABLE") if has_perf else t("HOURLY_STATUS_MISSING"),
            t("HOURLY_AVAIL_DETAIL"): t("HOURLY_AVAIL_PERFORMANCE_DETAIL"),
        },
        {
            t("HOURLY_AVAIL_STUDY"): t("HOURLY_AVAIL_CLIPPING"),
            t("HOURLY_AVAIL_STATUS"): t("HOURLY_STATUS_AVAILABLE") if clip.get("available", False) else t("HOURLY_STATUS_MISSING"),
            t("HOURLY_AVAIL_DETAIL"): t("HOURLY_AVAIL_CLIPPING_DETAIL"),
        },
        {
            t("HOURLY_AVAIL_STUDY"): t("HOURLY_AVAIL_HEATMAP"),
            t("HOURLY_AVAIL_STATUS"): t("HOURLY_STATUS_AVAILABLE") if has_egrid else t("HOURLY_STATUS_MISSING"),
            t("HOURLY_AVAIL_DETAIL"): t("HOURLY_AVAIL_HEATMAP_DETAIL"),
        },
        {
            t("HOURLY_AVAIL_STUDY"): t("HOURLY_AVAIL_GRID_LIMIT_BASE"),
            t("HOURLY_AVAIL_STATUS"): t("HOURLY_STATUS_AVAILABLE") if has_egrdlim else t("HOURLY_STATUS_MISSING"),
            t("HOURLY_AVAIL_DETAIL"): (
                t("HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_YES")
                if has_egrdlim else
                t("HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_NO")
            ),
        },
        {
            t("HOURLY_AVAIL_STUDY"): t("HOURLY_AVAIL_LIMIT_STUDY"),
            t("HOURLY_AVAIL_STATUS"): t("HOURLY_STATUS_AVAILABLE") if has_egrid else t("HOURLY_STATUS_MISSING"),
            t("HOURLY_AVAIL_DETAIL"): t("HOURLY_AVAIL_LIMIT_STUDY_DETAIL"),
        },
        {
            t("HOURLY_AVAIL_STUDY"): t("HOURLY_AVAIL_LOAD_FACTOR"),
            t("HOURLY_AVAIL_STATUS"): lf_status,
            t("HOURLY_AVAIL_DETAIL"): (
                t("HOURLY_AVAIL_LOAD_FACTOR_DETAIL_AVAILABLE")
                if has_load_factor_full else
                t("HOURLY_AVAIL_LOAD_FACTOR_DETAIL_ESTIMABLE")
                if has_egrid else
                t("HOURLY_AVAIL_LOAD_FACTOR_DETAIL_MISSING")
            ),
        },
    ]

    return pd.DataFrame(rows)


def _bar(df: pd.DataFrame, x: str, y: str, title: str, xlab: str, ylab: str):
    fig = px.bar(df, x=x, y=y, title=title, labels={x: xlab, y: ylab})
    fig.update_layout(margin=dict(l=30, r=30, t=60, b=30))
    return fig


def _line(df: pd.DataFrame, x: str, y: str, title: str, xlab: str, ylab: str):
    fig = px.line(df, x=x, y=y, markers=True, title=title, labels={x: xlab, y: ylab})
    fig.update_layout(margin=dict(l=30, r=30, t=60, b=30))
    return fig


def _combo_performance_chart(df: pd.DataFrame):
    if df is None or df.empty:
        return None

    plot_df = df[df["month_name"] != "Annual"].copy()
    if plot_df.empty:
        return None

    fig = go.Figure()

    # Main bars: E_Grid
    if "e_grid_kwh" in plot_df.columns and plot_df["e_grid_kwh"].notna().any():
        fig.add_bar(
            x=plot_df["month_name"],
            y=plot_df["e_grid_kwh"] / 1000.0,
            name="E_Grid (MWh)",
            yaxis="y",
        )

    # Line: GlobInc
    if "globinc_kwh_m2" in plot_df.columns and plot_df["globinc_kwh_m2"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=plot_df["month_name"],
                y=plot_df["globinc_kwh_m2"],
                mode="lines+markers",
                name="GlobInc (kWh/m²)",
                yaxis="y2",
            )
        )

    # Line: PR on positive hours
    if "pr_mean_prod" in plot_df.columns and plot_df["pr_mean_prod"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=plot_df["month_name"],
                y=plot_df["pr_mean_prod"] * 100.0,
                mode="lines+markers",
                name="PR (%)",
                yaxis="y3",
            )
        )

    fig.update_layout(
        title="Monthly Performance Overview",
        margin=dict(l=30, r=30, t=60, b=30),
        barmode="group",
        yaxis=dict(title="E_Grid (MWh)"),
        yaxis2=dict(
            title="GlobInc (kWh/m²)",
            overlaying="y",
            side="right",
        ),
        yaxis3=dict(
            title="PR (%)",
            anchor="free",
            overlaying="y",
            side="right",
            position=0.95,
        ),
        legend=dict(orientation="h"),
    )
    return fig


def _month_hour_heatmap_mw(
    df: pd.DataFrame,
    value_col: str = "E_Grid",
    dt_hours: float = 1.0,
    agg: str = "mean",
):
    if df is None or df.empty or value_col not in df.columns or not isinstance(df.index, pd.DatetimeIndex):
        return None

    dt_hours = float(dt_hours) if (dt_hours and dt_hours > 0) else 1.0

    tmp = pd.DataFrame(index=df.index)
    tmp["month"] = tmp.index.month
    tmp["hour"] = tmp.index.hour

    v = pd.to_numeric(df[value_col], errors="coerce").fillna(0.0)
    power_kw = v / dt_hours
    tmp["value_mw"] = power_kw / 1000.0

    pivot = tmp.pivot_table(
        values="value_mw",
        index="hour",
        columns="month",
        aggfunc=agg,
    ).reindex(index=list(range(24)), columns=list(range(1, 13)))

    pivot = pivot.fillna(0.0)

    month_labels = [calendar.month_abbr[m] for m in range(1, 13)]
    hour_labels = [f"{h:02d}:00" for h in range(24)]

    z = pivot.to_numpy(dtype=float)
    eps = 1e-9
    text = np.where(z > eps, np.round(z, 2).astype(str), "")

    colorscale_wyr = [
        [0.00, "#ffffff"],
        [0.50, "#fff2a8"],
        [1.00, "#d7191c"],
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=month_labels,
            y=hour_labels,
            colorscale=colorscale_wyr,
            colorbar=dict(title="Mean Power (MW)", len=0.8, thickness=14),
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=10),
            hovertemplate=(
                "Month: %{x}<br>"
                "Hour: %{y}<br>"
                "Mean Power: %{z:.2f} MW"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(margin=dict(l=40, r=40, t=10, b=10))
    fig.update_xaxes(side="top")
    fig.update_yaxes(autorange="reversed")
    return fig


def _build_system_summary_markdown(ctx: Any) -> str | None:
    ss = ctx.results.get("system_summary", {})
    if not ss or not ss.get("available", False):
        return None

    lines = []

    lines.append(
        t("HOURLY_SYSTEM_SENTENCE_GENERAL").format(
            prod_mwh=_fmt_mwh_from_kwh(ss.get("production_wo_night_kwh"), 1)
        )
    )

    lines.append(
        t("HOURLY_SYSTEM_SENTENCE_CLIP_NIGHT").format(
            clip_mwh=_fmt_mwh_from_kwh(ss.get("clipping_kwh"), 1),
            clip_pct=_fmt_pct(ss.get("clipping_pct_of_production"), 1),
            night_mwh=_fmt_mwh_from_kwh(ss.get("night_kwh"), 1),
            night_pct=_fmt_pct(ss.get("night_pct_of_production"), 1),
        )
    )

    if ss.get("has_grid_limit", False):
        lines.append(
            t("HOURLY_SYSTEM_SENTENCE_GRID").format(
                grid_mwh=_fmt_mwh_from_kwh(ss.get("grid_limit_kwh"), 1),
                grid_pct=_fmt_pct(ss.get("grid_limit_pct_of_production"), 1),
            )
        )

    if ss.get("meteo_level") is not None or ss.get("globeff_ratio_annual") is not None:
        lines.append(
            t("HOURLY_SYSTEM_SENTENCE_METEO").format(
                meteo=t(f"HOURLY_METEO_{ss.get('meteo_level', 'GOOD')}"),
                optics=t(f"HOURLY_OPTICS_{ss.get('optics_level', 'MODERATE_LOSSES')}"),
                globeff_ratio=_fmt_pct(ss.get("globeff_ratio_annual"), 1),
            )
        )

    tilt_gain = ss.get("tilt_gain_pct")
    optical_eff = ss.get("optical_efficiency_pct")

    if tilt_gain is not None and optical_eff is not None:
        lines.append(
            t("HOURLY_SYSTEM_SENTENCE_OPTICS_FULL").format(
                tilt_gain=_fmt_pct(tilt_gain, 1),
                optical_efficiency=_fmt_pct(optical_eff, 1),
            )
        )
    elif optical_eff is not None:
        lines.append(
            t("HOURLY_SYSTEM_SENTENCE_OPTICS_ONLY").format(
                optical_efficiency=_fmt_pct(optical_eff, 1),
            )
        )

    if ss.get("productive_utilization_ratio") is not None:
        lines.append(
            t("HOURLY_SYSTEM_SENTENCE_UTILIZATION").format(
                utilization_pct=_fmt_pct(100.0 * float(ss.get("productive_utilization_ratio")), 1),
                ref_label=t(ss.get("productive_utilization_reference_label", "HOURLY_UTILIZATION_REFERENCE_P99")),
            )
        )

    if ss.get("pr_mean") is not None and ss.get("productible_specific") is not None:
        lines.append(
            t("HOURLY_SYSTEM_SENTENCE_PERFORMANCE_WITH_PRODUCTIBLE").format(
                pr=_fmt_pct(
                    None if ss.get("pr_mean") is None
                    else 100.0 * float(ss.get("pr_mean")),
                    1,
                ),
                productible=_fmt_num(ss.get("productible_specific"), 1),
            )
        )
    elif ss.get("pr_mean") is not None:
        lines.append(
            t("HOURLY_SYSTEM_SENTENCE_PERFORMANCE_NO_PRODUCTIBLE").format(
                pr=_fmt_pct(
                    None if ss.get("pr_mean") is None
                    else 100.0 * float(ss.get("pr_mean")),
                    1,
                )
            )
        )

    rec_map = {
        "FAVORABLE": "HOURLY_BRIDGING_RECOMMENDATION_FAVORABLE",
        "CAUTION": "HOURLY_BRIDGING_RECOMMENDATION_CAUTION",
        "NOT_RECOMMENDED": "HOURLY_BRIDGING_RECOMMENDATION_NOT_RECOMMENDED",
        "NOT_AVAILABLE": "HOURLY_BRIDGING_RECOMMENDATION_NOT_AVAILABLE",
    }
    rec_key = rec_map.get(ss.get("bridging_recommendation_level", "NOT_AVAILABLE"), "HOURLY_BRIDGING_RECOMMENDATION_NOT_AVAILABLE")

    dcac_map = {
        "REVIEW_RELEVANT": "HOURLY_DCAC_RECOMMENDATION_RELEVANT",
        "REVIEW_POSSIBLE": "HOURLY_DCAC_RECOMMENDATION_POSSIBLE",
        "REVIEW_NOT_PRIORITY": "HOURLY_DCAC_RECOMMENDATION_NOT_PRIORITY",
        "NOT_AVAILABLE": "HOURLY_DCAC_RECOMMENDATION_NOT_AVAILABLE",
    }
    dcac_key = dcac_map.get(ss.get("dc_ac_review_recommendation_level", "NOT_AVAILABLE"), "HOURLY_DCAC_RECOMMENDATION_NOT_AVAILABLE")
    lines.append(t(dcac_key))

    lines.append(
        t(rec_key).format(
            utilization_pct=_fmt_pct(
                None if ss.get("productive_utilization_ratio") is None else 100.0 * float(ss.get("productive_utilization_ratio")),
                1,
            ),
            energy_above_pct=_fmt_pct(ss.get("energy_above_limit_pct_of_production"), 1),
        )
    )

    return "\n\n".join(lines)


with section("SECTION_INPUTS", icon="🧾"):
    st.markdown(f"**{t('HOURLY_INPUTS_GUIDE_TITLE')}**")
    st.markdown(
        "- " + t("HOURLY_INPUTS_GUIDE_LIMIT_VALUE") + "\n"
        "- " + t("HOURLY_INPUTS_GUIDE_GRID_CAPACITY_REVISED") + "\n"
        "- " + t("HOURLY_INPUTS_GUIDE_CLIPPING") + "\n"
        "- " + t("HOURLY_INPUTS_GUIDE_NIGHT") + "\n"
        "- " + t("HOURLY_INPUTS_GUIDE_LOAD_FACTOR")
    )

    uploaded = st.file_uploader(
        t("HOURLY_UPLOAD_LABEL"),
        type=["csv", "txt"],
        accept_multiple_files=False,
    )

    add_timestamp = st.checkbox(
        t("HOURLY_TIMESTAMP_OUTPUTS"),
        value=bool(get(TOOL_ID, "add_timestamp_to_outputs", True)),
    )
    set_(TOOL_ID, "add_timestamp_to_outputs", add_timestamp)

    threshold_col = st.text_input(
        t("HOURLY_LIMIT_COLUMN_LABEL"),
        value=str(get(TOOL_ID, "threshold_column", "E_Grid")),
        help=t("HOURLY_LIMIT_COLUMN_HELP"),
    )
    set_(TOOL_ID, "threshold_column", threshold_col)

    threshold_value = st.number_input(
        t("HOURLY_LIMIT_VALUE_LABEL"),
        value=float(get(TOOL_ID, "threshold_value", 0.0)),
        step=1.0,
        help=t("HOURLY_LIMIT_VALUE_HELP"),
    )
    set_(TOOL_ID, "threshold_value", float(threshold_value))

    night_disc = st.checkbox(
        t("HOURLY_NIGHT_DISCONNECT_LABEL"),
        value=bool(get(TOOL_ID, "night_disconnection", True)),
        help=t("HOURLY_NIGHT_DISCONNECT_HELP"),
    )
    set_(TOOL_ID, "night_disconnection", bool(night_disc))

    grid_capacity_kw = st.number_input(
        t("HOURLY_GRID_CAPACITY_LABEL_REVISED"),
        value=float(get(TOOL_ID, "grid_capacity_kw", 0.0)),
        min_value=0.0,
        step=200.0,
        help=t("HOURLY_GRID_CAPACITY_HELP_REVISED"),
    )
    set_(TOOL_ID, "grid_capacity_kw", float(grid_capacity_kw))


with section("SECTION_RUN", icon="▶️"):
    st.markdown('<div class="pv-run">', unsafe_allow_html=True)
    run_btn = st.button(t("HOURLY_RUN"), type="primary")
    st.markdown("</div>", unsafe_allow_html=True)


with section("SECTION_RESULTS", icon="📊"):
    if run_btn:
        if uploaded is None:
            st.warning(t("HOURLY_UPLOAD_LABEL"))
        else:
            with st.spinner(t("HOURLY_RUNNING")):
                try:
                    cap_raw = float(get(TOOL_ID, "grid_capacity_kw", 0.0))
                    cap_kw = cap_raw if cap_raw > 0 else None

                    ctx = analyze_hourly_source(
                        source=uploaded.getvalue(),
                        source_name=uploaded.name,
                        threshold_value=float(get(TOOL_ID, "threshold_value", 0.0)),
                        threshold_column=str(get(TOOL_ID, "threshold_column", "E_Grid")),
                        night_disconnection=bool(get(TOOL_ID, "night_disconnection", False)),
                        grid_capacity_kw=cap_kw,
                    )
                    set_(TOOL_ID, "has_context", True)
                    st.session_state[f"tool.{TOOL_ID}.context"] = ctx
                    result = ToolResult(ok=True, meta={"source_name": uploaded.name}, context=ctx)
                except Exception as e:
                    set_(TOOL_ID, "has_context", False)
                    result = ToolResult(ok=False, message=str(e), meta={"source_name": uploaded.name})

            if result.ok:
                st.success(t("HOURLY_DONE"))
            else:
                st.error(result.message or t("HOURLY_FAILED"))
                st.stop()

    ctx = _get_ctx()
    if ctx is None:
        st.info(t("HOURLY_NO_OUTPUTS_YET"))
    else:
        df = ctx.df_raw
        cols = set(df.columns.tolist())

        tab_main, tab_details = st.tabs(
            [
                t("HOURLY_TAB_MAIN_ANALYSIS"),
                t("HOURLY_TAB_DETAILED_ANALYSIS"),
            ]
        )

        with tab_main:
            gp = ctx.results.get("global_production", {})
            clip = ctx.results.get("inverter_clipping", {})
            gl = ctx.results.get("grid_limit", {})
            lf = ctx.results.get("load_factor", {})
            thr = ctx.results.get("threshold", {})
            perf = ctx.results.get("performance_monthly", {})

            dt_hours = 1.0
            irregular = 0.0
            if gp and gp.get("available", False):
                s_gp = gp.get("summary", {})
                dt_hours = float(s_gp.get("dt_hours", 1.0) or 1.0)
                dt_meta = s_gp.get("dt_meta", {}) if isinstance(s_gp.get("dt_meta", {}), dict) else {}
                irregular = float(dt_meta.get("irregular_share", 0.0))

            _subheader_with_help("HOURLY_SUMMARY", "HOURLY_HELP_FILE_SUMMARY_MD")
            st.write({
                t("HOURLY_SUMMARY_FILE"): ctx.input_file.name,
                t("HOURLY_GLOBAL_PROJECT"): ctx.general_info.get("Project_name", "") or "-",
                t("HOURLY_GLOBAL_PROJECT_FILE"): ctx.general_info.get("Project_file", "") or "-",
                t("HOURLY_GLOBAL_VARIANT"): ctx.general_info.get("Variant_name", "") or "-",
                t("HOURLY_SUMMARY_PVSYST_VERSION"): ctx.general_info.get("PVSyst_version", "") or "-",
                t("HOURLY_SUMMARY_SIM_DATE"): ctx.general_info.get("Simulation_date", "") or "-",
                t("HOURLY_SUMMARY_PERIOD"): f"{df.index.min()} → {df.index.max()}",
                t("HOURLY_SUMMARY_ROWS"): int(len(df)),
                t("HOURLY_GLOBAL_TIMESTEP"): f"{dt_hours:g} h",
                t("HOURLY_GLOBAL_TIMESTEP_QUALITY"): f"{(1.0 - irregular) * 100:.1f} %",
                t("HOURLY_SUMMARY_NIGHT_OPTION"): (
                    t("HOURLY_NIGHT_DISCONNECT_ON")
                    if bool(ctx.options.night_disconnection) else t("HOURLY_NIGHT_DISCONNECT_OFF")
                ),
            })

            with st.expander(t("HOURLY_SUMMARY_COLUMNS_EXPANDER")):
                st.write({t("HOURLY_SUMMARY_COLUMNS"): ", ".join(list(df.columns))})

            _subheader_with_help("HOURLY_AVAILABLE_STUDIES_TITLE", "HOURLY_HELP_AVAILABLE_STUDIES_MD")
            st.dataframe(_build_availability_rows(ctx), width="stretch", hide_index=True)

            _subheader_with_help("HOURLY_GLOBAL_PRODUCTION_TITLE", "HOURLY_HELP_GLOBAL_RESULTS_MD")
            if not gp or not gp.get("available", False):
                st.warning(t("HOURLY_GLOBAL_NOT_AVAILABLE"))
            else:
                s = gp["summary"]
                grid_capacity = getattr(ctx.options, "grid_capacity_kw", None)

                annual_lf = s.get("annual_load_factor", None)
                if annual_lf is None and gl and gl.get("available", False):
                    annual_lf = (gl.get("summary", {}) or {}).get("annual_load_factor", None)
                if annual_lf is None and lf and lf.get("available", False):
                    annual_lf = (lf.get("summary", {}) or {}).get("annual_load_factor", None)

                st.write({
                    t("HOURLY_GLOBAL_PRODUCTION_NO_IMPORT") + " (kWh)": _fmt_num(s.get("production_without_import_kwh"), 0),
                    t("HOURLY_GLOBAL_NET_PRODUCTION") + " (kWh)": _fmt_num(s.get("net_production_kwh"), 0),
                    t("HOURLY_GLOBAL_NIGHT_CONSUMPTION") + " (kWh)": _fmt_num(s.get("night_consumption_kwh"), 0),
                    t("HOURLY_GLOBAL_OPERATING_HOURS"): (
                        f"{_fmt_num(s.get('operating_hours'), 1)} h "
                        f"({_fmt_pct(s.get('operating_pct'), 1)})"
                    ),
                    t("HOURLY_GLOBAL_IMPORT_HOURS"): f"{_fmt_num(s.get('import_hours'), 1)} h",
                    t("HOURLY_GLOBAL_PR"): _fmt_pct(None if s.get("pr_mean") is None else 100.0 * float(s.get("pr_mean")), 1),
                    t("HOURLY_GLOBAL_GRID_CAPACITY"): (
                        f"{_fmt_num(grid_capacity, 0)} kW" if grid_capacity else t("HOURLY_GLOBAL_GRID_CAPACITY_NONE")
                    ),
                    t("HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR"): (
                        f"{100.0 * float(annual_lf):.2f} %" if annual_lf is not None
                        else t("HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR_NONE")
                    ),
                })

            _subheader_with_help("HOURLY_SYSTEM_SUMMARY_TITLE", "HOURLY_HELP_SYSTEM_SUMMARY_MD")
            summary_md = _build_system_summary_markdown(ctx)
            if summary_md:
                st.markdown(summary_md)

            _subheader_with_help("HOURLY_PERFORMANCE_MONTHLY_TITLE", "HOURLY_HELP_PERFORMANCE_MONTHLY_MD")
            if perf and perf.get("available", False):
                pm = _sort_month_name(perf.get("monthly", pd.DataFrame()))
                fig_perf = _combo_performance_chart(pm)
                if fig_perf is not None:
                    _centered_plot(fig_perf, key="perf_combo_main", ratio=(1, 4, 1), height=500)

                pm_disp = _build_performance_display_table(perf)
                st.dataframe(pm_disp, width="stretch", hide_index=True)

            _subheader_with_help("HOURLY_SECTION_CLIPPING_TITLE", "HOURLY_HELP_CLIPPING_MD")
            if not clip or not clip.get("available", False):
                st.info(t("HOURLY_CLIPPING_NOT_AVAILABLE"))
            elif clip.get("empty", False):
                st.info(t("HOURLY_EMPTY"))
            else:
                clip_s = clip.get("summary", {})
                monthly_clip = _sort_month_name(clip.get("monthly", pd.DataFrame()))

                primary_ref = t(clip_s.get("pct_reference_primary_label", "HOURLY_CLIP_REFERENCE_PROD_WO_NIGHT"))
                secondary_ref = t(clip_s.get("pct_reference_secondary_label", "HOURLY_CLIP_REFERENCE_POTENTIAL_AC"))

                st.write({
                    t("HOURLY_CLIP_ENERGY") + " (kWh)": _fmt_num(clip_s.get("energy_clipped_kwh"), 0),
                    t("HOURLY_CLIP_PCT_PRIMARY"): _fmt_pct(clip_s.get("pct_of_egrid_pos"), 2),
                    t("HOURLY_CLIP_REFERENCE_PRIMARY"): primary_ref,
                    t("HOURLY_CLIP_PCT_SECONDARY"): _fmt_pct(clip_s.get("pct_of_potential"), 2),
                    t("HOURLY_CLIP_REFERENCE_SECONDARY"): secondary_ref,
                    t("HOURLY_CLIP_HOURS"): f"{_fmt_num(clip_s.get('hours_clipping'), 1)} h",
                    t("HOURLY_CLIP_MAX_VALUE"): _fmt_num(clip_s.get("max_clipping_value"), 2),
                })

                if monthly_clip is not None and not monthly_clip.empty and "energy_clipped_kwh" in monthly_clip.columns:
                    fig_clip = _bar(
                        monthly_clip[monthly_clip["month_name"] != "Annual"] if "Annual" in monthly_clip["month_name"].astype(str).tolist() else monthly_clip,
                        x="month_name",
                        y="energy_clipped_kwh",
                        title="Monthly Inverter Clipping Losses",
                        xlab="Month",
                        ylab="Clipping Loss (kWh)",
                    )
                    _centered_plot(fig_clip, key="clip_monthly_main", ratio=(1, 3, 1), height=420)

            _subheader_with_help("HOURLY_HEATMAP_TITLE", "HOURLY_HELP_HEATMAP_MD")
            if "E_Grid" not in cols:
                st.warning(t("HOURLY_HEATMAP_MISSING_COLUMN") + ": E_Grid")
            else:
                fig_hm = _month_hour_heatmap_mw(
                    df=df,
                    value_col="E_Grid",
                    dt_hours=dt_hours,
                    agg="mean",
                )
                if fig_hm is None:
                    st.warning(t("HOURLY_HEATMAP_NOT_AVAILABLE"))
                else:
                    _centered_plot(fig_hm, key="heatmap_main", ratio=(1, 4, 1), height=650)
                    st.caption(t("HOURLY_HEATMAP_CAPTION_MW"))

            _subheader_with_help("HOURLY_SECTION_LIMIT_STUDY_TITLE", "HOURLY_HELP_GRID_LIMIT_MD")

            st.markdown(f"**{t('HOURLY_LIMIT_CURRENT_STATE_TITLE')}**")
            if gl and gl.get("available", False):
                gl_s = gl.get("summary", {})
                method = str(gl_s.get("method", ""))

                st.write({
                    t("HOURLY_LIMIT_METHOD"): (
                        t("HOURLY_LIMIT_METHOD_MEASURED")
                        if method == "measured"
                        else t("HOURLY_LIMIT_METHOD_ESTIMATED")
                        if method == "estimated_from_capacity"
                        else "—"
                    ),
                    t("HOURLY_GRID_LOST_ENERGY") + " (kWh)": _fmt_num(gl_s.get("lost_kwh"), 0),
                    t("HOURLY_GRID_LOST_PCT"): _fmt_pct(gl_s.get("lost_pct"), 2),
                    t("HOURLY_GRID_HOURS_LIMITED"): f"{_fmt_num(gl_s.get('hours_limited'), 1)} h",
                    t("HOURLY_GRID_INJECTED") + " (kWh)": _fmt_num(gl_s.get("injected_kwh"), 0),
                })
            else:
                st.info(t("HOURLY_GRID_LIMIT_NOT_AVAILABLE"))

            st.markdown(f"**{t('HOURLY_LIMIT_COMPLEMENTARY_STUDY_TITLE')}**")
            if thr and thr.get("available", False):
                thr_s = thr.get("summary", {})
                st.write({
                    t("HOURLY_LIMIT_COLUMN_LABEL"): thr_s.get("threshold_column", "—"),
                    t("HOURLY_LIMIT_VALUE_LABEL"): _fmt_num(thr_s.get("threshold_value"), 2),
                    t("HOURLY_THR_HOURS_ABOVE"): f"{_fmt_num(thr_s.get('hours_above'), 1)} h",
                    t("HOURLY_THR_SHARE_ABOVE"): _fmt_pct(thr_s.get("pct_above_operating_time"), 1),
                    t("HOURLY_THR_ENERGY_ABOVE") + " (kWh)": _fmt_num(thr_s.get("energy_above_kwh"), 0),
                })

                monthly = _sort_month_name(thr.get("monthly", pd.DataFrame()))
                if monthly is not None and not monthly.empty and "energy_above_kwh" in monthly.columns:
                    fig_thr = _bar(
                        monthly[monthly["month_name"] != "Annual"] if "Annual" in monthly["month_name"].astype(str).tolist() else monthly,
                        x="month_name",
                        y="energy_above_kwh",
                        title="Monthly Energy Above Limit",
                        xlab="Month",
                        ylab="Energy Above Limit (kWh)",
                    )
                    _centered_plot(fig_thr, key="threshold_monthly_main", ratio=(1, 3, 1), height=420)
            else:
                st.info(t("HOURLY_THRESHOLD_NOT_AVAILABLE"))

            _subheader_with_help("HOURLY_SECTION_LOAD_FACTOR_TITLE", "HOURLY_HELP_LOAD_FACTOR_MD")
            if lf and lf.get("available", False):
                lf_s = lf.get("summary", {})
                st.write({
                    t("HOURLY_LF_P_ACTIVE") + " (kWh)": _fmt_num(lf_s.get("P_kWh"), 0),
                    t("HOURLY_LF_Q_REACTIVE") + " (kWh)": _fmt_num(lf_s.get("Q_kWh_equiv"), 0),
                    t("HOURLY_LF_S_APPARENT") + " (kWh)": _fmt_num(lf_s.get("S_kWh_equiv"), 0),
                    t("HOURLY_LF_COSPHI"): _fmt_num(lf_s.get("cosphi"), 3),
                    t("HOURLY_LF_Q_SHARE"): (
                        f"{100.0 * float(lf_s.get('q_share')):.2f} %" if lf_s.get("q_share") is not None else "—"
                    ),
                })

                lf_m = _sort_month_name(lf.get("monthly", pd.DataFrame()))
                if lf_m is not None and not lf_m.empty and "cosphi" in lf_m.columns and lf_m["cosphi"].notna().any():
                    fig_lf = _line(
                        lf_m[lf_m["month_name"] != "Annual"] if "Annual" in lf_m["month_name"].astype(str).tolist() else lf_m,
                        x="month_name",
                        y="cosphi",
                        title="Monthly Power Factor",
                        xlab="Month",
                        ylab="cos(phi)",
                    )
                    _centered_plot(fig_lf, key="cosphi_monthly_main", ratio=(1, 3, 1), height=420)
            else:
                if "E_Grid" in cols:
                    st.info(t("HOURLY_LOAD_FACTOR_ESTIMABLE"))
                else:
                    st.info(t("HOURLY_LOAD_FACTOR_NOT_AVAILABLE"))

        with tab_details:
            perf = ctx.results.get("performance_monthly", {})
            thr = ctx.results.get("threshold", {})
            gl = ctx.results.get("grid_limit", {})
            lf = ctx.results.get("load_factor", {})
            pd_res = ctx.results.get("power_distribution", {})
            clip = ctx.results.get("inverter_clipping", {})

            _subheader_with_help("HOURLY_DETAILS_PERFORMANCE_TITLE", "HOURLY_HELP_PERFORMANCE_MONTHLY_MD")
            if perf and perf.get("available", False):
                pm_disp = _build_performance_display_table(perf)
                st.dataframe(pm_disp, width="stretch", hide_index=True)

            _subheader_with_help("HOURLY_DETAILS_THRESHOLD_TITLE", "HOURLY_HELP_GRID_LIMIT_MD")
            if thr and thr.get("available", False):
                monthly = _sort_month_name(thr.get("monthly", pd.DataFrame()))
                monthly_pct = _sort_month_name(thr.get("monthly_pct", pd.DataFrame()))
                seasonal = thr.get("seasonal")
                night_monthly = _sort_month_name(thr.get("night_consumption_monthly", pd.DataFrame()))

                if monthly is not None and not monthly.empty:
                    fig1 = _bar(
                        monthly[monthly["month_name"] != "Annual"] if "Annual" in monthly["month_name"].astype(str).tolist() else monthly,
                        x="month_name",
                        y="hours_above",
                        title="Monthly Hours Above Limit",
                        xlab="Month",
                        ylab="Hours",
                    )
                    _centered_plot(fig1, key="thr_hours_detail", ratio=(1, 3, 1), height=420)

                    fig2 = _bar(
                        monthly[monthly["month_name"] != "Annual"] if "Annual" in monthly["month_name"].astype(str).tolist() else monthly,
                        x="month_name",
                        y="energy_above_kwh",
                        title="Monthly Energy Above Limit",
                        xlab="Month",
                        ylab="Energy Above Limit (kWh)",
                    )
                    _centered_plot(fig2, key="thr_energy_detail", ratio=(1, 3, 1), height=420)

                if monthly_pct is not None and not monthly_pct.empty:
                    fig3 = _line(
                        monthly_pct,
                        x="month_name",
                        y="pct_above",
                        title="Monthly Share Above Limit",
                        xlab="Month",
                        ylab="Share (%)",
                    )
                    _centered_plot(fig3, key="thr_pct_detail", ratio=(1, 3, 1), height=420)

                if night_monthly is not None and not night_monthly.empty:
                    fig4 = _bar(
                        night_monthly,
                        x="month_name",
                        y="night_consumption_kwh",
                        title="Monthly Night Import",
                        xlab="Month",
                        ylab="Night Import (kWh)",
                    )
                    _centered_plot(fig4, key="night_import_detail", ratio=(1, 3, 1), height=420)

                st.markdown(f"**{t('HOURLY_TABLE_THRESHOLD_MONTHLY')}**")
                m = thr["monthly"].copy()
                m_disp = pd.DataFrame({
                    t("HOURLY_COL_MONTH"): m["month_name"],
                    t("HOURLY_COL_HOURS_ABOVE"): m["hours_above"].map(lambda v: format_number(v, 1)),
                    t("HOURLY_COL_ENERGY_ABOVE_KWH"): m["energy_above_kwh"].map(lambda v: format_number(v, 0)),
                })
                st.dataframe(m_disp, width="stretch", hide_index=True)

                if seasonal is not None and not seasonal.empty:
                    st.markdown(f"**{t('HOURLY_TABLE_THRESHOLD_SEASONAL')}**")
                    s2 = seasonal.copy()
                    s2_disp = pd.DataFrame({
                        t("HOURLY_COL_SEASON"): s2["season"],
                        t("HOURLY_COL_HOURS_ABOVE"): s2["hours_above"].map(lambda v: format_number(v, 1)),
                        t("HOURLY_COL_ENERGY_ABOVE_KWH"): s2["energy_above_kwh"].map(lambda v: format_number(v, 0)),
                    })
                    st.dataframe(s2_disp, width="stretch", hide_index=True)
            else:
                st.info(t("HOURLY_THRESHOLD_NOT_AVAILABLE"))

            _subheader_with_help("HOURLY_DETAILS_GRID_LIMIT_TITLE", "HOURLY_HELP_GRID_LIMIT_MD")
            if gl and gl.get("available", False):
                gl_m = _sort_month_name(gl.get("monthly", pd.DataFrame()))
                if gl_m is not None and not gl_m.empty:
                    fig5 = _bar(
                        gl_m,
                        x="month_name",
                        y="lost_kwh",
                        title="Monthly Curtailment Loss",
                        xlab="Month",
                        ylab="Lost Energy (kWh)",
                    )
                    _centered_plot(fig5, key="grid_lost_kwh_detail", ratio=(1, 3, 1), height=420)

                    fig6 = _line(
                        gl_m,
                        x="month_name",
                        y="lost_pct",
                        title="Monthly Curtailment Loss Share",
                        xlab="Month",
                        ylab="Loss Share (%)",
                    )
                    _centered_plot(fig6, key="grid_lost_pct_detail", ratio=(1, 3, 1), height=420)

                    st.markdown(f"**{t('HOURLY_TABLE_GRID_LIMIT_MONTHLY')}**")
                    gm = gl_m.copy()
                    gm_disp = pd.DataFrame({
                        t("HOURLY_COL_MONTH"): gm["month_name"],
                        t("HOURLY_GRID_LOST_ENERGY") + " (kWh)": gm["lost_kwh"].map(lambda v: format_number(v, 0)),
                        t("HOURLY_GRID_LOST_PCT"): gm["lost_pct"].map(lambda v: f"{float(v):.2f} %"),
                        t("HOURLY_GRID_HOURS_LIMITED"): gm["hours_limited"].map(lambda v: format_number(v, 1)),
                        t("HOURLY_GRID_INJECTED") + " (kWh)": gm["injected_kwh"].map(lambda v: format_number(v, 0)),
                    })
                    st.dataframe(gm_disp, width="stretch", hide_index=True)
            else:
                st.info(t("HOURLY_GRID_LIMIT_NOT_AVAILABLE"))

            _subheader_with_help("HOURLY_DETAILS_CLIPPING_TITLE", "HOURLY_HELP_CLIPPING_MD")
            if clip and clip.get("available", False) and not clip.get("empty", False):
                clip_m = _sort_month_name(clip.get("monthly", pd.DataFrame()))
                if clip_m is not None and not clip_m.empty:
                    figc1 = _bar(
                        clip_m,
                        x="month_name",
                        y="energy_clipped_kwh",
                        title="Monthly Inverter Clipping Losses",
                        xlab="Month",
                        ylab="Clipping Loss (kWh)",
                    )
                    _centered_plot(figc1, key="clip_detail_energy", ratio=(1, 3, 1), height=420)

                    if "pct_clipping" in clip_m.columns:
                        figc2 = _line(
                            clip_m,
                            x="month_name",
                            y="pct_clipping",
                            title="Monthly Clipping Share",
                            xlab="Month",
                            ylab="Clipping Share (%)",
                        )
                        _centered_plot(figc2, key="clip_detail_pct", ratio=(1, 3, 1), height=420)
            else:
                st.info(t("HOURLY_CLIPPING_NOT_AVAILABLE"))

            _subheader_with_help("HOURLY_DETAILS_LOAD_FACTOR_TITLE", "HOURLY_HELP_LOAD_FACTOR_MD")
            if lf and lf.get("available", False):
                lf_m = _sort_month_name(lf.get("monthly", pd.DataFrame()))
                sat = lf.get("saturation_distribution")

                if lf_m is not None and not lf_m.empty and "cosphi" in lf_m.columns and lf_m["cosphi"].notna().any():
                    fig7 = _line(
                        lf_m,
                        x="month_name",
                        y="cosphi",
                        title="Monthly Power Factor",
                        xlab="Month",
                        ylab="cos(phi)",
                    )
                    _centered_plot(fig7, key="lf_cosphi_detail", ratio=(1, 3, 1), height=420)

                if sat is not None and not sat.empty:
                    fig8 = _bar(
                        sat,
                        x="class",
                        y="pct_time",
                        title="Relative Apparent Power Saturation",
                        xlab="Class",
                        ylab="Time Share (%)",
                    )
                    _centered_plot(fig8, key="lf_sat_detail", ratio=(1, 3, 1), height=420)

                st.markdown(f"**{t('HOURLY_TABLE_LOAD_FACTOR_MONTHLY')}**")
                lm = lf_m.copy()
                lm_disp = pd.DataFrame({
                    t("HOURLY_COL_MONTH"): lm["month_name"],
                    t("HOURLY_LF_S_APPARENT"): lm["S_kWh_equiv"].map(lambda v: format_number(v, 0)),
                    t("HOURLY_LF_Q_REACTIVE"): lm["Q_kWh_equiv"].map(lambda v: format_number(v, 0)),
                    t("HOURLY_LF_P_ACTIVE"): lm["P_kWh"].map(lambda v: format_number(v, 0) if v is not None else "—"),
                    t("HOURLY_LF_COSPHI"): lm["cosphi"].map(lambda v: f"{float(v):.3f}" if v is not None else "—"),
                    t("HOURLY_LF_Q_SHARE"): lm["q_share"].map(lambda v: f"{100.0 * float(v):.2f} %" if v is not None else "—"),
                })
                st.dataframe(lm_disp, width="stretch", hide_index=True)

                if sat is not None and not sat.empty:
                    st.markdown(f"**{t('HOURLY_TABLE_SATURATION_DIST')}**")
                    sd_disp = pd.DataFrame({
                        t("HOURLY_COL_CLASS"): sat["class"].astype(str),
                        t("HOURLY_COL_HOURS"): sat["hours"].map(lambda v: format_number(v, 1)),
                        t("HOURLY_COL_PCT_TIME"): sat["pct_time"].map(lambda v: f"{float(v):.1f} %"),
                    })
                    st.dataframe(sd_disp, width="stretch", hide_index=True)
            else:
                st.info(t("HOURLY_LOAD_FACTOR_NOT_AVAILABLE"))

            _subheader_with_help("HOURLY_DETAILS_POWER_DISTRIBUTION_TITLE", "HOURLY_HELP_POWER_DISTRIBUTION_MD")
            if not pd_res:
                st.info(t("HOURLY_EMPTY"))
            elif not pd_res.get("available", False):
                st.warning(t("HOURLY_DISTRIBUTION_NOT_AVAILABLE"))
                st.write(pd_res)
            elif pd_res.get("empty", False):
                st.info(t("HOURLY_EMPTY"))
            else:
                d = pd_res["summary"].copy()
                d_disp = pd.DataFrame({
                    t("HOURLY_COL_CLASS"): d["class"].astype(str),
                    t("HOURLY_COL_HOURS"): d["hours"].map(lambda v: format_number(v, 1)),
                    t("HOURLY_COL_PCT_TIME"): d["pct_time"].map(lambda x: f"{float(x):.1f} %"),
                    t("HOURLY_COL_ENERGY_KWH"): d["energy_kwh"].map(lambda v: format_number(v, 0)),
                })
                st.dataframe(d_disp, width="stretch", hide_index=True)

        st.caption(f"outputs: {OUTPUTS_DIR}")


with section("SECTION_EXPORT", icon="📤"):
    last_excel = get(TOOL_ID, "last_excel", "")
    last_pdf = get(TOOL_ID, "last_pdf", "")
    last_log = get(TOOL_ID, "last_log", "")

    ctx = _get_ctx()
    if ctx is None:
        st.info(t("HOURLY_NO_OUTPUTS_YET"))
    else:
        c1, c2 = st.columns(2, gap="large")

        with c1:
            if st.button(t("HOURLY_GENERATE_EXCEL"), width="stretch"):
                suffix = _ts_suffix(bool(get(TOOL_ID, "add_timestamp_to_outputs", True)))
                out = REPORTS_DIR / f"hourly_results_analysis{suffix}.xlsx"
                export_excel(ctx, out)
                set_(TOOL_ID, "last_excel", str(out))
                st.success(t("HOURLY_EXCEL_READY"))

        with c2:
            if st.button(t("HOURLY_GENERATE_PDF"), width="stretch"):
                suffix = _ts_suffix(bool(get(TOOL_ID, "add_timestamp_to_outputs", True)))
                out = REPORTS_DIR / f"hourly_results_analysis{suffix}.pdf"
                export_pdf(ctx, out)
                set_(TOOL_ID, "last_pdf", str(out))
                st.success(t("HOURLY_PDF_READY"))

        if st.button(t("HOURLY_GENERATE_LOG"), width="stretch"):
            suffix = _ts_suffix(bool(get(TOOL_ID, "add_timestamp_to_outputs", True)))
            out = LOGS_DIR / f"hourly_results_analysis{suffix}.txt"
            df = ctx.df_raw
            lines = [
                f"file={ctx.input_file.name}",
                f"project={ctx.general_info.get('Project_name','')}",
                f"variant={ctx.general_info.get('Variant_name','')}",
                f"pvsyst_version={ctx.general_info.get('PVSyst_version','')}",
                f"simulation_date={ctx.general_info.get('Simulation_date','')}",
                f"period_start={df.index.min()}",
                f"period_end={df.index.max()}",
                f"rows={len(df)}",
                f"limit_column={ctx.options.threshold_column}",
                f"limit_value={ctx.options.threshold_value}",
                f"night_disconnection={ctx.options.night_disconnection}",
                f"grid_capacity_kw={getattr(ctx.options, 'grid_capacity_kw', None)}",
                f"available_analyses={','.join(ctx.results.keys())}",
            ]
            _write_log(out, lines)
            set_(TOOL_ID, "last_log", str(out))
            st.success(t("HOURLY_LOG_READY"))

        if not last_excel and not last_pdf and not last_log:
            st.info(t("HOURLY_NO_EXPORTS_YET"))
        else:
            if last_excel:
                _download_from_path(
                    t("HOURLY_DOWNLOAD_EXCEL"),
                    Path(last_excel),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            if last_pdf:
                _download_from_path(t("HOURLY_DOWNLOAD_PDF"), Path(last_pdf), mime="application/pdf")
            if last_log:
                _download_from_path(t("HOURLY_DOWNLOAD_LOG"), Path(last_log), mime="text/plain")