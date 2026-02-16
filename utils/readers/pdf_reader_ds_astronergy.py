# utils/readers/pdf_reader_ds_astronergy.py
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# ASTRONERGY (CHINT) DATASHEET READER — standardized output (PVInsight schema v1)
# Target PDF example:
#   (600~620)ASTRO N7_CHSM66RN(DG)F-BH_2382x1134x30_Europe_20240312.pdf
#
# Key point (Astronergy layout):
# - STC table header contains power classes (600..620)
# - NMOT table header does NOT contain power classes (it contains NMOT Pmpp values),
#   so we map NMOT columns by index onto the STC power classes.
#
# Standard output schema (core):
# {
#   "meta": {...},
#   "variants": [ { "variant_id", "power_class_w", "nameplate", "nmot", ... }, ... ],
#   "temperature": {...},
#   "operating": {...},
#   "mechanical": {...},
#   "validation": {...},
#   "raw": {... optional debug ...}
# }
#
# Standard key naming (consistent across suppliers):
# - STC/nameplate:  pmax_w, vmp_v, imp_a, voc_v, isc_a, eff_pct(optional)
# - NMOT:           pmax_w, vmp_v, imp_a, voc_v, isc_a
# - temperature:    coeff_pmax_pct_per_c, coeff_voc_pct_per_c, coeff_isc_pct_per_c, nmot_c, nmot_tol_c
# - operating:      max_system_voltage_v, max_series_fuse_a, operating_temp_c{min,max},
#                   junction_box_ip(optional), diodes_count(optional)
# - mechanical:     dimensions_mm{length,width,thickness}, weight_kg, cell_type_raw, cells_count(optional),
#                   connector_type, cable_length_raw(optional), etc.
# =============================================================================


# -----------------------------------------------------------------------------
# PDF helpers
# -----------------------------------------------------------------------------

def _require_pdfplumber():
    try:
        import pdfplumber  # type: ignore
        return pdfplumber
    except Exception as e:
        raise RuntimeError("This reader requires pdfplumber. Install with: pip install pdfplumber") from e


def _norm(s: Any) -> str:
    if s is None:
        return ""
    s = str(s).replace("\u00a0", " ").strip()
    s = s.replace("℃", "°C")
    s = s.replace("×", "x")
    s = re.sub(r"[ \t]+", " ", s)
    return s


def _to_float(x: str) -> Optional[float]:
    x = (x or "").strip().replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", x):
        return None
    try:
        return float(x)
    except Exception:
        return None


def _find_best_technical_page(pages_text: List[str]) -> int:
    best_i, best_score = 0, -1
    for i, raw in enumerate(pages_text):
        t = _norm(raw)
        score = 0
        score += 4 if re.search(r"\bElectrical Specifications\b", t, re.IGNORECASE) else 0
        score += 3 if re.search(r"\bMechanical Specifications\b", t, re.IGNORECASE) else 0
        score += 2 if re.search(r"\bSTC\b", t) else 0
        score += 2 if re.search(r"\bNMOT\b", t) else 0
        score += 1 if re.search(r"Temperature coefficient", t, re.IGNORECASE) else 0
        score += 1 if re.search(r"Outer dimensions|Module weight|Connector type", t, re.IGNORECASE) else 0
        if score > best_score:
            best_score = score
            best_i = i
    return best_i + 1


def _split_lines(text: str) -> List[str]:
    return [l.strip() for l in _norm(text).splitlines() if l.strip()]


# -----------------------------------------------------------------------------
# Electrical table parsing (row-based, 5 columns)
# -----------------------------------------------------------------------------

def _find_all_starts(lines: List[str]) -> List[int]:
    """Return indices of lines that start an electrical table (Rated output...)."""
    out: List[int] = []
    for i, l in enumerate(lines):
        if re.search(r"Rated output\s*\(Pmpp\s*/\s*Wp\)", l, re.IGNORECASE):
            out.append(i)
    return out


def _extract_powers_from_header(line: str) -> List[int]:
    # Expect: 600 605 610 615 620 (power class, integer)
    nums = [int(x) for x in re.findall(r"\b(\d{3})\b", line)]
    out: List[int] = []
    for n in nums:
        if 300 <= n <= 800 and n not in out:
            out.append(n)
    return out


