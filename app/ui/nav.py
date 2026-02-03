# app/ui/nav.py  (ou ui/nav.py si tu importes sans "app.")
from __future__ import annotations
import streamlit as st
from config.config import HOME_PAGE, SETTINGS_PAGE, EXIT_PAGE

def switch_page_safe(page_path: str) -> None:
    try:
        st.switch_page(page_path)
    except Exception as e:
        st.error(f"Navigation impossible vers: {page_path}\n{e}")

def go_home() -> None:
    switch_page_safe(HOME_PAGE)

def go_settings() -> None:
    switch_page_safe(SETTINGS_PAGE)

def go_exit() -> None:
    switch_page_safe(EXIT_PAGE)
