# app/pages/00_home.py
from __future__ import annotations

import streamlit as st

from app.bootstrap import configure_page, bootstrap
from config.config import APP_NAME, APP_VERSION, LOGO_PNG
from config.tools_registry import TOOLS
from ui.i18n import t


# page_title should stay static (not translated) for Streamlit config behavior.
configure_page(page_title="Home", page_icon="🏠", layout="wide")

# Global bootstrap (state + css) + paths
paths = bootstrap(render_sidebar_ui=True)

# Header
cols = st.columns([1, 4])
with cols[0]:
    logo = LOGO_PNG
    if not logo.exists():
        cand = paths.assets / "logo.png"
        if cand.exists():
            logo = cand

    if logo.exists():
        st.image(str(logo), width=110)

with cols[1]:
    st.markdown(f"<div class='pv-title'>{t('APP_TITLE')}</div>", unsafe_allow_html=True)
    st.caption(f"{APP_NAME} - v{APP_VERSION}")
    st.markdown(f"<div class='pv-subtitle'>{t('APP_DESCRIPTION')}</div>", unsafe_allow_html=True)

st.divider()

# Tools
st.subheader(t("HOME_TOOLS_TITLE"))

enabled = [x for x in TOOLS if x.enabled]
if not enabled:
    st.info(t("HOME_TOOLS_EMPTY"))
else:
    for tool in enabled:
        c1, c2 = st.columns([1, 3], vertical_alignment="center")
        with c1:
            label = f"{tool.icon} {t(tool.title_key)}".strip()
            if tool.badge:
                label += f" - {tool.badge}"

            if st.button(label, width="stretch", key=f"home_{tool.tool_id}"):
                st.switch_page(tool.page)

        with c2:
            st.write(t(tool.desc_key))
