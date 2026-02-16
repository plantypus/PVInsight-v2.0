# core/module/iam_plot.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import math


# =============================================================================
# IAM PLOT PREP — PVInsight 2.0
#
# Purpose
# - Extract and validate IAM profile points from PAN standardized output:
#     pan_data["standard"]["iam"]  (as produced by utils/readers/reader_pan_file.py)
# - Return a plot-ready dataset (angles + IAM + loss %) and useful diagnostics
#
# Input expected (PAN reader):
# standard["iam"] = {
#   "mode": "...",
#   "profile_type": "...",
#   "profile": {
#       "name": "TCubicProfile",
#       "meta": {...},
#       "points": [{"angle_deg": 0.0, "iam": 1.0}, ...]
#   }
# }
#
# Notes
# - This module DOES NOT decide UI layout; it only returns structured data + diagnostics.
# - Streamlit can plot via Altair or Matplotlib using returned series.
# =============================================================================


@dataclass(frozen=True)
class IAMPlotResult:
    available: bool
    mode: Optional[str]
    profile_type: Optional[str]
    profile_name: Optional[str]
    points: List[Dict[str, float]]          # each: {"angle_deg": float, "iam": float, "loss_pct": float}
    warnings: List[str]
    stats: Dict[str, Any]                   # min/max, monotonic flags, etc.


def _safe_get(d: Dict[str, Any], path: List[str]) -> Any:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        s = str(x).strip().replace(",", ".")
        return float(s)
    except Exception:
        return None


def _sorted_unique_points(raw_points: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
    """
    Keep only valid (angle_deg, iam) pairs, cast to float,
    sort by angle, and keep last value if duplicate angles exist.
    """
    tmp: List[Tuple[float, float]] = []
    for p in raw_points:
        if not isinstance(p, dict):
            continue
        a = _as_float(p.get("angle_deg"))
        f = _as_float(p.get("iam"))
        if a is None or f is None:
            continue
        tmp.append((float(a), float(f)))

    tmp.sort(key=lambda t: t[0])

    # de-dup by angle (keep last)
    out: List[Tuple[float, float]] = []
    for a, f in tmp:
        if out and abs(out[-1][0] - a) < 1e-9:
            out[-1] = (a, f)
        else:
            out.append((a, f))
    return out


def _is_monotone_nonincreasing(vals: List[float], tol: float = 1e-9) -> bool:
    return all(vals[i] <= vals[i - 1] + tol for i in range(1, len(vals)))


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def extract_iam_profile(pan_data: Dict[str, Any]) -> IAMPlotResult:
    """
    Extract IAM curve from PAN reader output.

    Accepts either:
    - the full object returned by read_pan_file(...) (has "standard")
    - or directly a dict containing "standard" already
    """
    warnings: List[str] = []

    std = pan_data.get("standard") if isinstance(pan_data, dict) else None
    if not isinstance(std, dict):
        # maybe user passed already standard dict
        std = pan_data if isinstance(pan_data, dict) else None

    if not isinstance(std, dict):
        return IAMPlotResult(
            available=False,
            mode=None,
            profile_type=None,
            profile_name=None,
            points=[],
            warnings=["PAN data does not contain a 'standard' dict."],
            stats={},
        )

    iam = _safe_get(std, ["iam"])
    if not isinstance(iam, dict):
        return IAMPlotResult(
            available=False,
            mode=None,
            profile_type=None,
            profile_name=None,
            points=[],
            warnings=["No IAM block found in PAN standard output."],
            stats={},
        )

    mode = str(iam.get("mode") or "") or None
    profile_type = str(iam.get("profile_type") or "") or None

    prof = iam.get("profile")
    if not isinstance(prof, dict):
        return IAMPlotResult(
            available=False,
            mode=mode,
            profile_type=profile_type,
            profile_name=None,
            points=[],
            warnings=["IAM profile is missing or not a dict (iam.profile)."],
            stats={},
        )

    profile_name = str(prof.get("name") or "") or None
    raw_points = prof.get("points") or []
    if not isinstance(raw_points, list) or not raw_points:
        return IAMPlotResult(
            available=False,
            mode=mode,
            profile_type=profile_type,
            profile_name=profile_name,
            points=[],
            warnings=["IAM profile has no points (iam.profile.points)."],
            stats={},
        )

    pts = _sorted_unique_points(raw_points)

    if len(pts) < 2:
        warnings.append("IAM profile has fewer than 2 valid points; plot may be uninformative.")

    # Diagnostics
    angles = [a for a, _ in pts]
    factors = [f for _, f in pts]

    # Basic sanity checks
    if any(math.isnan(a) or math.isinf(a) for a in angles):
        warnings.append("IAM angles contain NaN/Inf.")
    if any(math.isnan(f) or math.isinf(f) for f in factors):
        warnings.append("IAM factors contain NaN/Inf.")

    # Range checks (soft warnings)
    if angles and (min(angles) < -1e-6 or max(angles) > 95.0):
        warnings.append("IAM angle range looks unusual (expected roughly 0..90°).")
    if factors and (min(factors) < -0.05 or max(factors) > 1.05):
        warnings.append("IAM factors outside expected range (roughly 0..1). Check PAN profile.")

    # Monotonic expected behavior: IAM usually non-increasing with angle
    mono = _is_monotone_nonincreasing(factors, tol=1e-6)
    if not mono and len(factors) >= 4:
        warnings.append("IAM is not monotone decreasing with angle; verify profile.")

    # Prepare plot-ready points
    out_points: List[Dict[str, float]] = []
    for a, f in pts:
        # loss_pct is performance loss due to IAM at that incidence angle
        loss_pct = (1.0 - f) * 100.0
        out_points.append(
            {
                "angle_deg": float(a),
                "iam": float(f),
                "loss_pct": float(loss_pct),
            }
        )

    stats: Dict[str, Any] = {
        "n_points": len(out_points),
        "angle_min_deg": float(min(angles)) if angles else None,
        "angle_max_deg": float(max(angles)) if angles else None,
        "iam_min": float(min(factors)) if factors else None,
        "iam_max": float(max(factors)) if factors else None,
        "monotone_decreasing": bool(mono),
    }

    # Typical expectation: IAM(0°) ~ 1 and IAM(90°) ~ 0 (not mandatory but informative)
    if angles:
        if abs(angles[0] - 0.0) > 1e-6:
            warnings.append("IAM does not start at 0°. Consider adding a 0° point for stability.")
        if abs(angles[-1] - 90.0) > 1e-6:
            warnings.append("IAM does not end at 90°. Consider adding a 90° point for stability.")

    return IAMPlotResult(
        available=True,
        mode=mode,
        profile_type=profile_type,
        profile_name=profile_name,
        points=out_points,
        warnings=warnings,
        stats=stats,
    )


def iam_points_as_xy(result: IAMPlotResult) -> Tuple[List[float], List[float]]:
    """
    Convenience: return x=angles, y=iam (for any plotting backend).
    """
    xs = [p["angle_deg"] for p in result.points]
    ys = [p["iam"] for p in result.points]
    return xs, ys


def iam_loss_as_xy(result: IAMPlotResult) -> Tuple[List[float], List[float]]:
    """
    Convenience: return x=angles, y=loss_pct (performance loss vs incidence angle).
    """
    xs = [p["angle_deg"] for p in result.points]
    ys = [p["loss_pct"] for p in result.points]
    return xs, ys


def interpolate_iam_linear(result: IAMPlotResult, *, angles_deg: List[float], clamp_0_1: bool = True) -> List[Optional[float]]:
    """
    Lightweight linear interpolation of IAM factor for requested angles.
    - Returns list aligned with angles_deg (None if not computable).
    - If clamp_0_1: clamp interpolated IAM to [0, 1].
    """
    if not result.available or len(result.points) < 2:
        return [None for _ in angles_deg]

    xs, ys = iam_points_as_xy(result)
    # Ensure sorted by angle
    pairs = sorted(zip(xs, ys), key=lambda t: t[0])
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]

    out: List[Optional[float]] = []
    for a in angles_deg:
        aa = _as_float(a)
        if aa is None:
            out.append(None)
            continue
        x = float(aa)

        # outside range -> edge value
        if x <= xs[0]:
            y = ys[0]
            out.append(_clamp(y, 0.0, 1.0) if clamp_0_1 else y)
            continue
        if x >= xs[-1]:
            y = ys[-1]
            out.append(_clamp(y, 0.0, 1.0) if clamp_0_1 else y)
            continue

        # find interval
        j = 1
        while j < len(xs) and xs[j] < x:
            j += 1
        x0, x1 = xs[j - 1], xs[j]
        y0, y1 = ys[j - 1], ys[j]
        if abs(x1 - x0) < 1e-12:
            y = y1
        else:
            t = (x - x0) / (x1 - x0)
            y = y0 + t * (y1 - y0)

        out.append(_clamp(y, 0.0, 1.0) if clamp_0_1 else y)

    return out


