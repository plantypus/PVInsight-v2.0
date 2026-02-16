# app/pages/40_compare_pan_to_ds.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from app.bootstrap import configure_page, bootstrap
from ui.tool_layout import tool_header, section
from ui.tool_state import init_tool_state, get, set_
from ui.i18n import t

from core.module.compare_pan_to_ds import compare_pan_to_ds
from core.module.iam_plot import extract_iam_profile

# NOTE: page_title doit rester statique (pas t(...)) pour éviter le piège Streamlit
configure_page(page_title="Compare PAN vs Datasheet", page_icon="🧾", layout="wide")

TOOL_ID = "compare_pan_to_ds"

paths = bootstrap(render_sidebar_ui=True)
OUTPUTS_DIR = paths.outputs


init_tool_state(
    TOOL_ID,
    defaults={
        "manufacturer": "dmegc",
        "add_timestamp_to_outputs": True,
        "last_pdf": "",
        "last_log": "",
        "project_name": "",
        "project_no": "",
        "solar_engineer": "",
    },
)

tool_header(icon="🧾", title_key="COMPARE_PAN_DS_TITLE", desc_key="COMPARE_PAN_DS_DESC", badge="NEW")


DS_MFR = [
    ("jinko", "COMPARE_PAN_DS_MFR_JINKO"),
    ("dmegc", "COMPARE_PAN_DS_MFR_DMEGC"),
    ("astronergy", "COMPARE_PAN_DS_MFR_ASTRONERGY"),
    ("das_solar", "COMPARE_PAN_DS_MFR_DAS_SOLAR"),
    ("canadian_solar", "COMPARE_PAN_DS_MFR_CANADIAN_SOLAR"),
]


# -----------------------------------------------------------------------------
# Utils UI
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


def _fmt_number(x, *, decimals: int = 3) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "–"
    try:
        v = float(x)
    except Exception:
        s = str(x).strip()
        return s if s else "–"

    # 1000-sep with narrow no-break space (French-friendly)
    s = f"{v:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", "\u202f")  # 12 345,678
    # trim trailing zeros nicely
    if decimals > 0:
        s = s.rstrip("0").rstrip(",")
    return s


def _fmt_unit_value(x, unit: str) -> str:
    if unit in ("W/m²", "V", "A", "W", "mm", "Ohm"):
        # numeric formats
        dec = 0 if unit in ("W", "mm", "Ohm") else 3
        return _fmt_number(x, decimals=dec)
    if unit in ("%/°C",):
        return _fmt_number(x, decimals=3)
    if unit in ("mA/°C", "mV/°C"):
        return _fmt_number(x, decimals=2)
    # fallback
    return str(x) if x is not None else "–"


