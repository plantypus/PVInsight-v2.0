# app/bootstrap.py
from __future__ import annotations

from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Optional

import streamlit as st

# UI (global)
from ui.state import init_state
from ui.theme import inject_css
from ui.layout import sidebar_header, sidebar_language_picker, sidebar_bottom_actions


# =============================================================================
# Paths (single source of truth)
# =============================================================================
ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs"
ASSETS_DIR = ROOT / "assets"


@dataclass(frozen=True)
class AppPaths:
    root: Path
    outputs: Path
    assets: Path


def ensure_root_importable() -> None:
    """
    Ensure project root and app/ are importable regardless of how Streamlit is launched.
    """
    app_dir = ROOT / "app"

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    # ✅ nécessaire pour pouvoir faire: from ui.state import ...
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))


def get_paths() -> AppPaths:
    return AppPaths(root=ROOT, outputs=OUTPUTS_DIR, assets=ASSETS_DIR)


def configure_page(*, page_title: str, page_icon: str, layout: str = "wide") -> None:
    """
    Wrapper to enforce Streamlit caveat: page_title must remain static (no t()).
    """
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)


def render_sidebar() -> None:
    """
    Standard PVInsight sidebar.
    """
    with st.sidebar:
        sidebar_header()
        st.divider()
        sidebar_language_picker()
        sidebar_bottom_actions()


def bootstrap(*, render_sidebar_ui: bool = False) -> AppPaths:
    """
    Global app bootstrap:
    - root import
    - init state
    - inject css
    - standard sidebar
    Returns paths object for uniform outputs/assets usage.
    """
    ensure_root_importable()

    # Global state & theme
    init_state()
    inject_css()

    # Standard sidebar
    if render_sidebar_ui:
        render_sidebar()

    # Ensure outputs exists (safe)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    return get_paths()
