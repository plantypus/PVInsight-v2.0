# utils/paths.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    figures_dir: Path
    reports_dir: Path
    logs_dir: Path


def _safe_slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-_.]+", "_", s)
    return s[:80].strip("_")


def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def make_run_folders(outputs_dir: Path, tool_name: str, mode: str = "flat") -> RunPaths:
    """
    mode:
      - "flat": outputs/ (pas de runs/ ni latest/)
    """
    ensure_dir(outputs_dir)

    # Tout va directement dans outputs/
    run_dir = ensure_dir(outputs_dir)

    figures_dir = ensure_dir(run_dir / "figures")
    reports_dir = ensure_dir(run_dir / "reports")
    logs_dir = ensure_dir(run_dir / "logs")

    return RunPaths(run_dir=run_dir, figures_dir=figures_dir, reports_dir=reports_dir, logs_dir=logs_dir)
