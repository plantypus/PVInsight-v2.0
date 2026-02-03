# app/ui/i18n.py
from __future__ import annotations
import streamlit as st

from assets.i18n.fr import TEXTS as FR
from assets.i18n.en import TEXTS as EN

def t(key: str) -> str:
    lang = st.session_state.get("lang", "fr")
    bundle = FR if lang == "fr" else EN
    return bundle.get(key, f"[{key}]")
