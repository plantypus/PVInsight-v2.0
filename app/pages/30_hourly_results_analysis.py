# app/pages/30_hourly_results_analysis.py
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
import streamlit as st
import plotly.express as px

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
        "grid_capacity_kw": 0.0,  # optional, number (0 = not provided)
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


def _parse_optional_float(s: str) -> Optional[float]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        v = float(s.replace(",", "."))
        return v if v > 0 else None
    except Exception:
        return None


# =============================================================================
# Plotly helpers
# =============================================================================
def _bar(df: pd.DataFrame, x: str, y: str, title: str, xlab: str, ylab: str):
    return px.bar(df, x=x, y=y, title=title, labels={x: xlab, y: ylab})


def _line(df: pd.DataFrame, x: str, y: str, title: str, xlab: str, ylab: str):
    return px.line(df, x=x, y=y, markers=True, title=title, labels={x: xlab, y: ylab})


# =============================================================================
# 1) Inputs
# =============================================================================
with section("SECTION_INPUTS", icon="🧾"):
    st.markdown(f"**{t('HOURLY_INPUTS_GUIDE_TITLE')}**")
    st.markdown(
        "- " + t("HOURLY_INPUTS_GUIDE_THRESHOLD") + "\n"
        "- " + t("HOURLY_INPUTS_GUIDE_DISTRIBUTION") + "\n"
        "- " + t("HOURLY_INPUTS_GUIDE_CLIPPING") + "\n"
        "- " + t("HOURLY_INPUTS_GUIDE_NIGHT") + "\n"
        "- " + t("HOURLY_INPUTS_GUIDE_GRID_CAPACITY")
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
        t("HOURLY_THRESHOLD_COLUMN_LABEL"),
        value=str(get(TOOL_ID, "threshold_column", "E_Grid")),
        help=t("HOURLY_THRESHOLD_COLUMN_HELP"),
    )
    set_(TOOL_ID, "threshold_column", threshold_col)

    threshold_value = st.number_input(
        t("HOURLY_THRESHOLD_VALUE_LABEL"),
        value=float(get(TOOL_ID, "threshold_value", 0.0)),
        step=1.0,
        help=t("HOURLY_THRESHOLD_VALUE_HELP"),
    )
    set_(TOOL_ID, "threshold_value", float(threshold_value))

    night_disc = st.checkbox(
        t("HOURLY_NIGHT_DISCONNECT_LABEL"),
        value=bool(get(TOOL_ID, "night_disconnection", True)),
        help=t("HOURLY_NIGHT_DISCONNECT_HELP"),
    )
    set_(TOOL_ID, "night_disconnection", bool(night_disc))

    grid_capacity_kw = st.number_input(
        t("HOURLY_GRID_CAPACITY_LABEL"),
        value=float(get(TOOL_ID, "grid_capacity_kw", 0.0)),
        min_value=0.0,
        step=200.0,
        help=t("HOURLY_GRID_CAPACITY_HELP"),
    )
    set_(TOOL_ID, "grid_capacity_kw", float(grid_capacity_kw))


