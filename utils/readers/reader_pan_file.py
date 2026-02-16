# utils/readers/reader_pan_file.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import re

# =============================================================================
# PVsyst .PAN reader (PVInsight 2.0) — corrected + simplified
#
# Goals
# - Lossless parsing into a hierarchical RAW dict
# - Standardized dict for downstream modules (module / electrical / iam)
# - Robust to PVsyst variants:
#     * "PVObject_=pvModule" (empty type)
#     * module electrical keys at root level (outside pvModule node)
#     * profile sub-blocks like IAMProfile=TCubicProfile ... End of TCubicProfile
# =============================================================================

Source = Union[str, Path, bytes]

_NUM_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")


# -----------------------------------------------------------------------------
# IO / decoding
# -----------------------------------------------------------------------------

def _decode_source(source: Source) -> Tuple[str, str]:
    if isinstance(source, bytes):
        for enc in ("utf-8", "cp1252", "latin-1"):
            try:
                return source.decode(enc), "<bytes>"
            except Exception:
                pass
        return source.decode("latin-1", errors="replace"), "<bytes>"

    p = source if isinstance(source, Path) else Path(str(source))
    data = p.read_bytes()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(enc), p.name
        except Exception:
            pass
    return data.decode("latin-1", errors="replace"), p.name


# -----------------------------------------------------------------------------
# Conversions
# -----------------------------------------------------------------------------

def _to_number_if_possible(x: Any) -> Any:
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return ""
    # PVsyst uses "$B18D" etc. -> keep
    if s.startswith("$"):
        return s
    # date-like -> keep
    if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}", s):
        return s
    if _NUM_RE.match(s):
        # int if possible
        if "." not in s and "e" not in s.lower():
            try:
                return int(s)
            except Exception:
                pass
        try:
            return float(s)
        except Exception:
            return s
    return s


def _g(primary: Dict[str, Any], fallback: Dict[str, Any], key: str) -> Any:
    """
    Read key from primary dict, else from fallback dict; returns typed (int/float/str).
    """
    if isinstance(primary, dict) and key in primary:
        return _to_number_if_possible(primary.get(key))
    if isinstance(fallback, dict) and key in fallback:
        return _to_number_if_possible(fallback.get(key))
    return None


# -----------------------------------------------------------------------------
# RAW parser (lossless-ish)
# -----------------------------------------------------------------------------

def _parse_pan_text(text: str) -> Dict[str, Any]:
    raw: Dict[str, Any] = {
        "format": "pvsyst_pan",
        "lines": text.splitlines(),
        "tree": {},
        "unknown_lines": [],
    }

    # Accept both PVObject_=pvModule and PVObject_Commercial=pvCommercial
    re_pvobject_begin = re.compile(r"^\s*PVObject_(\w*)\s*=\s*(\w+)\s*$")
    re_end_pvobject = re.compile(r"^\s*End of PVObject\s+(\w+)\s*$")
    re_generic_end = re.compile(r"^\s*End of\s+(.+?)\s*$")
    re_kv = re.compile(r"^\s*([^=]+?)\s*=\s*(.*?)\s*$")
    re_count = re.compile(r"^\s*(.+?),\s*Count\s*=\s*(\d+)\s*$")

    # Simple stack of dict nodes (each level is a dict to fill)
    stack: List[Dict[str, Any]] = [raw["tree"]]
    # For "End of <name>" handling on profile blocks
    name_stack: List[str] = ["<root>"]
    # For "Remarks, Count=5" items
    list_ctx: Optional[Tuple[str, Dict[str, Any]]] = None  # (list_name, container_dict)

    def cur() -> Dict[str, Any]:
        return stack[-1]

    for line in raw["lines"]:
        ss = line.strip()
        if not ss:
            continue

        # Begin PVObject
        m = re_pvobject_begin.match(ss)
        if m:
            obj_type = m.group(1) or "Root"
            obj_class = m.group(2)

            node: Dict[str, Any] = {"_type": obj_type, "_class": obj_class}
            cur().setdefault("PVObjects", [])
            cur()["PVObjects"].append(node)

            stack.append(node)
            name_stack.append(f"PVObject:{obj_class}")
            list_ctx = None
            continue

        # End PVObject
        m = re_end_pvobject.match(ss)
        if m:
            end_class = m.group(1)
            # Pop until we close the matching PVObject (best effort)
            for i in range(len(stack) - 1, 0, -1):
                node = stack[i]
                if isinstance(node, dict) and node.get("_class") == end_class:
                    stack = stack[:i]
                    name_stack = name_stack[:i]
                    break
            else:
                if len(stack) > 1:
                    stack.pop()
                    name_stack.pop()
            list_ctx = None
            continue

        # "X, Count=5" list header (Remarks)
        m = re_count.match(ss)
        if m:
            list_name = m.group(1).strip()
            count = int(m.group(2))
            container = {"Count": count, "items": {}}
            cur()[list_name] = container
            list_ctx = (list_name, container)
            continue

        # End of <something> (generic)
        m = re_generic_end.match(ss)
        if m and not ss.startswith("End of PVObject"):
            end_name = m.group(1).strip()

            # Close list context: "End of Remarks"
            if list_ctx is not None and end_name == list_ctx[0]:
                list_ctx = None
                continue

            # Close profile blocks like "End of TCubicProfile"
            if len(stack) > 1 and name_stack[-1] == f"Block:{end_name}":
                stack.pop()
                name_stack.pop()
                list_ctx = None
                continue

            # Otherwise ignore
            continue

        # Key=Value
        m = re_kv.match(ss)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip()

            # If we are inside a "Remarks, Count=.." block: put items there
            if list_ctx is not None:
                list_ctx[1]["items"][key] = val
                continue

            # Store KV
            cur()[key] = val

            # Special: profile sub-blocks (IAMProfile=TCubicProfile, etc.)
            # After this KV, subsequent lines (NPtsMax, Point_1...) belong to a dict named val until "End of val"
            if key.endswith("Profile") and re.match(r"^[A-Za-z]\w*$", val):
                subname = val
                cur()[subname] = {}
                stack.append(cur()[subname])
                name_stack.append(f"Block:{subname}")
                list_ctx = None
            continue

        # Unknown
        raw["unknown_lines"].append(ss)

    return raw


