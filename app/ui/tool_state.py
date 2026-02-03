# app/ui/tool_state.py
from __future__ import annotations
import streamlit as st
from typing import Any, Dict


def _k(tool_id: str, name: str) -> str:
    return f"tool.{tool_id}.{name}"


def init_tool_state(tool_id: str, defaults: Dict[str, Any]) -> None:
    """
    Initialise des paramètres dans session_state sous la forme:
      tool.<TOOL_ID>.<param>
    """
    for name, value in defaults.items():
        key = _k(tool_id, name)
        if key not in st.session_state:
            st.session_state[key] = value


def get(tool_id: str, name: str, default=None):
    return st.session_state.get(_k(tool_id, name), default)


def set_(tool_id: str, name: str, value) -> None:
    st.session_state[_k(tool_id, name)] = value
