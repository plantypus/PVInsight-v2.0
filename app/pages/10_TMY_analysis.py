# app/pages/10_TMY_analysis.py
from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from app.bootstrap import configure_page, bootstrap
from ui.tool_layout import tool_header, section
from ui.tool_state import init_tool_state, get, set_
from ui.i18n import t

from core.meteo.tmy_analysis import analyze_tmy_source


# NOTE: page_title doit rester statique (pas t(...)) pour éviter le piège Streamlit
configure_page(page_title="TMY Analysis", page_icon="🌤️", layout="wide")

TOOL_ID = "tmy_analysis"

# Bootstrap global (state + css) + paths
paths = bootstrap(render_sidebar_ui=True)
OUTPUTS_DIR = paths.outputs

# Defaults (par outil)
init_tool_state(
    TOOL_ID,
    defaults={
        "target_irradiance_unit": "W/m²",
        "energy_unit": "kWh/m²",
        "resample_hourly_if_subhourly": True,
        "add_timestamp_to_outputs": True,
        "last_pdf": "",
        "last_log": "",
    },
)

# Header standard
tool_header(icon="🌤️", title_key="TOOL_TMY_ANALYSIS_TITLE", desc_key="TOOL_TMY_ANALYSIS_DESC", badge="NEW")

OUTPUTS_DIR = OUTPUTS_DIR = paths.outputs

def _download_button_from_path(label: str, path: Path, mime: str) -> None:
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


def _interactive_timeseries(df: pd.DataFrame, col: str, y_title: str) -> alt.Chart:
    base = alt.Chart(df).encode(
        x=alt.X("datetime:T", title=t("TMY_DATE")),
        tooltip=[alt.Tooltip("datetime:T", title=t("TMY_DATE")), alt.Tooltip(f"{col}:Q", title=y_title)],
    )
    chart = base.mark_line().encode(
        y=alt.Y(f"{col}:Q", title=y_title),
    )
    return chart.interactive()


def _interactive_histogram(df: pd.DataFrame, col: str, x_title: str, bin_step: int | None = None, maxbins: int | None = None) -> alt.Chart:
    if bin_step is not None:
        x = alt.X(f"{col}:Q", bin=alt.Bin(step=bin_step), title=x_title)
    else:
        x = alt.X(f"{col}:Q", bin=alt.Bin(maxbins=maxbins or 30), title=x_title)

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=x,
            y=alt.Y("count():Q", title=t("TMY_COUNT")),
            tooltip=[alt.Tooltip("count():Q", title=t("TMY_COUNT"))],
        )
        .properties(height=260)
    )
    return chart.interactive()


# 1) Inputs
with section("SECTION_INPUTS", icon="🧾"):
    uploaded = st.file_uploader(
        t("TMY_UPLOAD_LABEL"),
        type=["csv", "txt"],
        accept_multiple_files=False,
    )

    c1, c2 = st.columns(2)
    with c1:
        target_irradiance_unit = st.selectbox(
            t("TMY_TARGET_IRR_UNIT"),
            options=["W/m²", "kW/m²"],
            index=0 if get(TOOL_ID, "target_irradiance_unit", "kW/m²") == "W/m²" else 1,
        )
        set_(TOOL_ID, "target_irradiance_unit", target_irradiance_unit)

    with c2:
        energy_unit = st.selectbox(
            t("TMY_ENERGY_UNIT"),
            options=["Wh/m²", "kWh/m²"],
            index=0 if get(TOOL_ID, "energy_unit", "kWh/m²") == "Wh/m²" else 1,
        )
        set_(TOOL_ID, "energy_unit", energy_unit)

    resample_hourly_if_subhourly = st.checkbox(
        t("TMY_RESAMPLE_1H"),
        value=bool(get(TOOL_ID, "resample_hourly_if_subhourly", True)),
    )
    set_(TOOL_ID, "resample_hourly_if_subhourly", resample_hourly_if_subhourly)

    add_timestamp_to_outputs = st.checkbox(
        t("TMY_TIMESTAMP_OUTPUTS"),
        value=bool(get(TOOL_ID, "add_timestamp_to_outputs", True)),
    )
    set_(TOOL_ID, "add_timestamp_to_outputs", add_timestamp_to_outputs)


# 2) Run
with section("SECTION_RUN", icon="▶️"):
    st.markdown('<div class="pv-run">', unsafe_allow_html=True)
    run_btn = st.button(
        t("TMY_RUN_ANALYSIS"),
        type="primary",
    )
    st.markdown('</div>', unsafe_allow_html=True)



