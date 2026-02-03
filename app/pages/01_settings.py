# app/pages/01_⚙️_Réglages.py
from __future__ import annotations

import streamlit as st

from app.bootstrap import configure_page, bootstrap
from ui.state import reset_to_defaults
from ui.i18n import t


# NOTE: page_title doit rester statique (pas t(...))
configure_page(page_title="Settings", page_icon="⚙️", layout="wide")

# Global bootstrap (state + css) + paths
bootstrap(render_sidebar_ui=False)

st.markdown(f"<div class='pv-title'>⚙️ {t('SETTINGS_TITLE')}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='pv-subtitle'>{t('SETTINGS_SUBTITLE')}</div>", unsafe_allow_html=True)

st.subheader(t("SETTINGS_SECTION_UI"))

# Tu ajouteras ici les paramètres utilisateurs (unités, chemins, options d’analyse, etc.)

col1, col2 = st.columns([1, 3])
with col1:
    if st.button(t("SETTINGS_RESET"), width="stretch"):
        reset_to_defaults()
        st.success(t("SETTINGS_RESET_DONE"))
