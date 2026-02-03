# app/pages/20_TMY_compare.py
from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from app.bootstrap import configure_page, bootstrap
from ui.tool_layout import tool_header, section
from ui.tool_state import init_tool_state, get, set_
from ui.i18n import t

from core.meteo.tmy_compare import compare_tmy_sources


# NOTE: page_title doit rester statique (pas t(...)) pour éviter le piège Streamlit
configure_page(page_title="TMY Compare", page_icon="⚖️", layout="wide")

TOOL_ID = "tmy_compare"

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
        "threshold_mean_pct": 5.0,
        "last_pdf": "",
    },
)

# Header standard
tool_header(icon="⚖️", title_key="TOOL_TMY_COMPARE_TITLE", desc_key="TOOL_TMY_COMPARE_DESC", badge="NEW")


# -----------------------------------------------------------------------------
# Downloads
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Charts (Altair)
# -----------------------------------------------------------------------------
COLOR_A = "#1f77b4"  # bleu pro
COLOR_B = "#ff7f0e"  # orange pro


def _as_dt(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["datetime"] = pd.to_datetime(out.get("datetime"), errors="coerce")
    out = out.dropna(subset=["datetime"])
    return out


def _interactive_overlay_long(df_long: pd.DataFrame, y_title: str) -> alt.Chart:
    """
    df_long must have: datetime, value, source ('A' or 'B')
    """
    return (
        alt.Chart(df_long)
        .mark_line()
        .encode(
            x=alt.X("datetime:T", title=t("TMY_DATE")),
            y=alt.Y("value:Q", title=y_title),
            color=alt.Color(
                "source:N",
                title="",
                scale=alt.Scale(
                    domain=["A", "B"],
                    range=[COLOR_A, COLOR_B],
                ),
            ),
            tooltip=[
                alt.Tooltip("datetime:T", title=t("TMY_DATE")),
                alt.Tooltip("source:N", title=t("TMY_COMPARE_FILE")),
                alt.Tooltip("value:Q", title=y_title),
            ],
        )
        .interactive()
    )


def _interactive_delta(df: pd.DataFrame, delta_col: str, y_title: str) -> alt.Chart:
    line = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("datetime:T", title=t("TMY_DATE")),
            y=alt.Y(f"{delta_col}:Q", title=y_title),
            tooltip=[
                alt.Tooltip("datetime:T", title=t("TMY_DATE")),
                alt.Tooltip(f"{delta_col}:Q", title=t("TMY_COMPARE_DELTA")),
            ],
        )
    )
    zero = alt.Chart(pd.DataFrame({"y": [0.0]})).mark_rule().encode(y="y:Q")
    return (line + zero).interactive()


