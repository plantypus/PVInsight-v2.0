# app/ui/layout.py
from __future__ import annotations
import base64
from pathlib import Path
import streamlit as st

from config.config import APP_NAME, APP_VERSION, LOGO_PNG
from ui.i18n import t

def _mime_from_suffix(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return "image/svg+xml"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    if suffix == ".gif":
        return "image/gif"
    return "image/png"

def render_local_image_inline(path: Path, width: int) -> None:
    try:
        payload = path.read_bytes()
    except OSError:
        return

    b64 = base64.b64encode(payload).decode("ascii")
    mime = _mime_from_suffix(path)
    st.markdown(
        f"<img src='data:{mime};base64,{b64}' width='{int(width)}'/>",
        unsafe_allow_html=True,
    )

def sidebar_header() -> None:
    if LOGO_PNG.exists():
        render_local_image_inline(LOGO_PNG, width=72)
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
