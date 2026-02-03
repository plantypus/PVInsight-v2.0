# utils/formatting.py
from __future__ import annotations

import math
from typing import Optional


def _to_float(x) -> Optional[float]:
    try:
        v = float(x)
    except Exception:
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def format_number(x, ndigits: int = 0, empty: str = "—") -> str:
    """
    Format with space thousand separators.
    - ndigits=0 -> "12 345"
    - ndigits>0 -> "12 345.6"
    """
    v = _to_float(x)
    if v is None:
        return empty

    if ndigits <= 0:
        return f"{v:,.0f}".replace(",", " ")
    return f"{v:,.{ndigits}f}".replace(",", " ")


def format_with_unit(x, unit: str = "", ndigits: int = 0, empty: str = "—") -> str:
    """
    Format a number and append a unit (no conversion).
    """
    s = format_number(x, ndigits=ndigits, empty=empty)
    u = (unit or "").strip()
    return f"{s} {u}" if (u and s != empty) else s
