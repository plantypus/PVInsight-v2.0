# app/ui/tool_layout.py
from __future__ import annotations
import streamlit as st
from ui.i18n import t


def tool_header(icon: str, title_key: str, desc_key: str, badge: str | None = None) -> None:
    title = f"{icon} {t(title_key)}"
    if badge:
        title += f" · {badge}"

    st.markdown(f"<div class='pv-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='pv-subtitle'>{t(desc_key)}</div>", unsafe_allow_html=True)
    st.divider()


def section(title_key: str, icon: str = ""):
    label = f"{icon} {t(title_key)}" if icon else t(title_key)
    return st.expander(label, expanded=True)