def _extract_row_values(line: str) -> List[float]:
    vals: List[float] = []
    for n in re.findall(r"[-+]?\d+(?:\.\d+)?", line):
        f = _to_float(n)
        if f is not None:
            vals.append(f)
    return vals


def _parse_stc_table(lines: List[str]) -> Tuple[Dict[str, Dict[str, float]], List[int], Optional[int]]:
    """
    STC table: header line contains the power classes (600..620).
    Returns (stc_by_power, powers, start_idx).
    """
    starts = _find_all_starts(lines)
    for start in starts:
        powers = _extract_powers_from_header(lines[start])
        if len(powers) >= 3:
            stc_by_power: Dict[str, Dict[str, float]] = {str(p): {} for p in powers}

            def take_row(pat: str, key: str, idx_hint: int) -> None:
                row = None
                for k in range(start + idx_hint - 1, start + idx_hint + 2):
                    if 0 <= k < len(lines) and re.search(pat, lines[k], re.IGNORECASE):
                        row = lines[k]
                        break
                if row is None:
                    for k in range(start, min(start + 15, len(lines))):
                        if re.search(pat, lines[k], re.IGNORECASE):
                            row = lines[k]
                            break
                if row is None:
                    return

                vals = _extract_row_values(row)

                # Pmpp line includes the power header numbers: remove them
                if re.search(r"Rated output\s*\(Pmpp", row, re.IGNORECASE):
                    tmp = vals[:]
                    for p in powers:
                        for ii, v in enumerate(tmp):
                            if abs(v - float(p)) < 1e-6:
                                tmp.pop(ii)
                                break
                    vals = tmp

                vals = vals[: len(powers)]
                for i_p, p in enumerate(powers):
                    if i_p < len(vals):
                        stc_by_power[str(p)][key] = float(vals[i_p])

            take_row(r"Rated output\s*\(Pmpp\s*/\s*Wp\)", "pmax_w", 0)
            take_row(r"Rated voltage\s*\(Vmpp\s*/\s*V\)", "vmp_v", 1)
            take_row(r"Rated current\s*\(Impp\s*/\s*A\)", "imp_a", 2)
            take_row(r"Open circuit voltage\s*\(Voc\s*/\s*V\)", "voc_v", 3)
            take_row(r"Short circuit current\s*\(Isc\s*/\s*A\)", "isc_a", 4)
            take_row(r"Module efficiency", "eff_pct", 5)

            stc_by_power = {p: d for p, d in stc_by_power.items() if d}
            return stc_by_power, powers, start

    return {}, [], None


def _parse_nmot_table_using_powers(
    lines: List[str],
    powers: List[int],
    after_idx: int,
) -> Tuple[Dict[str, Dict[str, float]], Optional[int]]:
    """
    NMOT table: header line does NOT contain power classes (it contains NMOT Pmpp values).
    We map the 5 column values by index onto the STC power classes.
    Returns (nmot_by_power, start_idx).
    """
    starts = _find_all_starts(lines)
    start = None
    for s in starts:
        if s > after_idx:
            start = s
            break
    if start is None or not powers:
        return {}, None

    nmot_by_power: Dict[str, Dict[str, float]] = {str(p): {} for p in powers}

    def take_row(pat: str, key: str, idx_hint: int) -> None:
        row = None
        for k in range(start + idx_hint - 1, start + idx_hint + 2):
            if 0 <= k < len(lines) and re.search(pat, lines[k], re.IGNORECASE):
                row = lines[k]
                break
        if row is None:
            for k in range(start, min(start + 12, len(lines))):
                if re.search(pat, lines[k], re.IGNORECASE):
                    row = lines[k]
                    break
        if row is None:
            return

        vals = _extract_row_values(row)
        vals = vals[: len(powers)]
        for i_p, p in enumerate(powers):
            if i_p < len(vals):
                nmot_by_power[str(p)][key] = float(vals[i_p])

    take_row(r"Rated output\s*\(Pmpp\s*/\s*Wp\)", "pmax_w", 0)
    take_row(r"Rated voltage\s*\(Vmpp\s*/\s*V\)", "vmp_v", 1)
    take_row(r"Rated current\s*\(Impp\s*/\s*A\)", "imp_a", 2)
    take_row(r"Open circuit voltage\s*\(Voc\s*/\s*V\)", "voc_v", 3)
    take_row(r"Short circuit current\s*\(Isc\s*/\s*A\)", "isc_a", 4)

    nmot_by_power = {p: d for p, d in nmot_by_power.items() if d}
    return nmot_by_power, start


