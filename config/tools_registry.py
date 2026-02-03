# config/tools_registry.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    page: str              # path relative to app/ (Streamlit expects pages/...)
    icon: str
    title_key: str         # i18n key
    desc_key: str          # i18n key
    enabled: bool = True
    badge: Optional[str] = None


TOOLS: List[ToolSpec] = [
    ToolSpec(
        tool_id="tmy_analysis",
        page="pages/10_TMY_analysis.py",
        icon="🌤️",
        title_key="TOOL_TMY_ANALYSIS_TITLE",
        desc_key="TOOL_TMY_ANALYSIS_DESC",
        enabled=True,
        badge="NEW",
    ),
    ToolSpec(
        tool_id="tmy_compare",
        page="pages/20_TMY_compare.py",
        icon="⚖️",
        title_key="TOOL_TMY_COMPARE_TITLE",
        desc_key="TOOL_TMY_COMPARE_DESC",
        enabled=True,
        badge="NEW",
    ),
    ToolSpec(
        tool_id="hourly_results_analysis",
        page="pages/30_hourly_results_analysis.py",
        icon="📈",
        title_key="TOOL_HOURLY_RESULTS_TITLE",
        desc_key="TOOL_HOURLY_RESULTS_DESC",
        enabled=True,
        badge="NEW",
    ),
]