def iam_png_from_result(result: Dict[str, Any], *, title: str = "IAM") -> Optional[bytes]:
    """
    Returns a PNG (bytes) of IAM curve using Matplotlib, or None if IAM is missing.
    Expects IAM points under: result["pan_only"]["standard"]["iam"]["profile"]["points"]
    points: [{"angle_deg": float, "iam": float}, ...]
    """
    # Lazy import (avoid matplotlib dependency for other tools)
    import matplotlib.pyplot as plt

    # Extract points
    pan_only = result.get("pan_only") or {}
    std = (pan_only.get("standard") or {}) if isinstance(pan_only, dict) else {}
    iam = std.get("iam") or {}
    prof = iam.get("profile") or {}
    pts = prof.get("points") or []

    if not isinstance(pts, list) or not pts:
        return None

    x: List[float] = []
    y: List[float] = []
    for p in pts:
        if not isinstance(p, dict):
            continue
        a = p.get("angle_deg")
        f = p.get("iam")
        if isinstance(a, (int, float)) and isinstance(f, (int, float)):
            x.append(float(a))
            y.append(float(f))

    if len(x) < 2:
        return None

    # Plot
    fig = plt.figure(figsize=(5.2, 2.2), dpi=200)  # ~1/3 page wide, low height
    ax = fig.add_axes([0.12, 0.22, 0.83, 0.70])     # manual margins for labels/title

    ax.plot(x, y, linewidth=1.5)
    ax.scatter(x, y, s=8)  # smaller points

    ax.set_title(title, fontsize=9)
    ax.set_xlabel("Incidence angle (°)", fontsize=8)
    ax.set_ylabel("IAM (-)", fontsize=8)

    # Horizontal grid only
    ax.grid(True, axis="y", linewidth=0.5)
    ax.grid(False, axis="x")

    ax.tick_params(axis="both", labelsize=8)

    # Export to PNG bytes
    buf = BytesIO()
    fig.savefig(buf, format="png", transparent=False, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
