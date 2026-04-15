# config/config.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# =============================================================================
# Paths
# =============================================================================
ROOT_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT_DIR / "assets"
I18N_DIR = ASSETS_DIR / "i18n"
LOGO_PNG = ASSETS_DIR / "logo.png"
LOGO_ICO = ASSETS_DIR / "logo.ico"


# =============================================================================
# App identity
# =============================================================================
APP_NAME = "PVInsight - PV Data Analyzer"
APP_VERSION = "2.5"


# =============================================================================
# Pages (file paths used by st.navigation + st.switch_page)
# =============================================================================
HOME_PAGE = "pages/00_home.py"
SETTINGS_PAGE = "pages/01_settings.py"
EXIT_PAGE = "pages/99_exit.py"

# PVSyst "Hourly results" typical format (may be overridden by the reader's fallback)
PVSYST_DATE_FMT = "%d/%m/%Y %H:%M"

# Outputs structure under app/bootstrap.py paths.outputs
REPORTS_SUBDIR = "reports"
FIGURES_SUBDIR = "figures"
LOGS_SUBDIR = "logs"


# =============================================================================
# Tools registry (HOME buttons + descriptions)
# =============================================================================
@dataclass(frozen=True)
class ToolCard:
    key: str
    page: str                  # file path of the target page
    icon: str
    title_key: str             # i18n key
    desc_key: str              # i18n key
    enabled: bool = True
    badge: Optional[str] = None
