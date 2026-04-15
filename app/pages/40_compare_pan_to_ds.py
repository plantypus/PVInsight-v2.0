# app/pages/40_compare_pan_to_ds.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import tempfile

import altair as alt
import pandas as pd
import streamlit as st

from app.bootstrap import configure_page, bootstrap
from config.tools_registry import get_tool_icon
from ui.tool_layout import tool_header_from_registry, section
from ui.tool_state import init_tool_state, get, set_
from ui.i18n import t

from core.module.compare_pan_to_ds import compare_pan_to_ds
from core.module.iam_plot import extract_iam_profile

TOOL_ID = "compare_pan_to_ds"

# NOTE: page_title should stay static (not translated) for Streamlit config behavior.
configure_page(page_title="Compare PAN vs Datasheet", page_icon=get_tool_icon(TOOL_ID, "🧾"), layout="wide")

paths = bootstrap(render_sidebar_ui=True)


init_tool_state(
    TOOL_ID,
    defaults={
        "manufacturer": "dmegc",
        "last_pdf_bytes": b"",
        "last_log_bytes": b"",
    },
)

tool_header_from_registry(TOOL_ID)


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
def _download_button_from_bytes(label: str, data: bytes, file_name: str, mime: str) -> None:
    if not data:
        st.info(t("COMPARE_PAN_DS_NO_OUTPUTS_YET"))
        return
    st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime=mime,
        width="stretch",
    )


def _fmt_number(x, *, decimals: int = 3) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "-"
    try:
        v = float(x)
    except Exception:
        s = str(x).strip()
    return s if s else "-"

    # 1000-sep with narrow no-break space (French-friendly)
    s = f"{v:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", "\u202f")  # 12 345,678
    # trim trailing zeros nicely
    if decimals > 0:
        s = s.rstrip("0").rstrip(",")
    return s


def _fmt_unit_value(x, unit: str) -> str:
    if unit in ("W/m2", "V", "A", "W", "mm", "Ohm"):
        # numeric formats
        dec = 0 if unit in ("W", "mm", "Ohm") else 3
        return _fmt_number(x, decimals=dec)
    if unit in ("%/degC",):
        return _fmt_number(x, decimals=3)
    if unit in ("mA/degC", "mV/degC"):
        return _fmt_number(x, decimals=2)
    # fallback
    return str(x) if x is not None else "-"


def _fmt_pct(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "-"
    try:
        v = float(x)
    except Exception:
        return "-"
    # percent display with 1-2 decimals
    s = _fmt_number(v, decimals=2)
    return f"{s} %"


def _fmt_status(s: str) -> str:
    s = str(s or "").upper().strip()
    if s == "OK":
        return "OK"
    if s == "WARN":
        return "WARN"
    return "-"


def _format_analysis_date(iso_dt: str | None) -> str:
    if not iso_dt:
        return "-"
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
with section("SECTION_INPUTS"):
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

# =============================================================================
# 2) Run
# =============================================================================
with section("SECTION_RUN"):
    st.markdown('<div class="pv-run">', unsafe_allow_html=True)
    run_btn = st.button(t("COMPARE_PAN_DS_RUN"), type="primary", help=t("COMPARE_PAN_DS_RUN_HELP"))
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# 3) Explanations
# =============================================================================
# with section("COMPARE_PAN_DS_ELEC_EXPLAINER_SECION", expanded=False):
with st.expander(t("COMPARE_PAN_DS_ELEC_EXPLAINER_TITLE"), expanded=False):
    st.markdown(t("COMPARE_PAN_DS_ELEC_EXPLAINER_TEXT"))
# =============================================================================
# 3) Results
# =============================================================================
with section("SECTION_RESULTS"):
    if run_btn:
        if pan_file is None or ds_file is None:
            st.warning(t("COMPARE_PAN_DS_NEED_FILES"))
            st.stop()

        try:
            with st.spinner(t("COMPARE_PAN_DS_RUNNING")):
                with tempfile.TemporaryDirectory(prefix="pvinsight_pan_ds_") as tmpdir:
                    result = compare_pan_to_ds(
                        pan=pan_file.getvalue(),
                        ds=ds_file.getvalue(),
                        manufacturer_code=str(get(TOOL_ID, "manufacturer", "jinko")),
                        outputs_dir=Path(tmpdir),
                        pan_source_name="module.pan",
                        ds_source_name="datasheet.pdf",
                        cleanup_tmp_files=True,
                    )
                    exports = (result.get("exports") or {}) if isinstance(result, dict) else {}
                    pdf_path = Path(str(exports.get("pdf_path") or ""))
                    log_path = Path(str(exports.get("log_path") or ""))
                    pdf_bytes = pdf_path.read_bytes() if pdf_path.exists() else b""
                    log_bytes = log_path.read_bytes() if log_path.exists() else b""
        except Exception as e:
            st.error(t("COMPARE_PAN_DS_ERROR"))
            st.error(str(e))
            st.stop()

        st.success(t("COMPARE_PAN_DS_DONE"))

        # store exports in memory only
        set_(TOOL_ID, "last_pdf_bytes", pdf_bytes)
        set_(TOOL_ID, "last_log_bytes", log_bytes)

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
        # Graphs - IAM
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

        if pdf_bytes or log_bytes:
            st.caption(t("COMPARE_PAN_DS_EXPORTS_READY"))

    else:
        st.info(t("COMPARE_PAN_DS_NO_OUTPUTS_YET"))


# =============================================================================
# 4) Export (PDF + log only)
# =============================================================================
with section("SECTION_EXPORT"):
    st.subheader(t("COMPARE_PAN_DS_EXPORT_TITLE"), help=t("COMPARE_PAN_DS_HELP_EXPORTS"))

    pdf_b = get(TOOL_ID, "last_pdf_bytes", b"") or b""
    log_b = get(TOOL_ID, "last_log_bytes", b"") or b""

    if not pdf_b and not log_b:
        st.info(t("COMPARE_PAN_DS_NO_OUTPUTS_YET"))
    else:
        if pdf_b:
            _download_button_from_bytes(
                t("COMPARE_PAN_DS_DOWNLOAD_PDF"),
                pdf_b,
                file_name="pan_vs_datasheet_report.pdf",
                mime="application/pdf",
            )
        if log_b:
            _download_button_from_bytes(
                t("COMPARE_PAN_DS_DOWNLOAD_LOG"),
                log_b,
                file_name="pan_vs_datasheet_log.txt",
                mime="text/plain",
            )

