# app/pages/XX_tool_template.py
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
import streamlit as st

from app.bootstrap import configure_page, bootstrap
from ui.tool_layout import tool_header, section
from ui.tool_state import init_tool_state, get, set_
from ui.i18n import t

# TODO: importer ton core
# from core.<domain>.<tool> import run_tool


# IMPORTANT: page_title statique (pas t())
configure_page(page_title="Tool Template", page_icon="🧩", layout="wide")

TOOL_ID = "tool_template"

paths = bootstrap(render_sidebar_ui=True)  # paths.outputs, paths.assets, ...
OUTPUTS_DIR = paths.outputs

# Defaults par outil (persistés)
init_tool_state(
    TOOL_ID,
    defaults={
        "add_timestamp_to_outputs": True,
        "last_export": "",
        "last_log": "",
        # TODO: params UI
        # "my_option": "A",
    },
)

tool_header(icon="🧩", title_key="TOOL_TEMPLATE_TITLE", desc_key="TOOL_TEMPLATE_DESC", badge="NEW")


@dataclass
class ToolResult:
    ok: bool
    message: str = ""
    df: Optional[pd.DataFrame] = None
    export_path: Optional[Path] = None
    log_path: Optional[Path] = None
    meta: Optional[dict[str, Any]] = None
    run_dir: Optional[Path] = None


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


# =============================================================================
# 1) Inputs
# =============================================================================
with section("SECTION_INPUTS", icon="🧾"):
    uploaded = st.file_uploader(
        t("TEMPLATE_UPLOAD_LABEL"),
        type=["csv", "txt"],  # TODO
        accept_multiple_files=False,
    )

    add_timestamp = st.checkbox(
        t("TEMPLATE_TIMESTAMP_OUTPUTS"),
        value=bool(get(TOOL_ID, "add_timestamp_to_outputs", True)),
    )
    set_(TOOL_ID, "add_timestamp_to_outputs", add_timestamp)

    # TODO: inputs spécifiques outil
    # my_choice = st.selectbox(...); set_(TOOL_ID, "my_choice", my_choice)


# =============================================================================
# 2) Run
# =============================================================================
with section("SECTION_RUN", icon="▶️"):
    st.markdown('<div class="pv-run">', unsafe_allow_html=True)
    run_btn = st.button(
        t("TEMPLATE_RUN"),
        type="primary",
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# 3) Results
# =============================================================================
with section("SECTION_RESULTS", icon="📊"):
    if run_btn:
        if uploaded is None:
            st.warning(t("TEMPLATE_UPLOAD_LABEL"))
        else:
            with st.spinner(t("TEMPLATE_RUNNING")):
                # -----------------------------------------------------------------
                # TODO: appeler ton core
                # result = run_tool(
                #     source=uploaded.getvalue(),
                #     source_name=uploaded.name,
                #     outputs_dir=paths.outputs,
                #     add_timestamp_to_outputs=get(TOOL_ID, "add_timestamp_to_outputs", True),
                #     ...
                # )
                # -----------------------------------------------------------------
                result = ToolResult(
                    ok=True,
                    message="TODO: replace with core call",
                    meta={"source_name": uploaded.name},
                    run_dir=paths.outputs,
                )

            if result.ok:
                st.success(t("TEMPLATE_DONE"))
            else:
                st.error(result.message or t("TEMPLATE_FAILED"))

            # Store export paths for Export section
            if result.export_path:
                set_(TOOL_ID, "last_export", str(result.export_path))
            if result.log_path:
                set_(TOOL_ID, "last_log", str(result.log_path))

            # Summary
            st.subheader(t("TEMPLATE_SUMMARY"))
            st.write(result.meta or {})

            # Outputs
            st.subheader(t("TEMPLATE_OUTPUTS"))
            if result.df is not None and not result.df.empty:
                st.dataframe(result.df, width="stretch")
            else:
                st.info(t("TEMPLATE_NO_TABLE"))

            if result.run_dir:
                st.caption(f"outputs: {result.run_dir}")

    else:
        st.info(t("TEMPLATE_NO_OUTPUTS_YET"))


# =============================================================================
# 4) Export
# =============================================================================
with section("SECTION_EXPORT", icon="📤"):
    export_s = get(TOOL_ID, "last_export", "")
    log_s = get(TOOL_ID, "last_log", "")

    if not export_s and not log_s:
        st.info(t("TEMPLATE_NO_OUTPUTS_YET"))
    else:
        if export_s:
            _download_from_path(t("TEMPLATE_DOWNLOAD_EXPORT"), Path(export_s), mime="application/octet-stream")
        if log_s:
            _download_from_path(t("TEMPLATE_DOWNLOAD_LOG"), Path(log_s), mime="text/plain")
