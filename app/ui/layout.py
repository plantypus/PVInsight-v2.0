# app/ui/layout.py
from __future__ import annotations
import streamlit as st

from config.config import APP_NAME, APP_VERSION, LOGO_PNG
from ui.i18n import t

def sidebar_header() -> None:
    if LOGO_PNG.exists():
        st.image(str(LOGO_PNG), width=72)
    st.markdown(f"**{APP_NAME}**")
    st.caption(f"v{APP_VERSION}")

def sidebar_language_picker() -> None:
    lang_map = {"fr": t("LANG_FR"), "en": t("LANG_EN")}
    current = st.session_state.get("lang", "fr")

    # clé stable pour le widget
    choice = st.selectbox(
        t("LANG_LABEL"),
        options=["fr", "en"],
        format_func=lambda x: lang_map.get(x, x),
        index=0 if current == "fr" else 1,
        key="ui.lang_picker",
    )

    # si changement => update + rerun immédiat
    if choice != current:
        st.session_state["lang"] = choice
        st.rerun()

def sidebar_bottom_actions() -> None:
    st.divider()

    # Bouton Home (inline, pas de on_click)
    if st.button(t("BTN_GO_HOME"), use_container_width=True):
        st.switch_page("pages/00_home.py")

    # # Bouton Exit (inline, pas de on_click)
    # if st.button(t("BTN_EXIT"), use_container_width=True):
    #     st.switch_page("pages/99_exit.py")