def _fmt_pct(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "–"
    try:
        v = float(x)
    except Exception:
        return "–"
    # percent display with 1-2 decimals
    s = _fmt_number(v, decimals=2)
    return f"{s} %"


def _fmt_status(s: str) -> str:
    s = str(s or "").upper().strip()
    if s == "OK":
        return "✅ OK"
    if s == "WARN":
        return "⚠️ WARN"
    return "—"


def _format_analysis_date(iso_dt: str | None) -> str:
    if not iso_dt:
        return "–"
    # iso like "2026-02-12T17:03:22"
    try:
        dt = datetime.fromisoformat(str(iso_dt))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        # fallback (keep raw)
        return str(iso_dt)


def _format_compare_rows(rows: list[dict]) -> pd.DataFrame:
    """
    Output columns (pretty):
      - parameter, unit, pan, datasheet, deviation_pct, status
    """
    df = pd.DataFrame(rows).copy()
    if df.empty:
        return df

    # ensure columns
    for c in ("label", "unit", "pan", "datasheet", "deviation_pct", "status"):
        if c not in df.columns:
            df[c] = None

    out = pd.DataFrame()
    out["parameter"] = df["label"]
    out["unit"] = df["unit"]

    # format values using unit
    out["pan"] = [
        _fmt_unit_value(v, u) for v, u in zip(df["pan"].tolist(), df["unit"].tolist())
    ]
    out["datasheet"] = [
        _fmt_unit_value(v, u) for v, u in zip(df["datasheet"].tolist(), df["unit"].tolist())
    ]
    out["deviation_pct"] = [ _fmt_pct(v) for v in df["deviation_pct"].tolist() ]
    out["status"] = [ _fmt_status(v) for v in df["status"].tolist() ]

    return out


# -----------------------------------------------------------------------------
# IAM plotting
# -----------------------------------------------------------------------------
def _iam_altair_chart(df: pd.DataFrame) -> alt.Chart:
    """
    df columns: angle_deg, iam, loss_pct
    - limit x range so it does not auto-zoom too hard
    - half-width in layout, reasonable height
    """
    if df.empty:
        return alt.Chart(pd.DataFrame({"angle_deg": [], "iam": []}))

    # make sure numeric
    dff = df.copy()
    dff["angle_deg"] = pd.to_numeric(dff["angle_deg"], errors="coerce")
    dff["iam"] = pd.to_numeric(dff["iam"], errors="coerce")
    dff = dff.dropna(subset=["angle_deg", "iam"])

    x_min = float(dff["angle_deg"].min()) if not dff.empty else 0.0
    x_max = float(dff["angle_deg"].max()) if not dff.empty else 90.0

    base = alt.Chart(dff).encode(
        x=alt.X(
            "angle_deg:Q",
            title=t("COMPARE_PAN_DS_IAM_X"),
            scale=alt.Scale(domain=[x_min, x_max]),
        ),
        tooltip=[
            alt.Tooltip("angle_deg:Q", title=t("COMPARE_PAN_DS_IAM_X"), format=".1f"),
            alt.Tooltip("iam:Q", title=t("COMPARE_PAN_DS_IAM_Y"), format=".4f"),
            alt.Tooltip("loss_pct:Q", title=t("COMPARE_PAN_DS_IAM_LOSS"), format=".2f"),
        ],
    )

    line = base.mark_line().encode(y=alt.Y("iam:Q", title=t("COMPARE_PAN_DS_IAM_Y")))
    pts = base.mark_point(size=45).encode(y="iam:Q")

    # interactive but not too aggressive
    return (line + pts).properties(height=280)


def _iam_table_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["angle_deg"] = pd.to_numeric(out.get("angle_deg"), errors="coerce").round(1)
    out["iam"] = pd.to_numeric(out.get("iam"), errors="coerce").round(5)
    out["loss_pct"] = pd.to_numeric(out.get("loss_pct"), errors="coerce").round(2)
    out = out.dropna(subset=["angle_deg", "iam"])
    return out[["angle_deg", "iam", "loss_pct"]]


# =============================================================================
# 1) Inputs
# =============================================================================
with section("SECTION_INPUTS", icon="🧾"):
    st.markdown(f"**{t('COMPARE_PAN_DS_INPUTS_HELP')}**")

    mfr_codes = [k for k, _ in DS_MFR]
    mfr_labels = [t(lbl) for _, lbl in DS_MFR]

    current_mfr = str(get(TOOL_ID, "manufacturer", "jinko"))
    if current_mfr not in mfr_codes:
        current_mfr = mfr_codes[0]
    mfr_idx = mfr_codes.index(current_mfr)

    mfr_label = st.selectbox(
        t("COMPARE_PAN_DS_MFR_SELECT"),
        options=mfr_labels,
        index=mfr_idx,
        help=t("COMPARE_PAN_DS_MFR_HELP"),
    )
    manufacturer_code = mfr_codes[mfr_labels.index(mfr_label)]
    set_(TOOL_ID, "manufacturer", manufacturer_code)

    c1, c2 = st.columns(2)
    with c1:
        pan_file = st.file_uploader(
            t("COMPARE_PAN_DS_UPLOAD_PAN"),
            type=["pan", "PAN"],
            accept_multiple_files=False,
        )
    with c2:
        ds_file = st.file_uploader(
            t("COMPARE_PAN_DS_UPLOAD_DS"),
            type=["pdf", "PDF"],
            accept_multiple_files=False,
        )

    # Optional project info
    with st.expander(t("COMPARE_PAN_DS_PROJECT_EXPANDER"), expanded=True):
        set_(TOOL_ID, "project_name", st.text_input(t("COMPARE_PAN_DS_PROJECT_NAME"), value=str(get(TOOL_ID, "project_name", ""))))
        set_(TOOL_ID, "project_no", st.text_input(t("COMPARE_PAN_DS_PROJECT_NO"), value=str(get(TOOL_ID, "project_no", ""))))
        set_(TOOL_ID, "solar_engineer", st.text_input(t("COMPARE_PAN_DS_SOLAR_ENGINEER"), value=str(get(TOOL_ID, "solar_engineer", ""))))

    add_timestamp_to_outputs = st.checkbox(
        t("COMPARE_PAN_DS_TIMESTAMP_OUTPUTS"),
        value=bool(get(TOOL_ID, "add_timestamp_to_outputs", True)),
        help=t("COMPARE_PAN_DS_TIMESTAMP_HELP"),
    )
    set_(TOOL_ID, "add_timestamp_to_outputs", add_timestamp_to_outputs)


# =============================================================================
# 2) Run
# =============================================================================
with section("SECTION_RUN", icon="▶️"):
    st.markdown('<div class="pv-run">', unsafe_allow_html=True)
    run_btn = st.button(t("COMPARE_PAN_DS_RUN"), type="primary", help=t("COMPARE_PAN_DS_RUN_HELP"))
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# 3) Explanations
# =============================================================================
#with section("COMPARE_PAN_DS_ELEC_EXPLAINER_SECION", icon="📘",expanded=False):
with st.expander(t("COMPARE_PAN_DS_ELEC_EXPLAINER_TITLE"), icon="📘", expanded=False):
    st.markdown(t("COMPARE_PAN_DS_ELEC_EXPLAINER_TEXT"))
# =============================================================================
# 3) Results
# =============================================================================
with section("SECTION_RESULTS", icon="📊"):
    if run_btn:
        if pan_file is None or ds_file is None:
            st.warning(t("COMPARE_PAN_DS_NEED_FILES"))
            st.stop()

        try:
            with st.spinner(t("COMPARE_PAN_DS_RUNNING")):
                result = compare_pan_to_ds(
                    pan=pan_file.getvalue(),
                    ds=ds_file.getvalue(),
                    manufacturer_code=str(get(TOOL_ID, "manufacturer", "jinko")),
                    outputs_dir=OUTPUTS_DIR,
                    pan_source_name=pan_file.name,
                    ds_source_name=ds_file.name,
                    cleanup_tmp_files=False,
                    project_info={
                        "project_name": str(get(TOOL_ID, "project_name", "")),
                        "project_no": str(get(TOOL_ID, "project_no", "")),
                        "solar_engineer": str(get(TOOL_ID, "solar_engineer", "")),
                    },
                )
        except Exception as e:
            st.error(t("COMPARE_PAN_DS_ERROR"))
            st.exception(e)
            st.stop()

        st.success(t("COMPARE_PAN_DS_DONE"))

        # store exports immediately so Section 4 works
        exports = (result.get("exports") or {}) if isinstance(result, dict) else {}
        pdf_path = str(exports.get("pdf_path") or "")
        log_path = str(exports.get("log_path") or "")
        set_(TOOL_ID, "last_pdf", pdf_path)
        set_(TOOL_ID, "last_log", log_path)

        # -----------------------------------------------------------------
        # Warnings (global)
        # -----------------------------------------------------------------
        if result.get("warnings"):
            st.subheader(t("COMPARE_PAN_DS_WARNINGS_TITLE"))
            for w in result["warnings"]:
                st.warning(w)

        # -----------------------------------------------------------------
        # Generalities
        # -----------------------------------------------------------------
        st.subheader(t("COMPARE_PAN_DS_GENERALITIES_TITLE"), help=t("COMPARE_PAN_DS_HELP_GENERALITIES"))

        gen = result.get("generalities", {}) or {}
        st.write(
            {
                t("COMPARE_PAN_DS_GEN_DATE"): _format_analysis_date(gen.get("analysis_datetime")),
                t("COMPARE_PAN_DS_GEN_MFR"): gen.get("manufacturer_code"),
                t("COMPARE_PAN_DS_GEN_PAN_FILE"): gen.get("pan_file"),
                t("COMPARE_PAN_DS_GEN_DS_FILE"): gen.get("datasheet_file"),
                t("COMPARE_PAN_DS_GEN_PAN_MODEL"): gen.get("pan_model"),
                t("COMPARE_PAN_DS_GEN_PAN_POWER"): gen.get("pan_power_w_int"),
                t("COMPARE_PAN_DS_GEN_DS_VARIANT"): gen.get("datasheet_variant_id"),
                t("COMPARE_PAN_DS_GEN_DS_POWER"): gen.get("datasheet_power_w_int"),
            }
        )

        # -----------------------------------------------------------------
        # Comparison table
        # -----------------------------------------------------------------
        st.subheader(t("COMPARE_PAN_DS_TABLE_TITLE"), help=t("COMPARE_PAN_DS_HELP_COMPARISON"))

        comp = result.get("comparison", {}) or {}
        if not comp.get("enabled", False):
            st.info(t("COMPARE_PAN_DS_COMPARE_SKIPPED"))
            av = comp.get("available_variants") or []
            if av:
                st.caption(t("COMPARE_PAN_DS_AVAILABLE_VARIANTS"))
                st.write(av)
        else:
            df = _format_compare_rows(comp.get("rows", []) or [])
            if df.empty:
                st.info(t("COMPARE_PAN_DS_NO_ROWS"))
            else:
                # display only the wanted columns (pretty)
                rename = {
                    "parameter": t("COMPARE_PAN_DS_COL_LABEL"),
                    "unit": t("COMPARE_PAN_DS_COL_UNIT"),
                    "pan": t("COMPARE_PAN_DS_COL_PAN"),
                    "datasheet": t("COMPARE_PAN_DS_COL_DS"),
                    "deviation_pct": t("COMPARE_PAN_DS_COL_DPCT"),
                    "status": t("COMPARE_PAN_DS_COL_STATUS"),
                }
                st.dataframe(df.rename(columns=rename), width="stretch", hide_index=True)

        # -----------------------------------------------------------------
        # Graphs — IAM
        # -----------------------------------------------------------------
        st.subheader(t("COMPARE_PAN_DS_GRAPHS_TITLE"), help=t("COMPARE_PAN_DS_HELP_IAM"))

        pan_only = result.get("pan_only", {}) or {}
        iam_res = extract_iam_profile(pan_only if "standard" in pan_only else {"standard": pan_only})

        if not iam_res.available:
            st.info(t("COMPARE_PAN_DS_IAM_NOT_AVAILABLE"))
            if iam_res.warnings:
                for w in iam_res.warnings:
                    st.warning(w)
        else:
            st.caption(
                f"{t('COMPARE_PAN_DS_IAM_MODE')}: {iam_res.mode or '-'}  |  "
                f"{t('COMPARE_PAN_DS_IAM_PROFILE')}: {iam_res.profile_name or '-'}  |  "
                f"{t('COMPARE_PAN_DS_IAM_TYPE')}: {iam_res.profile_type or '-'}"
            )

            df_iam = pd.DataFrame(iam_res.points)

            # 50/50 layout
            c1, c2 = st.columns([1, 1])
            with c1:
                st.altair_chart(_iam_altair_chart(df_iam), width="stretch")
            with c2:
                st.markdown(f"**{t('COMPARE_PAN_DS_IAM_TABLE_TITLE')}**")
                st.dataframe(
                    _iam_table_df(df_iam).rename(
                        columns={
                            "angle_deg": t("COMPARE_PAN_DS_IAM_COL_ANGLE"),
                            "iam": t("COMPARE_PAN_DS_IAM_COL_IAM"),
                            "loss_pct": t("COMPARE_PAN_DS_IAM_COL_LOSS"),
                        }
                    ),
                    width="stretch",
                    height=280,
                    hide_index=True,
                )

            if iam_res.warnings:
                st.subheader(t("COMPARE_PAN_DS_IAM_WARNINGS_TITLE"))
                for w in iam_res.warnings:
                    st.warning(w)

            if iam_res.stats:
                st.subheader(t("COMPARE_PAN_DS_IAM_STATS_TITLE"))
                st.write(iam_res.stats)

        if pdf_path or log_path:
            st.caption(t("COMPARE_PAN_DS_EXPORTS_READY"))

    else:
        st.info(t("COMPARE_PAN_DS_NO_OUTPUTS_YET"))


# =============================================================================
# 4) Export (PDF + log only)
# =============================================================================
with section("SECTION_EXPORT", icon="📤"):
    st.subheader(t("COMPARE_PAN_DS_EXPORT_TITLE"), help=t("COMPARE_PAN_DS_HELP_EXPORTS"))

    pdf_s = str(get(TOOL_ID, "last_pdf", "") or "")
    log_s = str(get(TOOL_ID, "last_log", "") or "")

    if not pdf_s and not log_s:
        st.info(t("COMPARE_PAN_DS_NO_OUTPUTS_YET"))
    else:
        if pdf_s:
            _download_button_from_path(t("COMPARE_PAN_DS_DOWNLOAD_PDF"), Path(pdf_s), mime="application/pdf")
        if log_s:
            _download_button_from_path(t("COMPARE_PAN_DS_DOWNLOAD_LOG"), Path(log_s), mime="text/plain")
