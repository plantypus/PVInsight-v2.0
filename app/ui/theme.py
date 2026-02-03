# app/ui/theme.py
from __future__ import annotations
import streamlit as st

def inject_css() -> None:
    st.markdown(
        """
        <style>
        .pv-title { font-size: 2.0rem; font-weight: 700; margin-bottom: 0.25rem; }
        .pv-subtitle { font-size: 1.0rem; opacity: 0.85; margin-bottom: 1rem; }
        .tool-row { padding: 0.25rem 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )
