# utils/columns.py
from __future__ import annotations

from typing import Dict, List, Tuple
import difflib


def check_required_columns(columns: List[str], required: List[str]) -> Tuple[bool, List[str]]:
    missing = [c for c in required if c not in columns]
    return (len(missing) == 0), missing


def suggest_similar_columns(
    columns: List[str],
    missing: List[str],
    cutoff: float = 0.6,
) -> Dict[str, List[str]]:
    suggestions: Dict[str, List[str]] = {}
    for m in missing:
        suggestions[m] = difflib.get_close_matches(m, columns, n=3, cutoff=cutoff)
    return suggestions
