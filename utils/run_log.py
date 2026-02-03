# utils/run_log.py
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

import pandas as pd


def _fmt(v: Any) -> str:
    if v is None:
        return "-"
    if isinstance(v, (pd.Timestamp,)):
        return str(v)
    return str(v)


def write_run_log(
    log_path: Path,
    tool_name: str,
    sources: List[str],
    header_info: Optional[Dict[str, str]] = None,
    units_by_col: Optional[Dict[str, str]] = None,
    time_step_minutes: Optional[int] = None,
    quality: Optional[Any] = None,   # DataQuality
    warnings: Optional[List[str]] = None,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append("=" * 70)
    lines.append(f"{tool_name} — PVInsight")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)
    lines.append("Sources:")
    for s in sources:
        lines.append(f"  - {s}")
    lines.append("")

    if time_step_minutes is not None:
        lines.append(f"Time step (min): {time_step_minutes}")
        lines.append("")

    if header_info:
        lines.append("Header info:")
        for k, v in header_info.items():
            lines.append(f"  {k}: {v}")
        lines.append("")

    if units_by_col:
        lines.append("Units by column:")
        for k, v in units_by_col.items():
            lines.append(f"  {k}: {v}")
        lines.append("")

    if quality is not None:
        lines.append("Quality summary:")
        for field in ["n_rows", "n_nan", "n_nat", "start", "end", "expected_rows", "warning"]:
            if hasattr(quality, field):
                lines.append(f"  {field}: {_fmt(getattr(quality, field))}")
        lines.append("")

    if warnings:
        lines.append("Warnings:")
        for w in warnings:
            lines.append(f"  - {w}")
        lines.append("")
    else:
        lines.append("Warnings: none")
        lines.append("")

    log_path.write_text("\n".join(lines), encoding="utf-8")
