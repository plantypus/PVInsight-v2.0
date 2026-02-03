# app/ui/state.py
from __future__ import annotations
import streamlit as st

DEFAULTS = {
    "lang": "fr",  # "fr" or "en"
}

def init_state() -> None:
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_to_defaults() -> None:
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
