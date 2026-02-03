# pages/99_exit.py
from __future__ import annotations

import streamlit as st
from ui.state import init_state
from ui.i18n import t

st.set_page_config(page_title="Exit", page_icon="⛔", layout="wide")
init_state()

# hide sidebar + top header for this page
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 2rem; max-width: 900px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(f"⛔ {t('EXIT_TITLE')}")

st.write(t("EXIT_TEXT"))
st.success(t("EXIT_CLOSE_TAB"))
st.caption(t("EXIT_CLOUD_NOTE"))

if st.button("🏠 " + t("PAGE_HOME_TITLE"), use_container_width=True):
    st.switch_page("pages/00_home.py")