# 3) Results
with section("SECTION_RESULTS", icon="📊"):
    if run_btn:
        if uploaded is None:
            st.warning(t("TMY_UPLOAD_LABEL"))
        else:
            with st.spinner(t("TMY_RUNNING")):
                result = analyze_tmy_source(
                    source=uploaded.getvalue(),
                    source_name=uploaded.name,
                    outputs_dir=OUTPUTS_DIR,
                    output_mode="flat",
                    target_irradiance_unit=get(TOOL_ID, "target_irradiance_unit", "W/m²"),
                    energy_unit=get(TOOL_ID, "energy_unit", "kWh/m²"),
                    resample_hourly_if_subhourly=get(TOOL_ID, "resample_hourly_if_subhourly", True),
                    add_timestamp_to_outputs=get(TOOL_ID, "add_timestamp_to_outputs", True),
                )

            st.success(t("TMY_DONE"))

            # store for Export (PDF/log only)
            set_(TOOL_ID, "last_pdf", str(result.report_pdf))
            set_(TOOL_ID, "last_log", str(result.log_path))

            df = result.dataset.df.copy()
            df["datetime"] = pd.to_datetime(df.get("datetime"), errors="coerce")
            df = df.dropna(subset=["datetime"])

            # Summary
            st.subheader(t("TMY_SUMMARY"))
            st.write(
                {
                    "source_name": result.dataset.source_name,
                    "time_step_minutes": result.dataset.time_step_minutes,
                    "rows": result.dataset.quality.n_rows,
                    "period_start": str(result.dataset.quality.start),
                    "period_end": str(result.dataset.quality.end),
                }
            )

            # Energy
            st.subheader(t("TMY_ENERGY"))
            e = result.energy
            rows = []
            if e.annual_ghi is not None:
                rows.append(("GHI", e.annual_ghi, e.unit))
            if e.annual_dni is not None:
                rows.append(("DNI", e.annual_dni, e.unit))
            if e.annual_dhi is not None:
                rows.append(("DHI", e.annual_dhi, e.unit))

            if rows:
                st.dataframe(pd.DataFrame(rows, columns=[t("TMY_VAR"), t("TMY_VALUE"), t("TMY_UNIT")]), width="stretch")
            else:
                st.info(t("TMY_NO_ENERGY"))

            # Pretty stats (preferred) fallback raw stats
            st.subheader(t("TMY_STATS"))
            if hasattr(result, "stats_pretty") and result.stats_pretty is not None and not result.stats_pretty.empty:
                st.dataframe(result.stats_pretty, width="stretch")
            else:
                st.dataframe(result.stats, width="stretch")

            # Interactive curves
            st.subheader(t("TMY_CURVES_TITLE"))
            c1, c2 = st.columns(2)

            with c1:
                if "ghi" in df.columns:
                    u = result.dataset.units_by_col.get("ghi", "")
                    st.altair_chart(
                        _interactive_timeseries(df[["datetime", "ghi"]].dropna(), "ghi", f"GHI ({u})".strip()),
                        width="stretch",
                    )
                else:
                    st.info(t("TMY_GHI_NOT_AVAILABLE"))

            with c2:
                if "temp" in df.columns:
                    u = result.dataset.units_by_col.get("temp", "")
                    st.altair_chart(
                        _interactive_timeseries(df[["datetime", "temp"]].dropna(), "temp", f"{t('TMY_TEMP_LABEL')} ({u})".strip()),
                        width="stretch",
                    )
                else:
                    st.info(t("TMY_TEMP_NOT_AVAILABLE"))

            # Interactive distributions
            st.subheader(t("TMY_DISTRIBUTIONS_TITLE"))

            # GHI histogram (exclude <= 0, bins step=200)
            st.markdown(f"**{t('TMY_GHI_DISTRIB_LABEL')}**")
            if "ghi" in df.columns:
                s = pd.to_numeric(df["ghi"], errors="coerce")
                s = s[s > 0].dropna()
                if not s.empty:
                    df_ghi = pd.DataFrame({"ghi": s})
                    u = result.dataset.units_by_col.get("ghi", "")
                    st.altair_chart(
                        _interactive_histogram(df_ghi, "ghi", f"GHI ({u})".strip(), bin_step=200),
                        width="stretch",
                    )
                    # Table % (computed in core if present, else simple fallback)
                    if hasattr(result, "ghi_distribution") and result.ghi_distribution is not None and not result.ghi_distribution.empty:
                        st.dataframe(result.ghi_distribution, width="stretch")
                else:
                    st.info(t("TMY_GHI_DISTRIB_EMPTY"))
            else:
                st.info(t("TMY_GHI_NOT_AVAILABLE"))

            # Temperature histogram
            st.markdown(f"**{t('TMY_TEMP_DISTRIB_LABEL')}**")
            if "temp" in df.columns:
                s = pd.to_numeric(df["temp"], errors="coerce").dropna()
                if not s.empty:
                    df_temp = pd.DataFrame({"temp": s})
                    u = result.dataset.units_by_col.get("temp", "")
                    st.altair_chart(
                        _interactive_histogram(df_temp, "temp", f"{t('TMY_TEMP_LABEL')} ({u})".strip(), maxbins=30),
                        width="stretch",
                    )
                else:
                    st.info(t("TMY_TEMP_DISTRIB_EMPTY"))
            else:
                st.info(t("TMY_TEMP_NOT_AVAILABLE"))

            # Warnings
            if result.dataset.warnings:
                st.subheader(t("TMY_WARNINGS"))
                for w in result.dataset.warnings:
                    st.warning(w)

            st.caption(f"outputs: {result.run_dir}")

    else:
        st.info(t("TMY_NO_OUTPUTS_YET"))


# 4) Export (PDF + log only)
with section("SECTION_EXPORT", icon="📤"):
    pdf_s = get(TOOL_ID, "last_pdf", "")
    log_s = get(TOOL_ID, "last_log", "")

    if not pdf_s and not log_s:
        st.info(t("TMY_NO_OUTPUTS_YET"))
    else:
        if pdf_s:
            _download_button_from_path(t("TMY_DOWNLOAD_PDF"), Path(pdf_s), mime="application/pdf")
        if log_s:
            _download_button_from_path(t("TMY_DOWNLOAD_LOG"), Path(log_s), mime="text/plain")