# -----------------------------------------------------------------------------
# PVObject search
# -----------------------------------------------------------------------------

def _find_pvobject(root: Any, class_name: str) -> Optional[Dict[str, Any]]:
    def rec(node: Any) -> Optional[Dict[str, Any]]:
        if isinstance(node, dict):
            if node.get("_class") == class_name:
                return node
            pvobjs = node.get("PVObjects")
            if isinstance(pvobjs, list):
                for o in pvobjs:
                    r = rec(o)
                    if r:
                        return r
            for v in node.values():
                r = rec(v)
                if r:
                    return r
        elif isinstance(node, list):
            for it in node:
                r = rec(it)
                if r:
                    return r
        return None
    return rec(root)


# -----------------------------------------------------------------------------
# IAM standardization
# -----------------------------------------------------------------------------

def _standardize_iam(iam_obj: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "mode": iam_obj.get("IAMMode"),
        "profile_type": iam_obj.get("IAMProfile"),
        "profile": None,
    }

    prof_key = str(iam_obj.get("IAMProfile") or "").strip()
    prof = iam_obj.get(prof_key) if prof_key else None
    if isinstance(prof, dict):
        points: List[Dict[str, Any]] = []
        meta: Dict[str, Any] = {}
        for k, v in prof.items():
            ks = str(k)
            if ks.startswith("Point_"):
                parts = [p.strip() for p in str(v).split(",")]
                if len(parts) == 2:
                    a = _to_number_if_possible(parts[0])
                    f = _to_number_if_possible(parts[1])
                    if isinstance(a, (int, float)) and isinstance(f, (int, float)):
                        points.append({"angle_deg": float(a), "iam": float(f)})
                    else:
                        points.append({"raw": str(v)})
                else:
                    points.append({"raw": str(v)})
            else:
                meta[ks] = _to_number_if_possible(v)

        if points and all(("angle_deg" in p and "iam" in p) for p in points):
            points.sort(key=lambda p: p["angle_deg"])  # type: ignore

        out["profile"] = {"name": prof_key, "meta": meta, "points": points}

    return out


# -----------------------------------------------------------------------------
# Main standardization
# -----------------------------------------------------------------------------

