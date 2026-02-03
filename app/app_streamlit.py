# app/app_streamlit.py
from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

# ============================================================================
# FORCE ADD PROJECT ROOT + app/ TO PYTHONPATH (BEFORE ANY project import)
# ============================================================================
ROOT = Path(__file__).resolve().parents[1]       # project_root/
APP_DIR = ROOT / "app"                           # project_root/app

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Now imports work reliably
from app.bootstrap import configure_page, bootstrap  # noqa: E402
from config.config import HOME_PAGE, SETTINGS_PAGE, EXIT_PAGE  # noqa: E402
from config.tools_registry import TOOLS  # noqa: E402
from ui.i18n import t  # noqa: E402

# NOTE: page_title doit rester statique (pas t(...))
configure_page(page_title="PVInsight", page_icon="☀️", layout="wide")

# Global bootstrap (state + css)
bootstrap(render_sidebar_ui=False)

pages = [
    st.Page(HOME_PAGE, title=t("PAGE_HOME_TITLE"), icon="🏠"),
    st.Page(SETTINGS_PAGE, title=t("PAGE_SETTINGS_TITLE"), icon="⚙️"),
]

# Pages outils (à plat, sans groupe)
for tool in TOOLS:
    if tool.enabled:
        pages.append(
            st.Page(
                tool.page,
                title=t(tool.title_key),
                icon=tool.icon,
            )
        )

# Exit (accepté visible)
# pages.append(st.Page(EXIT_PAGE, title=t("PAGE_EXIT_TITLE"), icon="⛔"))

st.navigation(pages, position="sidebar").run()