# -----------------------------------------------------------------------------
# Other sections parsing
# -----------------------------------------------------------------------------

def _parse_temperature_and_operating(lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    blob = "\n".join(lines)
    temperature: Dict[str, Any] = {}
    operating: Dict[str, Any] = {}

    m = re.search(r"Temperature coefficient\s*\(Pmpp\)\s*([-+0-9.]+)\s*%/°C", blob, re.IGNORECASE)
    if m:
        temperature["coeff_pmax_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"Temperature coefficient\s*\(Isc\)\s*([-+0-9.]+)\s*%/°C", blob, re.IGNORECASE)
    if m:
        temperature["coeff_isc_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"Temperature coefficient\s*\(Voc\)\s*([-+0-9.]+)\s*%/°C", blob, re.IGNORECASE)
    if m:
        temperature["coeff_voc_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"Nominal module operating\s*temperature\s*\(NMOT\)\s*(\d+)\s*±\s*(\d+)\s*°C", blob, re.IGNORECASE)
    if m:
        temperature["nmot_c"] = int(m.group(1))
        temperature["nmot_tol_c"] = int(m.group(2))

    # Operating params
    m = re.search(r"Max\.\s*series\s*fuse\s*rating\s*(\d+)\s*A", blob, re.IGNORECASE)
    if m:
        operating["max_series_fuse_a"] = int(m.group(1))

    # Standardize key name to max_system_voltage_v (int)
    m = re.search(r"Max\.\s*system\s*voltage\s*\(IEC/UL\)\s*(\d+)\s*VDC", blob, re.IGNORECASE)
    if m:
        operating["max_system_voltage_v"] = int(m.group(1))

    m = re.search(r"No\.\s*of\s*diodes\s*(\d+)", blob, re.IGNORECASE)
    if m:
        operating["diodes_count"] = int(m.group(1))

    m = re.search(r"Junction\s*box\s*IP\s*rating\s*IP\s*([0-9A-Za-z]+)", blob, re.IGNORECASE)
    if m:
        operating["junction_box_ip"] = m.group(1)

    return (
        {k: v for k, v in temperature.items() if v is not None},
        {k: v for k, v in operating.items() if v is not None},
    )


def _parse_mechanical(lines: List[str]) -> Dict[str, Any]:
    blob = "\n".join(lines)
    mech: Dict[str, Any] = {}

    m = re.search(r"Outer dimensions\s*\(L x W x H\)\s*([0-9]+)\s*x\s*([0-9]+)\s*x\s*([0-9]+)\s*mm", blob, re.IGNORECASE)
    if m:
        mech["dimensions_mm"] = {"length": int(m.group(1)), "width": int(m.group(2)), "thickness": int(m.group(3))}

    m = re.search(r"Cell type\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["cell_type_raw"] = m.group(1).strip()

    m = re.search(r"No\.\s*of\s*cells\s*([0-9]+)(?:\s*\(([^)]+)\))?", blob, re.IGNORECASE)
    if m:
        mech["cells_count"] = int(m.group(1))
        if m.group(2):
            mech["cells_layout"] = m.group(2).strip()

    m = re.search(r"Connector type\s*\(IEC/UL\)\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["connector_type"] = m.group(1).strip()

    m = re.search(r"Cable length\s*\(Including connector\)\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["cable_length_raw"] = m.group(1).strip()

    m = re.search(r"Module weight\s*([0-9.]+)\s*kg", blob, re.IGNORECASE)
    if m:
        mech["weight_kg"] = _to_float(m.group(1))

    # Extra fields (keep if present; harmless for other modules)
    m = re.search(r"Cable diameter\s*\(IEC/UL\)\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["cable_diameter"] = m.group(1).strip()

    m = re.search(r"Packing unit\s*([0-9]+)\s*pcs\s*/\s*box", blob, re.IGNORECASE)
    if m:
        mech["packing_unit_pcs_per_box"] = int(m.group(1))

    m = re.search(r"Modules per 40'\s*HQ\s*container\s*([0-9]+)\s*pcs", blob, re.IGNORECASE)
    if m:
        mech["modules_per_40hq"] = int(m.group(1))

    m = re.search(r"Maximum mechanical test load\s*([0-9]+)\s*Pa\s*\(front\)\s*/\s*([0-9]+)\s*Pa\s*\(back\)", blob, re.IGNORECASE)
    if m:
        mech["mechanical_test_load_pa"] = {"front": int(m.group(1)), "back": int(m.group(2))}

    return {k: v for k, v in mech.items() if v not in (None, "", {}, [])}


def _parse_identification(page1_text: str, page2_text: str, powers: List[int]) -> Dict[str, Any]:
    t1 = _norm(page1_text)
    t2 = _norm(page2_text)

    ident: Dict[str, Any] = {
        "manufacturer": "Astronergy (CHINT)",
        "family": None,
        "series": None,
        "power_range_w": None,
        "powers_w": powers,
        "models": [],
    }

    # Family/model
    m = re.search(r"\bCHSM[0-9A-Z\(\)\-/]+", t1)
    if not m:
        m = re.search(r"\bCHSM[0-9A-Z\(\)\-/]+", t2)
    if m:
        ident["family"] = m.group(0)

    # Series
    if re.search(r"\bASTRO\s*N7\b", t1, re.IGNORECASE) or re.search(r"\bASTRO\s*N7\b", t2, re.IGNORECASE):
        ident["series"] = "ASTRO N7"

    # Power range
    m = re.search(r"\b(\d{3})\s*~\s*(\d{3})W\b", t1)
    if not m:
        m = re.search(r"\b(\d{3})~(\d{3})W\b", t2)
    if m:
        ident["power_range_w"] = {"min": int(m.group(1)), "max": int(m.group(2))}

    if ident.get("family") and powers:
        ident["models"] = [f"{ident['family']}-{p}" for p in powers]
    else:
        ident["models"] = [str(p) for p in powers] if powers else []

    return {k: v for k, v in ident.items() if v not in (None, "", {}, [])}


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

def _validate_pmax_relation(block_by_variant: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    rep: Dict[str, Any] = {"by_variant": {}, "warnings": []}
    for vid, d in block_by_variant.items():
        pmax = d.get("pmax_w")
        vmp = d.get("vmp_v")
        imp = d.get("imp_a")
        if pmax is None or vmp is None or imp is None:
            rep["by_variant"][vid] = {"status": "missing"}
            continue
        p_est = vmp * imp
        rel = (p_est - pmax) / pmax if pmax else None
        ok = (rel is not None) and (abs(rel) <= 0.05)
        rep["by_variant"][vid] = {
            "status": "ok" if ok else "check",
            "pmax_w": float(pmax),
            "vmp_v": float(vmp),
            "imp_a": float(imp),
            "p_est_w": float(p_est),
            "rel_err": float(rel) if rel is not None else None,
        }
        if not ok and rel is not None:
            rep["warnings"].append(f"{vid}: Pmax={pmax:.2f} vs Vmp*Imp={p_est:.2f} (rel={rel:+.2%})")
    return rep


# -----------------------------------------------------------------------------
# Standardization (schema v1)
# -----------------------------------------------------------------------------

def _build_standard_output(
    pdf_path: str,
    tech_page: int,
    ident: Dict[str, Any],
    stc_by_power: Dict[str, Dict[str, float]],
    nmot_by_power: Dict[str, Dict[str, float]],
    mechanical: Dict[str, Any],
    operating: Dict[str, Any],
    temperature: Dict[str, Any],
) -> Dict[str, Any]:
    powers: List[int] = ident.get("powers_w", []) or []
    family = ident.get("family")
    manufacturer = ident.get("manufacturer", "Astronergy (CHINT)")
    series = ident.get("series")

    # Build variants
    variants: List[Dict[str, Any]] = []
    for p in powers:
        stc = stc_by_power.get(str(p), {}) or {}
        nmot = nmot_by_power.get(str(p), {}) or {}

        variant_id = f"{family}-{p}" if family else f"{p}"
        nameplate = {k: stc.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a", "eff_pct") if stc.get(k) is not None}
        nmot_std = {k: nmot.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a") if nmot.get(k) is not None}

        variants.append(
            {
                "variant_id": variant_id,
                "power_class_w": int(p),
                "nameplate": nameplate,
                "nmot": nmot_std,
                "efficiency_stc_pct": nameplate.get("eff_pct"),
            }
        )

    # Validation
    stc_flat = {v["variant_id"]: v.get("nameplate", {}) for v in variants}
    nmot_flat = {v["variant_id"]: v.get("nmot", {}) for v in variants}

    validation = {
        "stc": _validate_pmax_relation(stc_flat) if stc_flat else {},
        "nmot": _validate_pmax_relation(nmot_flat) if nmot_flat else {},
    }

    # Meta
    meta: Dict[str, Any] = {
        "schema": "pvinsight.module_datasheet.v1",
        "reader_id": "astronergy_pdf_v1",
        "source_pdf": str(pdf_path),
        "technical_page_used": tech_page,
        "manufacturer": manufacturer,
    }
    if family:
        meta["family"] = family
    if series:
        meta["series"] = series
    if ident.get("power_range_w") is not None:
        meta["power_range_w"] = ident.get("power_range_w")

    # Mechanical: keep normalized core keys + harmless extras
    mech_std: Dict[str, Any] = {}
    for k in (
        "dimensions_mm",
        "weight_kg",
        "cell_type_raw",
        "cells_count",
        "cells_layout",
        "connector_type",
        "cable_length_raw",
        "cable_diameter",
        "packing_unit_pcs_per_box",
        "modules_per_40hq",
        "mechanical_test_load_pa",
    ):
        if mechanical.get(k) is not None:
            mech_std[k] = mechanical.get(k)

    # Operating: ensure standard naming
    op_std: Dict[str, Any] = {}
    for k in ("max_system_voltage_v", "max_series_fuse_a", "operating_temp_c", "junction_box_ip", "diodes_count"):
        if operating.get(k) is not None:
            op_std[k] = operating.get(k)

    # Temperature: already standardized
    temp_std: Dict[str, Any] = {}
    for k in ("coeff_pmax_pct_per_c", "coeff_voc_pct_per_c", "coeff_isc_pct_per_c", "nmot_c", "nmot_tol_c"):
        if temperature.get(k) is not None:
            temp_std[k] = temperature.get(k)

    return {
        "meta": meta,
        "variants": variants,
        "temperature": temp_std,
        "operating": op_std,
        "mechanical": mech_std,
        "validation": validation,
    }


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def read_astronergy_datasheet(pdf_path: str) -> Dict[str, Any]:
    pdfplumber = _require_pdfplumber()
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(pdf_path)

    with pdfplumber.open(str(p)) as pdf:
        pages_text = [(page.extract_text() or "") for page in pdf.pages]
        tech_page = _find_best_technical_page(pages_text)

        page1_text = pages_text[0] if pages_text else ""
        tech_text = pages_text[tech_page - 1] if tech_page - 1 < len(pages_text) else ""

    lines = _split_lines(tech_text)

    stc_by_power, powers, stc_start = _parse_stc_table(lines)
    nmot_by_power: Dict[str, Dict[str, float]] = {}

    if stc_start is not None and powers:
        nmot_by_power, _ = _parse_nmot_table_using_powers(lines, powers, after_idx=stc_start)

    # Safety fallback: infer powers from STC dict keys
    if not powers and stc_by_power:
        try:
            powers = sorted(int(k) for k in stc_by_power.keys())
        except Exception:
            powers = []

    # Other sections
    temperature, operating = _parse_temperature_and_operating(lines)
    mechanical = _parse_mechanical(lines)

    ident = _parse_identification(page1_text, tech_text, powers)

    standardized = _build_standard_output(
        pdf_path=pdf_path,
        tech_page=tech_page,
        ident=ident,
        stc_by_power=stc_by_power,
        nmot_by_power=nmot_by_power,
        mechanical=mechanical,
        operating=operating,
        temperature=temperature,
    )

    # Optional raw trace
    standardized["raw"] = {
        "identification": ident,
        "electrical_stc_by_power": stc_by_power,
        "electrical_nmot_by_power": nmot_by_power,
        "technical_text_excerpt": "\n".join(lines[:40]),
    }

    def prune(x: Any) -> Any:
        if isinstance(x, dict):
            dd = {k: prune(v) for k, v in x.items()}
            return {k: v for k, v in dd.items() if v not in (None, "", {}, [], [""])}
        if isinstance(x, list):
            ll = [prune(v) for v in x]
            return [v for v in ll if v not in (None, "", {}, [], [""])]
        return x

    return prune(standardized)


# -----------------------------------------------------------------------------
# Console report (standard schema)
# -----------------------------------------------------------------------------

def print_astronergy_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("ASTRONERGY (CHINT) DATASHEET READER — PVInsight schema v1 (ALL VARIANTS)")
    print("=" * 110)

    meta = data.get("meta", {}) or {}
    print(f"PDF: {meta.get('source_pdf')}")
    print(f"Technical page used: {meta.get('technical_page_used')}")
    print("-" * 110)

    print("[META]")
    for k in ("schema", "reader_id", "manufacturer", "series", "family", "power_range_w"):
        if meta.get(k) is not None:
            print(f"  - {k}: {meta.get(k)}")

    variants: List[Dict[str, Any]] = data.get("variants", []) or []
    print("\n[VARIANTS]")
    print(f"  - count: {len(variants)}")
    for v in variants:
        print(f"      • {v.get('variant_id')} (power_class_w={v.get('power_class_w')})")

    mech = data.get("mechanical", {}) or {}
    if mech:
        print("\n[MECHANICAL]")
        for k, v in mech.items():
            print(f"  - {k}: {v}")

    temp = data.get("temperature", {}) or {}
    print("\n[TEMPERATURE]")
    if temp:
        for k, v in temp.items():
            print(f"  - {k}: {v}")
    else:
        print("  - (not found)")

    op = data.get("operating", {}) or {}
    if op:
        print("\n[OPERATING]")
        for k, v in op.items():
            print(f"  - {k}: {v}")

    def fmt(v: Any) -> str:
        return "-" if v is None else str(v)

    print("\n[ELECTRICAL — STC (nameplate)]")
    for v in variants:
        vid = v.get("variant_id")
        stc = (v.get("nameplate") or {})
        print(
            f"  - {vid}: Pmax={fmt(stc.get('pmax_w'))} W | Voc={fmt(stc.get('voc_v'))} V | Isc={fmt(stc.get('isc_a'))} A | "
            f"Vmp={fmt(stc.get('vmp_v'))} V | Imp={fmt(stc.get('imp_a'))} A | Eff={fmt(stc.get('eff_pct'))} %"
        )

    print("\n[ELECTRICAL — NMOT]")
    for v in variants:
        vid = v.get("variant_id")
        nm = (v.get("nmot") or {})
        if not nm:
            print(f"  - {vid}: (not parsed)")
            continue
        print(
            f"  - {vid}: Pmax={fmt(nm.get('pmax_w'))} W | Voc={fmt(nm.get('voc_v'))} V | Isc={fmt(nm.get('isc_a'))} A | "
            f"Vmp={fmt(nm.get('vmp_v'))} V | Imp={fmt(nm.get('imp_a'))} A"
        )

    val = data.get("validation", {}) or {}
    if val:
        print("\n[VALIDATION: Pmax ≈ Vmp×Imp]")
        for name in ("stc", "nmot"):
            block = (val.get(name) or {})
            byv = (block.get("by_variant") or {})
            warns = (block.get("warnings") or [])
            print(f"  {name.upper()}:")
            for v in variants:
                vid = v.get("variant_id")
                r = byv.get(vid, {})
                status = r.get("status", "missing")
                rel = r.get("rel_err")
                if rel is None:
                    print(f"    - {vid}: {status}")
                else:
                    print(f"    - {vid}: {status} (rel_err={rel:+.2%})")
            if warns:
                print("    WARNINGS:")
                for w in warns:
                    print(f"      - {w}")

    print("\n" + "=" * 110)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Astronergy datasheet reader (PVInsight schema v1)")
    ap.add_argument("pdf", help="Path to Astronergy datasheet PDF")
    ap.add_argument("--json", dest="json_out", help="Optional JSON output path")
    args = ap.parse_args()

    data = read_astronergy_datasheet(args.pdf)
    print_astronergy_report(data)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved JSON: {args.json_out}")


if __name__ == "__main__":
    main()