def _build_long_series(df_a: pd.DataFrame, df_b: pd.DataFrame, var: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      - df_long: datetime, value, source
      - df_delta: datetime, Delta
    """
    tmp = pd.DataFrame({"datetime": df_a["datetime"]})
    tmp["A"] = pd.to_numeric(df_a[var], errors="coerce")
    tmp["B"] = pd.to_numeric(df_b[var], errors="coerce")
    tmp["Delta"] = tmp["A"] - tmp["B"]
    tmp = tmp.dropna(subset=["datetime"])

    df_long = pd.concat(
        [
            tmp[["datetime", "A"]].rename(columns={"A": "value"}).assign(source="A"),
            tmp[["datetime", "B"]].rename(columns={"B": "value"}).assign(source="B"),
        ],
        ignore_index=True,
    ).dropna(subset=["datetime", "value"])

    df_delta = tmp[["datetime", "Delta"]].dropna(subset=["datetime", "Delta"])
    return df_long, df_delta


# =============================================================================
# 1) Inputs
# =============================================================================
with section("SECTION_INPUTS", icon="🧾"):
    cA, cB = st.columns(2)
    with cA:
        uploaded_a = st.file_uploader(
            t("TMY_COMPARE_UPLOAD_A"),
            type=["csv", "txt"],
            accept_multiple_files=False,
            key="tmy_compare_a",
        )
    with cB:
        uploaded_b = st.file_uploader(
            t("TMY_COMPARE_UPLOAD_B"),
            type=["csv", "txt"],
            accept_multiple_files=False,
            key="tmy_compare_b",
        )

    c1, c2 = st.columns(2)
    with c1:
        target_irradiance_unit = st.selectbox(
            t("TMY_COMPARE_TARGET_IRR_UNIT"),
            options=["W/m²", "kW/m²"],
            index=0 if get(TOOL_ID, "target_irradiance_unit", "W/m²") == "W/m²" else 1,
        )
        set_(TOOL_ID, "target_irradiance_unit", target_irradiance_unit)

    with c2:
        energy_unit = st.selectbox(
            t("TMY_COMPARE_ENERGY_UNIT"),
            options=["Wh/m²", "kWh/m²"],
            index=0 if get(TOOL_ID, "energy_unit", "kWh/m²") == "Wh/m²" else 1,
        )
        set_(TOOL_ID, "energy_unit", energy_unit)

    resample_hourly_if_subhourly = st.checkbox(
        t("TMY_COMPARE_RESAMPLE_1H"),
        value=bool(get(TOOL_ID, "resample_hourly_if_subhourly", True)),
    )
    set_(TOOL_ID, "resample_hourly_if_subhourly", resample_hourly_if_subhourly)

    threshold_mean_pct = st.number_input(
        t("TMY_COMPARE_THRESHOLD_MEAN_PCT"),
        min_value=0.0,
        max_value=100.0,
        value=float(get(TOOL_ID, "threshold_mean_pct", 5.0)),
        step=0.5,
    )
    set_(TOOL_ID, "threshold_mean_pct", float(threshold_mean_pct))


# =============================================================================
# 2) Run
# =============================================================================
with section("SECTION_RUN", icon="▶️"):
    st.markdown('<div class="pv-run">', unsafe_allow_html=True)
    run_btn = st.button(
        t("TMY_COMPARE_RUN"),
        type="primary",
    )
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# 3) Results
# =============================================================================
with section("SECTION_RESULTS", icon="📊"):
    if run_btn:
        if uploaded_a is None or uploaded_b is None:
            st.warning(t("TMY_COMPARE_NEED_TWO_FILES"))
        else:
            try:
                with st.spinner(t("TMY_COMPARE_RUNNING")):
                    result = compare_tmy_sources(
                        source_a=uploaded_a.getvalue(),
                        name_a=uploaded_a.name,
                        source_b=uploaded_b.getvalue(),
                        name_b=uploaded_b.name,
                        outputs_dir=OUTPUTS_DIR,
                        output_mode="runs",
                        target_irradiance_unit=get(TOOL_ID, "target_irradiance_unit", "W/m²"),
                        energy_unit=get(TOOL_ID, "energy_unit", "kWh/m²"),
                        resample_hourly_if_subhourly=get(TOOL_ID, "resample_hourly_if_subhourly", True),
                        threshold_mean_pct=float(get(TOOL_ID, "threshold_mean_pct", 5.0)),
                        force_hourly_step_minutes=60,
                    )
            except Exception as e:
                st.error(t("TMY_COMPARE_ERROR_READ"))
                st.exception(e)
            else:
                st.success(t("TMY_COMPARE_DONE"))
                set_(TOOL_ID, "last_pdf", str(result.report_pdf))

                # --- Summary
                st.subheader(t("TMY_COMPARE_SUMMARY"))

                native_step_a = int(getattr(result, "native_step_a_min", result.ds_a.time_step_minutes))
                native_step_b = int(getattr(result, "native_step_b_min", result.ds_b.time_step_minutes))
                used_step = int(getattr(result, "used_step_min", 60 if get(TOOL_ID, "resample_hourly_if_subhourly", True) else min(native_step_a, native_step_b)))

                st.write(
                    {
                        t("TMY_COMPARE_UPLOAD_A"): result.ds_a.source_name,
                        t("TMY_COMPARE_UPLOAD_B"): result.ds_b.source_name,
                        t("TMY_COMPARE_STEP_NATIVE_A"): f"{native_step_a} min",
                        t("TMY_COMPARE_STEP_NATIVE_B"): f"{native_step_b} min",
                        t("TMY_COMPARE_STEP_USED"): f"{used_step} min",
                        t("TMY_COMPARE_ALERT"): bool(result.alert_flag),
                    }
                )

                # --- Energy (full files)
                st.subheader(t("TMY_COMPARE_ENERGY_FULL"))
                ea, eb = result.energy_a, result.energy_b
                rows = [
                    {
                        t("TMY_COMPARE_FILE"): "A",
                        "GHI": ea.annual_ghi,
                        "DNI": ea.annual_dni,
                        "DHI": ea.annual_dhi,
                        t("TMY_UNIT"): ea.unit,
                    },
                    {
                        t("TMY_COMPARE_FILE"): "B",
                        "GHI": eb.annual_ghi,
                        "DNI": eb.annual_dni,
                        "DHI": eb.annual_dhi,
                        t("TMY_UNIT"): eb.unit,
                    },
                ]
                st.dataframe(pd.DataFrame(rows), width="stretch")

                # --- Metrics (human labels)
                st.subheader(t("TMY_COMPARE_METRICS"))

                HUMAN_VAR = {
                    "ghi": t("TMY_COMPARE_VAR_GHI"),
                    "dni": t("TMY_COMPARE_VAR_DNI"),
                    "dhi": t("TMY_COMPARE_VAR_DHI"),
                    "temp": t("TMY_COMPARE_VAR_TEMP"),
                    "wind_speed": t("TMY_COMPARE_VAR_WIND"),
                }

                HUMAN_METRICS = {
                    "variable": t("TMY_COMPARE_COL_VARIABLE"),
                    "n": t("TMY_COMPARE_COL_N"),
                    "mean_a": t("TMY_COMPARE_COL_MEAN_A"),
                    "mean_b": t("TMY_COMPARE_COL_MEAN_B"),
                    "bias_mean": t("TMY_COMPARE_COL_BIAS"),
                    "mae": t("TMY_COMPARE_COL_MAE"),
                    "rmse": t("TMY_COMPARE_COL_RMSE"),
                    "mean_pct": t("TMY_COMPARE_COL_MEAN_PCT"),
                    "max_pct": t("TMY_COMPARE_COL_MAX_PCT"),
                    "max_abs": t("TMY_COMPARE_COL_MAX_ABS"),
                }

                if result.metrics is None or result.metrics.empty:
                    st.info(t("TMY_COMPARE_NO_COMMON_VARS"))
                else:
                    dfm = result.metrics.copy()
                    if "variable" in dfm.columns:
                        dfm["variable"] = dfm["variable"].map(lambda v: HUMAN_VAR.get(v, str(v)))

                    for c in ["mean_a", "mean_b", "bias_mean", "mae", "rmse", "mean_pct", "max_pct", "max_abs"]:
                        if c in dfm.columns:
                            dfm[c] = pd.to_numeric(dfm[c], errors="coerce").round(3)

                    dfm = dfm.rename(columns=HUMAN_METRICS)
                    st.dataframe(dfm, width="stretch")

                # --- Interactive plots (A/B fixed colors + delta)
                st.subheader(t("TMY_COMPARE_PLOTS"))

                df_a = _as_dt(result.df_a)
                df_b = _as_dt(result.df_b)

                vars_to_plot = [v for v in ["ghi", "dni", "dhi", "temp"] if v in df_a.columns and v in df_b.columns]
                if not vars_to_plot:
                    st.info(t("TMY_COMPARE_NO_PLOTS"))
                else:
                    for v in vars_to_plot:
                        unit = result.ds_a.units_by_col.get(v, "")
                        label_var = HUMAN_VAR.get(v, v.upper())
                        y_title = f"{label_var} ({unit})".strip()

                        df_long, df_delta = _build_long_series(df_a, df_b, v)

                        st.markdown(f"**{t('TMY_COMPARE_VAR_BLOCK').format(var=label_var)}**")

                        c1, c2 = st.columns(2)
                        with c1:
                            st.altair_chart(_interactive_overlay_long(df_long, y_title=y_title), width="stretch")
                        with c2:
                            st.altair_chart(
                                _interactive_delta(df_delta, "Delta", y_title=f"{t('TMY_COMPARE_DELTA')} ({unit})".strip()),
                                width="stretch",
                            )
    else:
        st.info(t("TMY_COMPARE_NO_OUTPUTS_YET"))


# =============================================================================
# 4) Export (PDF only)
# =============================================================================
with section("SECTION_EXPORT", icon="📤"):
    pdf_s = get(TOOL_ID, "last_pdf", "")
    if not pdf_s:
        st.info(t("TMY_COMPARE_NO_OUTPUTS_YET"))
    else:
        _download_button_from_path(t("TMY_COMPARE_DOWNLOAD_PDF"), Path(pdf_s), mime="application/pdf")