# =============================================================================
# 2) Run
# =============================================================================
with section("SECTION_RUN", icon="▶️"):
    st.markdown('<div class="pv-run">', unsafe_allow_html=True)
    run_btn = st.button(t("HOURLY_RUN"), type="primary")
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# 3) Results
# =============================================================================
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
                        grid_capacity_kw=cap_kw,  # optional (should be supported by pipeline/options)
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

        # ---------------------------------------------------------------------
        # Global production
        # ---------------------------------------------------------------------
        gp = ctx.results.get("global_production", {})
        st.subheader(t("HOURLY_GLOBAL_PRODUCTION_TITLE"))

        if not gp or not gp.get("available", False):
            st.warning(t("HOURLY_GLOBAL_NOT_AVAILABLE"))
            if gp and gp.get("missing_columns"):
                st.write({t("HOURLY_MISSING_COLUMNS"): ", ".join(gp["missing_columns"])})
                if gp.get("suggestions"):
                    st.write({t("HOURLY_SUGGESTED_COLUMNS"): gp["suggestions"]})
        else:
            s = gp["summary"]
            dt_meta = s.get("dt_meta", {}) if isinstance(s.get("dt_meta", {}), dict) else {}
            irregular = float(dt_meta.get("irregular_share", 0.0))
            grid_capacity = getattr(ctx.options, "grid_capacity_kw", None)

            # --- annual load factor: fallback chain (global_production -> grid_limit -> load_factor)
            annual_lf = s.get("annual_load_factor", None)

            gl = ctx.results.get("grid_limit", {})
            if annual_lf is None and gl and gl.get("available", False):
                annual_lf = (gl.get("summary", {}) or {}).get("annual_load_factor", None)

            lf = ctx.results.get("load_factor", {})
            if annual_lf is None and lf and lf.get("available", False):
                annual_lf = (lf.get("summary", {}) or {}).get("annual_load_factor", None)


            st.write({
                t("HOURLY_GLOBAL_PROJECT"): ctx.general_info.get("Project_name", "") or "-",
                t("HOURLY_GLOBAL_PROJECT_FILE"): ctx.general_info.get("Project_file", "") or "-",
                t("HOURLY_GLOBAL_VARIANT"): ctx.general_info.get("Variant_name", "") or "-",
                t("HOURLY_GLOBAL_TIMESTEP"): f"{float(s.get('dt_hours', 1.0)):g} h",
                t("HOURLY_GLOBAL_TIMESTEP_QUALITY"): f"{(1.0 - irregular) * 100:.1f} %",
                t("HOURLY_GLOBAL_OPERATING_HOURS"): f"{format_number(s['operating_hours'], 0)} h ({s['operating_pct']:.1f} %)",
                t("HOURLY_GLOBAL_NET_PRODUCTION") + " (kWh)": format_number(s["net_production_kwh"], 0),
                t("HOURLY_GLOBAL_PRODUCTION_NO_IMPORT") + " (kWh)": format_number(s["production_without_import_kwh"], 0),
                t("HOURLY_GLOBAL_NIGHT_CONSUMPTION") + " (kWh)": format_number(s["night_consumption_kwh"], 0),
                t("HOURLY_GLOBAL_IMPORT_HOURS"): f"{format_number(s['import_hours'], 0)} h",
                t("HOURLY_GLOBAL_GRID_CAPACITY"): (f"{format_number(grid_capacity, 0)} kW" if grid_capacity else t("HOURLY_GLOBAL_GRID_CAPACITY_NONE")),
                t("HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR"): (
                    f"{100.0 * float(annual_lf):.2f} %"
                    if annual_lf is not None else t("HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR_NONE")
                ),
            })

        # ---------------------------------------------------------------------
        # File summary
        # ---------------------------------------------------------------------
        st.subheader(t("HOURLY_SUMMARY"))
        st.write({
            t("HOURLY_SUMMARY_FILE"): ctx.input_file.name,
            t("HOURLY_SUMMARY_PVSYST_VERSION"): ctx.general_info.get("PVSyst_version", ""),
            t("HOURLY_SUMMARY_SIM_DATE"): ctx.general_info.get("Simulation_date", ""),
            t("HOURLY_SUMMARY_PERIOD"): f"{df.index.min()} → {df.index.max()}",
            t("HOURLY_SUMMARY_ROWS"): int(len(df)),
            t("HOURLY_SUMMARY_COLUMNS"): ", ".join(list(df.columns)),
            t("HOURLY_SUMMARY_NIGHT_OPTION"): t("HOURLY_NIGHT_DISCONNECT_ON") if bool(ctx.options.night_disconnection) else t("HOURLY_NIGHT_DISCONNECT_OFF"),
        })

        tab_graphs, tab_dist = st.tabs([t("HOURLY_TAB_GRAPHS"), t("HOURLY_TAB_DISTRIBUTION")])

        # ---------------------------------------------------------------------
        # TAB: Graphs (2/3 left column)
        # ---------------------------------------------------------------------
        with tab_graphs:
            left, right = st.columns([2, 1], gap="large")

            # Threshold (existing)
            thr = ctx.results.get("threshold", {})
            with right:
                st.markdown(f"**{t('HOURLY_RESULTS_THRESHOLD')}**")

            if thr and thr.get("available", False):
                thr_s = thr["summary"]
                monthly = thr.get("monthly")
                monthly_pct = thr.get("monthly_pct")
                night_monthly = thr.get("night_consumption_monthly")

                with left:
                    if monthly is not None and not monthly.empty:
                        st.plotly_chart(
                            _bar(
                                monthly,
                                x="month_name",
                                y="hours_above",
                                title=t("HOURLY_CHART_MONTHLY_HOURS"),
                                xlab=t("HOURLY_COL_MONTH"),
                                ylab=t("HOURLY_Y_HOURS"),
                            ),
                            width="stretch",
                        )
                        st.plotly_chart(
                            _bar(
                                monthly,
                                x="month_name",
                                y="energy_above_kwh",
                                title=t("HOURLY_CHART_MONTHLY_ENERGY_ABOVE"),
                                xlab=t("HOURLY_COL_MONTH"),
                                ylab=t("HOURLY_Y_ENERGY_KWH"),
                            ),
                            width="stretch",
                        )

                    if monthly_pct is not None and not monthly_pct.empty:
                        st.plotly_chart(
                            _line(
                                monthly_pct,
                                x="month_name",
                                y="pct_above",
                                title=t("HOURLY_CHART_MONTHLY_SHARE"),
                                xlab=t("HOURLY_COL_MONTH"),
                                ylab=t("HOURLY_Y_PERCENT"),
                            ),
                            width="stretch",
                        )

                    if night_monthly is not None and not night_monthly.empty:
                        st.plotly_chart(
                            _bar(
                                night_monthly,
                                x="month_name",
                                y="night_consumption_kwh",
                                title=t("HOURLY_CHART_NIGHT_IMPORT"),
                                xlab=t("HOURLY_COL_MONTH"),
                                ylab=t("HOURLY_Y_ENERGY_KWH"),
                            ),
                            width="stretch",
                        )

                with right:
                    st.write({
                        t("HOURLY_THR_OPERATING_HOURS"): f"{format_number(thr_s['operating_hours'], 0)} h",
                        t("HOURLY_THR_HOURS_ABOVE"): f"{format_number(thr_s['hours_above'], 0)} h",
                        t("HOURLY_THR_SHARE_ABOVE"): f"{thr_s['pct_above_operating_time']:.1f} %",
                        t("HOURLY_THR_ENERGY_ABOVE") + " (kWh)": format_number(thr_s["energy_above_kwh"], 0),
                    })
                    st.divider()
                    st.markdown(f"**{t('HOURLY_RESULTS_NIGHT')}**")
                    st.write({
                        t("HOURLY_NIGHT_HOURS"): f"{format_number(thr_s['night_import_hours'], 0)} h",
                        t("HOURLY_NIGHT_CONSUMPTION") + " (kWh)": format_number(thr_s["night_consumption_kwh"], 0),
                    })
            else:
                with left:
                    st.warning(t("HOURLY_THRESHOLD_NOT_AVAILABLE"))
                with right:
                    if thr and thr.get("missing_columns"):
                        st.write({t("HOURLY_MISSING_COLUMNS"): ", ".join(thr["missing_columns"])})
                        if thr.get("suggestions"):
                            st.write({t("HOURLY_SUGGESTED_COLUMNS"): thr["suggestions"]})

            # Grid limitation (new)
            gl = ctx.results.get("grid_limit", {})
            with right:
                st.divider()
                st.markdown(f"**{t('HOURLY_RESULTS_GRID_LIMIT')}**")
                with st.popover(t("HOURLY_HELP_BUTTON")):
                     st.markdown(t("HOURLY_HELP_GRID_LIMIT_MD"))

            if gl and gl.get("available", False):
                gl_s = gl["summary"]
                gl_m = gl.get("monthly")

                with left:
                    if gl_m is not None and not gl_m.empty:
                        st.plotly_chart(
                            _bar(
                                gl_m,
                                x="month_name",
                                y="lost_kwh",
                                title=t("HOURLY_CHART_GRID_LIMIT_LOST_KWH"),
                                xlab=t("HOURLY_COL_MONTH"),
                                ylab=t("HOURLY_Y_ENERGY_KWH"),
                            ),
                            width="stretch",
                        )
                        st.plotly_chart(
                            _line(
                                gl_m,
                                x="month_name",
                                y="lost_pct",
                                title=t("HOURLY_CHART_GRID_LIMIT_LOST_PCT"),
                                xlab=t("HOURLY_COL_MONTH"),
                                ylab=t("HOURLY_Y_PERCENT"),
                            ),
                            width="stretch",
                        )

                with right:
                    st.write({
                        t("HOURLY_GRID_LOST_ENERGY") + " (kWh)": format_number(gl_s["lost_kwh"], 0),
                        t("HOURLY_GRID_LOST_PCT"): f"{gl_s['lost_pct']:.2f} %",
                        t("HOURLY_GRID_HOURS_LIMITED"): f"{format_number(gl_s['hours_limited'], 0)} h",
                        t("HOURLY_GRID_ANNUAL_LF"): (
                            f"{100.0 * float(gl_s.get('annual_load_factor')):.2f} %"
                            if gl_s.get("annual_load_factor") is not None else t("HOURLY_GRID_ANNUAL_LF_NONE")
                        ),
                    })
            else:
                with right:
                    st.write(t("HOURLY_GRID_LIMIT_NOT_AVAILABLE"))

            # Load factor / PF (new)
            lf = ctx.results.get("load_factor", {})
            with right:
                st.divider()
                st.markdown(f"**{t('HOURLY_RESULTS_LOAD_FACTOR')}**")
                with st.popover(t("HOURLY_HELP_BUTTON")):
                    st.markdown(t("HOURLY_HELP_LOAD_FACTOR_MD"))


            if lf and lf.get("available", False):
                lf_s = lf["summary"]
                lf_m = lf.get("monthly")
                sat = lf.get("saturation_distribution")

                with left:
                    if lf_m is not None and not lf_m.empty and "cosphi" in lf_m.columns and lf_m["cosphi"].notna().any():
                        st.plotly_chart(
                            _line(
                                lf_m,
                                x="month_name",
                                y="cosphi",
                                title=t("HOURLY_CHART_COSPHI_MONTHLY"),
                                xlab=t("HOURLY_COL_MONTH"),
                                ylab=t("HOURLY_Y_COSPHI"),
                            ),
                            width="stretch",
                        )

                    if sat is not None and not sat.empty:
                        st.plotly_chart(
                            _bar(
                                sat,
                                x="class",
                                y="pct_time",
                                title=t("HOURLY_CHART_SATURATION_DIST"),
                                xlab=t("HOURLY_COL_CLASS"),
                                ylab=t("HOURLY_Y_PERCENT"),
                            ),
                            width="stretch",
                        )

                with right:
                    st.write({
                        t("HOURLY_LF_COSPHI"): (
                            f"{float(lf_s.get('cosphi')):.3f}" if lf_s.get("cosphi") is not None else t("HOURLY_LF_NOT_AVAILABLE")
                        ),
                        t("HOURLY_LF_Q_SHARE"): (
                            f"{100.0 * float(lf_s.get('q_share')):.2f} %" if lf_s.get("q_share") is not None else t("HOURLY_LF_NOT_AVAILABLE")
                        ),
                        t("HOURLY_LF_ANNUAL_LF"): (
                            f"{100.0 * float(lf_s.get('annual_load_factor')):.2f} %"
                            if lf_s.get("annual_load_factor") is not None else t("HOURLY_LF_ANNUAL_LF_NONE")
                        ),
                    })
            else:
                with right:
                    st.write(t("HOURLY_LOAD_FACTOR_NOT_AVAILABLE"))

        # ---------------------------------------------------------------------
        # TAB: Distribution & Tables
        # ---------------------------------------------------------------------
        with tab_dist:
            left, right = st.columns([2, 1], gap="large")

            # Threshold tables
            thr = ctx.results.get("threshold", {})
            if thr and thr.get("available", False):
                with left:
                    st.markdown(f"**{t('HOURLY_TABLE_THRESHOLD_MONTHLY')}**")
                    m = thr["monthly"].copy()
                    m_disp = pd.DataFrame({
                        t("HOURLY_COL_MONTH"): m["month_name"],
                        t("HOURLY_COL_HOURS_ABOVE"): m["hours_above"].map(lambda v: format_number(v, 0)),
                        t("HOURLY_COL_ENERGY_ABOVE_KWH"): m["energy_above_kwh"].map(lambda v: format_number(v, 0)),
                    })
                    st.dataframe(m_disp, width="stretch", hide_index=True)

                    st.markdown(f"**{t('HOURLY_TABLE_THRESHOLD_SEASONAL')}**")
                    s2 = thr["seasonal"].copy()
                    s2_disp = pd.DataFrame({
                        t("HOURLY_COL_SEASON"): s2["season"],
                        t("HOURLY_COL_HOURS_ABOVE"): s2["hours_above"].map(lambda v: format_number(v, 0)),
                        t("HOURLY_COL_ENERGY_ABOVE_KWH"): s2["energy_above_kwh"].map(lambda v: format_number(v, 0)),
                    })
                    st.dataframe(s2_disp, width="stretch", hide_index=True)

            # Grid limitation table
            gl = ctx.results.get("grid_limit", {})
            if gl and gl.get("available", False):
                with left:
                    st.markdown(f"**{t('HOURLY_TABLE_GRID_LIMIT_MONTHLY')}**")
                    gm = gl["monthly"].copy()
                    gm_disp = pd.DataFrame({
                        t("HOURLY_COL_MONTH"): gm["month_name"],
                        t("HOURLY_GRID_LOST_ENERGY") + " (kWh)": gm["lost_kwh"].map(lambda v: format_number(v, 0)),
                        t("HOURLY_GRID_LOST_PCT"): gm["lost_pct"].map(lambda v: f"{float(v):.2f} %"),
                        t("HOURLY_GRID_HOURS_LIMITED"): gm["hours_limited"].map(lambda v: format_number(v, 0)),
                        t("HOURLY_GRID_INJECTED") + " (kWh)": gm["injected_kwh"].map(lambda v: format_number(v, 0)),
                    })
                    st.dataframe(gm_disp, width="stretch", hide_index=True)

            # Power distribution
            pd_res = ctx.results.get("power_distribution", {})
            with right:
                st.markdown(f"**{t('HOURLY_RESULTS_DISTRIBUTION')}**")
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
                        t("HOURLY_COL_HOURS"): d["hours"].map(lambda v: format_number(v, 0)),
                        t("HOURLY_COL_PCT_TIME"): d["pct_time"].map(lambda x: f"{float(x):.1f} %"),
                        t("HOURLY_COL_ENERGY_KWH"): d["energy_kwh"].map(lambda v: format_number(v, 0)),
                    })
                    st.dataframe(d_disp, width="stretch", hide_index=True)

            # Load factor tables
            lf = ctx.results.get("load_factor", {})
            if lf and lf.get("available", False):
                with right:
                    st.markdown(f"**{t('HOURLY_TABLE_LOAD_FACTOR_MONTHLY')}**")
                    lm = lf["monthly"].copy()
                    # cosphi / q_share may be None
                    lm_disp = pd.DataFrame({
                        t("HOURLY_COL_MONTH"): lm["month_name"],
                        t("HOURLY_LF_S_APPARENT"): lm["S_kWh_equiv"].map(lambda v: format_number(v, 0)),
                        t("HOURLY_LF_Q_REACTIVE"): lm["Q_kWh_equiv"].map(lambda v: format_number(v, 0)),
                        t("HOURLY_LF_P_ACTIVE"): lm["P_kWh"].map(lambda v: format_number(v, 0) if v is not None else "—"),
                        t("HOURLY_LF_COSPHI"): lm["cosphi"].map(lambda v: f"{float(v):.3f}" if v is not None else "—"),
                        t("HOURLY_LF_Q_SHARE"): lm["q_share"].map(lambda v: f"{100.0 * float(v):.2f} %" if v is not None else "—"),
                    })
                    st.dataframe(lm_disp, width="stretch", hide_index=True)

                    sd = lf.get("saturation_distribution")
                    if sd is not None and not sd.empty:
                        st.markdown(f"**{t('HOURLY_TABLE_SATURATION_DIST')}**")
                        sd_disp = pd.DataFrame({
                            t("HOURLY_COL_CLASS"): sd["class"].astype(str),
                            t("HOURLY_COL_HOURS"): sd["hours"].map(lambda v: format_number(v, 0)),
                            t("HOURLY_COL_PCT_TIME"): sd["pct_time"].map(lambda v: f"{float(v):.1f} %"),
                        })
                        st.dataframe(sd_disp, width="stretch", hide_index=True)

        st.caption(f"outputs: {OUTPUTS_DIR}")


# =============================================================================
# 4) Export
# =============================================================================
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
            if st.button(t("HOURLY_GENERATE_EXCEL"), use_container_width=True):
                suffix = _ts_suffix(bool(get(TOOL_ID, "add_timestamp_to_outputs", True)))
                out = REPORTS_DIR / f"hourly_results_analysis{suffix}.xlsx"
                export_excel(ctx, out)
                set_(TOOL_ID, "last_excel", str(out))
                st.success(t("HOURLY_EXCEL_READY"))

        with c2:
            if st.button(t("HOURLY_GENERATE_PDF"), use_container_width=True):
                suffix = _ts_suffix(bool(get(TOOL_ID, "add_timestamp_to_outputs", True)))
                out = REPORTS_DIR / f"hourly_results_analysis{suffix}.pdf"
                export_pdf(ctx, out)
                set_(TOOL_ID, "last_pdf", str(out))
                st.success(t("HOURLY_PDF_READY"))

        if st.button(t("HOURLY_GENERATE_LOG"), use_container_width=True):
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
                f"threshold_column={ctx.options.threshold_column}",
                f"threshold_value={ctx.options.threshold_value}",
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
