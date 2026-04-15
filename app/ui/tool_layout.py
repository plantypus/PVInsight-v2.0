# app/ui/tool_layout.py
from __future__ import annotations
import streamlit as st
from ui.i18n import t
from config.tools_registry import get_tool


def tool_header(icon: str, title_key: str, desc_key: str, badge: str | None = None) -> None:
    title = f"{icon} {t(title_key)}".strip()
    if badge:
        title += f" - {badge}"

    st.markdown(f"<div class='pv-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='pv-subtitle'>{t(desc_key)}</div>", unsafe_allow_html=True)
    st.divider()


def tool_header_from_registry(tool_id: str) -> None:
    tool = get_tool(tool_id)
    tool_header(
        icon=tool.icon,
        title_key=tool.title_key,
        desc_key=tool.desc_key,
        badge=tool.badge,
    )


def section(title_key: str, icon: str = ""):
    label = f"{icon} {t(title_key)}".strip() if icon else t(title_key)
    return st.expander(label, expanded=True)
