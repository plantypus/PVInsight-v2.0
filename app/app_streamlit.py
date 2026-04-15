# app/app_streamlit.py
from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

# Force add project root + app/ to PYTHONPATH before any project import.
ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app.bootstrap import configure_page, bootstrap  # noqa: E402
from config.config import HOME_PAGE  # noqa: E402
from config.tools_registry import TOOLS  # noqa: E402
from ui.i18n import t  # noqa: E402

# page_title must stay static (not translated) for Streamlit page config behavior.
configure_page(page_title="PVInsight", page_icon="*", layout="wide")

# Global bootstrap (state + css).
bootstrap(render_sidebar_ui=False)

pages = [
    st.Page(HOME_PAGE, title=t("PAGE_HOME_TITLE")),
]

# Tool pages (flat, no groups)
for tool in TOOLS:
    if tool.enabled:
        pages.append(
            st.Page(
                tool.page,
                title=t(tool.title_key),
            )
        )

st.navigation(pages, position="sidebar").run()