def _standardize(raw_tree: Dict[str, Any], source_name: str) -> Tuple[Dict[str, Any], List[str]]:
    warnings: List[str] = []

    root = raw_tree  # fallback for "electrical keys at root level"
    pvmodule = _find_pvobject(raw_tree, "pvModule") or {}
    commercial = _find_pvobject(raw_tree, "pvCommercial") or {}
    iam_obj = _find_pvobject(raw_tree, "pvIAM") or {}

    # Commercial / ID
    manufacturer = commercial.get("Manufacturer") or pvmodule.get("Manufacturer") or root.get("Manufacturer")
    model = commercial.get("Model") or pvmodule.get("Model") or root.get("Model")

    # Geometry in meters (sample)
    width_m = _g(commercial, commercial, "Width")
    height_m = _g(commercial, commercial, "Height")
    depth_m = _g(commercial, commercial, "Depth")
    weight_kg = _g(commercial, commercial, "Weight")

    area_m2 = None
    if isinstance(width_m, (int, float)) and isinstance(height_m, (int, float)):
        area_m2 = float(width_m) * float(height_m)

    # Tech / layout (fallback root)
    technol = (pvmodule.get("Technol") if pvmodule else None) or root.get("Technol")
    sub_layout = (pvmodule.get("SubModuleLayout") if pvmodule else None) or root.get("SubModuleLayout")
    front_surface = (pvmodule.get("FrontSurface") if pvmodule else None) or root.get("FrontSurface")

    ncel_s = _g(pvmodule, root, "NCelS")
    ncel_p = _g(pvmodule, root, "NCelP")
    ndiode = _g(pvmodule, root, "NDiode")
    bifaciality = _g(pvmodule, root, "BifacialityFactor")

    # STC ref
    gref = _g(pvmodule, root, "GRef")
    tref_c = _g(pvmodule, root, "TRef")

    # STC electrical
    pnom_w = _g(pvmodule, root, "PNom")
    isc_a = _g(pvmodule, root, "Isc")
    voc_v = _g(pvmodule, root, "Voc")
    imp_a = _g(pvmodule, root, "Imp")
    vmp_v = _g(pvmodule, root, "Vmp")

    # Tolerances
    tol_low = _g(pvmodule, root, "PNomTolLow")
    tol_up = _g(pvmodule, root, "PNomTolUp")

    # Efficiency from dimensions (if possible)
    eff_pct = None
    if isinstance(pnom_w, (int, float)) and isinstance(area_m2, (int, float)) and area_m2 > 0:
        eff_pct = float(pnom_w) / (1000.0 * float(area_m2)) * 100.0

    # Temp coeffs (raw units for now)
    mu_isc = _g(pvmodule, root, "muISC")
    mu_voc_spec = _g(pvmodule, root, "muVocSpec")
    mu_pmp_req = _g(pvmodule, root, "muPmpReq")
    rshunt = _g(pvmodule, root, "RShunt")
    rserie = _g(pvmodule, root, "RSerie")

    # Limits
    vmax_iec = _g(pvmodule, root, "VMaxIEC")
    vmax_ul = _g(pvmodule, root, "VMaxUL")

    # Remarks list
    remarks_items: List[str] = []
    rem = commercial.get("Remarks")
    if isinstance(rem, dict) and isinstance(rem.get("items"), dict):
        for kk in sorted(rem["items"].keys()):
            vv = str(rem["items"][kk]).strip()
            if vv:
                remarks_items.append(vv)

    # IAM
    iam_std = _standardize_iam(iam_obj) if iam_obj else None

    # Critical warnings
    crit_missing: List[str] = []
    for k, v in [("Manufacturer", manufacturer), ("Model", model), ("PNom", pnom_w), ("Vmp", vmp_v), ("Imp", imp_a)]:
        if v in (None, "", []):
            crit_missing.append(k)
    if crit_missing:
        warnings.append(f"Missing critical PAN fields: {', '.join(crit_missing)}")

    standard: Dict[str, Any] = {
        "meta": {
            "format": "pvsyst_pan",
            "source_name": source_name,
            "reader": "reader_pan_file",
            "warnings": warnings[:],
        },
        "module": {
            "manufacturer": manufacturer,
            "model": model,
            "technology": technol,
            "bifaciality_factor": bifaciality,
            "cells": {
                "series": ncel_s,
                "parallel": ncel_p,
                "diodes": ndiode,
                "layout": sub_layout,
            },
            "front_surface": front_surface,
            "dimensions_m": {"width": width_m, "height": height_m, "depth": depth_m},
            "area_m2": area_m2,
            "weight_kg": weight_kg,
            "remarks": remarks_items,
            "year_beg": commercial.get("YearBeg"),
            "datasource": commercial.get("DataSource"),
            "comment": commercial.get("Comment"),
        },
        "electrical": {
            "stc_ref": {"irradiance_w_m2": gref, "cell_temp_c": tref_c},
            "stc": {
                "pmp_w": pnom_w,
                "vmp_v": vmp_v,
                "imp_a": imp_a,
                "voc_v": voc_v,
                "isc_a": isc_a,
                "efficiency_pct": eff_pct,
                "pmp_tolerance_pct": {"minus": tol_low, "plus": tol_up},
            },
            "temp_coeff": {
                "mu_isc": mu_isc,
                "mu_voc_spec": mu_voc_spec,
                "mu_pmp_req": mu_pmp_req,
            },
            "limits": {
                "vmax_iec_v": vmax_iec,
                "vmax_ul_v": vmax_ul,
            },
            # We'll finalize mapping/units later
            "model_params": {
                "RShunt": rshunt,
                "RSerie": rserie,
            },
        },
        "iam": iam_std,
    }

    return standard, warnings


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def read_pan_file(source: Source) -> Dict[str, Any]:
    """
    Read a PVsyst .PAN file and return:
      {
        "meta": {...},
        "raw": {...},       # lossless parse
        "standard": {...},  # PVInsight normalized
      }
    """
    text, source_name = _decode_source(source)
    raw = _parse_pan_text(text)
    standard, warnings = _standardize(raw["tree"], source_name)

    return {
        "meta": {
            "format": "pvsyst_pan",
            "source_name": source_name,
            "reader": "reader_pan_file",
            "warnings": warnings,
        },
        "raw": raw,
        "standard": standard,
    }


# -----------------------------------------------------------------------------
# Manual test
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python reader_pan_file.py <file.PAN>")
        raise SystemExit(2)

    out = read_pan_file(Path(sys.argv[1]))
    print(json.dumps(out["standard"], indent=2, ensure_ascii=False))
