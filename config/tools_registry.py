# config/tools_registry.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    page: str
    icon: str
    title_key: str
    desc_key: str
    enabled: bool = True
    badge: Optional[str] = None


TOOLS: List[ToolSpec] = [
    ToolSpec(
        tool_id="tmy_analysis",
        page="pages/10_TMY_analysis.py",
        icon="TMY",
        title_key="TOOL_TMY_ANALYSIS_TITLE",
        desc_key="TOOL_TMY_ANALYSIS_DESC",
        enabled=True,
        badge="",
    ),
    ToolSpec(
        tool_id="tmy_compare",
        page="pages/20_TMY_compare.py",
        icon="CMP",
        title_key="TOOL_TMY_COMPARE_TITLE",
        desc_key="TOOL_TMY_COMPARE_DESC",
        enabled=True,
        badge="",
    ),
    ToolSpec(
        tool_id="hourly_results_analysis",
        page="pages/30_hourly_results_analysis.py",
        icon="HR",
        title_key="TOOL_HOURLY_RESULTS_TITLE",
        desc_key="TOOL_HOURLY_RESULTS_DESC",
        enabled=True,
        badge="",
    ),
    ToolSpec(
        tool_id="compare_pan_to_ds",
        page="pages/40_compare_pan_to_ds.py",
        icon="PAN",
        title_key="COMPARE_PAN_DS_TITLE",
        desc_key="COMPARE_PAN_DS_DESC",
        enabled=True,
        badge="",
    ),
    ToolSpec(
        tool_id="market_analysis",
        page="pages/50_market_analysis.py",
        icon="MKT",
        title_key="MARKET_ANALYSIS_TITLE",
        desc_key="MARKET_ANALYSIS_DESC",
        enabled=True,
        badge="",
    ),
]
