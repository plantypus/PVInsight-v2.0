# utils/readers/pdf_reader_ds_das_solar.py
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# DAS SOLAR DATASHEET READER — standardized output (PVInsight schema v1)
# Target PDF example: DAS-DH144NA 575W~600W (2 pages)
#
# Core approach (DAS layout):
# - pdfplumber.extract_words() on technical page (tables are better as words)
# - cluster words into "rows" by Y coordinate
# - parse:
#   (1) Electrical Parameters (STC) table (6 columns) + mechanical fields on the right
#   (2) Electrical Parameters (NMOT) table (6 columns) + temperature coefficients and NMOT value (right side)
#   (3) Ratings / packaging block (regex over full rows)
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
# Standard keys:
# - STC/nameplate:  pmax_w, vmp_v, imp_a, voc_v, isc_a, eff_pct(optional)
# - NMOT:           pmax_w, vmp_v, imp_a, voc_v, isc_a
# - temperature:    coeff_pmax_pct_per_c, coeff_voc_pct_per_c, coeff_isc_pct_per_c, nmot_c, nmot_tol_c
# - operating:      max_system_voltage_v, max_series_fuse_a, operating_temp_c{min,max}, bifaciality_pct(optional), static_load_pa(optional)
# - mechanical:     dimensions_mm{length,width,thickness}, weight_kg, cell_type_raw, connector_type, output_cable_raw
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
    s = s.replace("×", "×")  # keep multiplication sign (we parse it)
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
    """
    DAS: technical page contains "Electrical Parameters (STC" and engineering drawing.
    """
    best_i, best_score = 0, -1
    for i, raw in enumerate(pages_text):
        t = _norm(raw)
        score = 0
        score += 4 if re.search(r"Electrical Parameters\s*\(STC", t, re.IGNORECASE) else 0
        score += 2 if re.search(r"\bNMOT\b", t) else 0
        score += 2 if re.search(r"Module Size|Glass Thickness|Output Cable|Connector", t, re.IGNORECASE) else 0
        score += 1 if re.search(r"Max\. System Voltage|Operating Temperature|Bifaciality", t, re.IGNORECASE) else 0
        if score > best_score:
            best_score = score
            best_i = i
    return best_i + 1


# -----------------------------------------------------------------------------
# Word rows
# -----------------------------------------------------------------------------

def _cluster_words_by_y(words: List[dict], tol: float = 2.0) -> List[List[dict]]:
    ws = sorted(words, key=lambda w: (w["top"], w["x0"]))
    rows: List[List[dict]] = []
    for w in ws:
        if not rows:
            rows.append([w])
            continue
        if abs(w["top"] - rows[-1][0]["top"]) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    for r in rows:
        r.sort(key=lambda w: w["x0"])
    return rows


def _row_text(row: List[dict]) -> str:
    return " ".join(_norm(w["text"]) for w in row if _norm(w["text"]))


def _rows_text(words: List[dict], tol: float = 2.0) -> List[str]:
    return [_row_text(r) for r in _cluster_words_by_y(words, tol=tol)]


def _find_row_idx(rows: List[str], pattern: str) -> Optional[int]:
    for i, r in enumerate(rows):
        if re.search(pattern, r, re.IGNORECASE):
            return i
    return None


# -----------------------------------------------------------------------------
# Identification (family + variant models)
# -----------------------------------------------------------------------------

def _extract_family_and_power_range(page1_text: str) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
    t = _norm(page1_text)

    fam = None
    m = re.search(r"\bDAS-DH[0-9A-Z]+", t)
    if m:
        fam = m.group(0)

    rng = None
    m = re.search(r"(\d{3})\s*W\s*~\s*(\d{3})\s*W", t, re.IGNORECASE)
    if m:
        rng = (int(m.group(1)), int(m.group(2)))
    else:
        m = re.search(r"(\d{3})W~(\d{3})W", t)
        if m:
            rng = (int(m.group(1)), int(m.group(2)))

    return fam, rng


def _build_variant_ids(family: Optional[str], powers: List[int]) -> List[str]:
    if not powers:
        return []
    if family:
        return [f"{family}-{p}" for p in powers]
    return [str(p) for p in powers]


# -----------------------------------------------------------------------------
# DAS table parsing (row-based, 6 columns)
# -----------------------------------------------------------------------------

def _parse_6_values_left_of_markers(row: str, cut_markers: List[str]) -> List[float]:
    """
    Extract floats from the *left part* of a row (before right-side markers like temperature coeff labels).
    Prevents false matches where the same row contains 'Isc'/'Voc' text on the right side.
    """
    left = row
    for mk in cut_markers:
        m = re.search(mk, left, re.IGNORECASE)
        if m:
            left = left[: m.start()]
            break

    nums = re.findall(r"[-+]?\d+(?:\.\d+)?", left)
    vals: List[float] = []
    for n in nums:
        fv = _to_float(n)
        if fv is not None:
            vals.append(fv)
    return vals


def _extract_powers_from_stc_header(row: str) -> List[int]:
    nums = [int(x) for x in re.findall(r"\b(5\d{2}|6\d{2})\b", row)]
    out: List[int] = []
    for n in nums:
        if 300 <= n <= 800 and n not in out:
            out.append(n)
    return out


def _parse_stc_block(rows: List[str], start_idx: int) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any], List[int]]:
    """
    Parse STC electrical table + mechanical parameters from the right part of the same lines.
    """
    block = rows[start_idx : start_idx + 10]

    pmax_row = next((r for r in block if "Pmax" in r and "Nominal" in r), "")
    powers = _extract_powers_from_stc_header(pmax_row)

    stc: Dict[str, Dict[str, float]] = {str(p): {} for p in powers}
    mech: Dict[str, Any] = {}

    CUT_MARKERS_STC = [
        r"\bCell Type\b",
        r"\bModule Size\b",
        r"\bGlass Thickness\b",
        r"\bModule Weight\b",
        r"\bOutput Cable\b",
        r"\bConnector\b",
    ]

    def assign(row_pat: str, key: str) -> str:
        row = next((r for r in block if re.search(row_pat, r, re.IGNORECASE)), "")
        if not row:
            return ""
        vals = _parse_6_values_left_of_markers(row, CUT_MARKERS_STC)
        vals = vals[: len(powers)]
        for i, p in enumerate(powers):
            if i < len(vals):
                stc[str(p)][key] = float(vals[i])
        return row

    r_pmax = assign(r"Nominal Max\. Power.*Pmax", "pmax_w")
    r_voc = assign(r"Open Circuit Voltage.*Voc", "voc_v")
    r_isc = assign(r"Short Circuit Current.*Isc", "isc_a")
    r_vmp = assign(r"Operating Voltage.*Vmp", "vmp_v")
    r_imp = assign(r"Operating Current.*Imp", "imp_a")
    r_eff = assign(r"Efficiency", "eff_pct")

    joined = "\n".join([r_pmax, r_voc, r_isc, r_vmp, r_imp, r_eff])

    # Mechanical fields (right side of the STC rows)
    m = re.search(r"\bCell Type\b\s+([A-Za-z0-9 \-]+)", joined, re.IGNORECASE)
    if m:
        mech["cell_type_raw"] = m.group(1).strip()

    # Module Size e.g. "2278×1134×30mm"
    m = re.search(r"\bModule Size\b\s+([0-9×x]+\s*×\s*[0-9×x]+\s*×\s*[0-9]+mm)", joined, re.IGNORECASE)
    if m:
        raw = m.group(1).replace(" ", "")
        mm = re.search(r"(\d{3,5})×(\d{3,5})×(\d{1,4})mm", raw)
        if mm:
            mech["dimensions_mm"] = {"length": int(mm.group(1)), "width": int(mm.group(2)), "thickness": int(mm.group(3))}
        else:
            mech["dimensions_raw"] = raw

    m = re.search(r"\bGlass Thickness\b\s+([0-9.]+mm\s*\+\s*[0-9.]+mm)", joined, re.IGNORECASE)
    if m:
        mech["glass_thickness_raw"] = m.group(1).replace(" ", "")

    m = re.search(r"\bModule Weight\b\s+([0-9.]+)\s*Kg", joined, re.IGNORECASE)
    if m:
        mech["weight_kg"] = _to_float(m.group(1))

    m = re.search(r"\bOutput Cable\b\s+(.+?)(?:\n|$)", joined, re.IGNORECASE)
    if m:
        mech["output_cable_raw"] = m.group(1).strip()

    m = re.search(r"\bConnector\b\s+(.+?)(?:\n|$)", joined, re.IGNORECASE)
    if m:
        mech["connector_type"] = m.group(1).strip()

    stc = {p: d for p, d in stc.items() if d}
    mech = {k: v for k, v in mech.items() if v not in (None, "", {})}
    return stc, mech, powers


def _parse_nmot_and_temp_block(rows: List[str], start_idx: int, powers: List[int]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any]]:
    """
    Parse NMOT electrical table + temperature coefficients/NMOT value on the right side.

    Fix:
    - anchor matching on the left label (start-of-line)
    - cut numeric extraction before right-side markers
    """
    block = rows[start_idx : start_idx + 12]
    nmot: Dict[str, Dict[str, float]] = {str(p): {} for p in powers}
    temp: Dict[str, Any] = {}

    CUT_MARKERS_NMOT = [
        r"Short Circuit Current\(Isc\)",
        r"Open Circuit Voltage\(Voc\)",
        r"Nominal Max\. Power\(Pmax\)",
        r"\bNMOT\b",
        r"\bTemperature\b",
    ]

    def find_row_left(label_regex_anchored: str) -> str:
        for r in block:
            if re.match(label_regex_anchored, r.strip(), re.IGNORECASE):
                return r
        return ""

    def assign(label_anchored: str, key: str) -> None:
        row = find_row_left(label_anchored)
        if not row:
            return
        vals = _parse_6_values_left_of_markers(row, CUT_MARKERS_NMOT)
        vals = vals[: len(powers)]
        for i, p in enumerate(powers):
            if i < len(vals):
                nmot[str(p)][key] = float(vals[i])

    assign(r"^Nominal Max\. Power\(Pmax/W\)", "pmax_w")
    assign(r"^Open Circuit Voltage\(Voc/V\)", "voc_v")
    assign(r"^Short Circuit Current\(Isc/A\)", "isc_a")
    assign(r"^Operating Voltage\(Vmp/V\)", "vmp_v")
    assign(r"^Operating Current\(Imp/A\)", "imp_a")

    # Temperature coefficients + NMOT value are on the right side; parse from block blob
    blob = "\n".join(block)

    m = re.search(r"Short Circuit Current\(Isc\)\s*([+\-]?\d+(?:\.\d+)?)\s*%/°C", blob, re.IGNORECASE)
    if m:
        temp["coeff_isc_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"Open Circuit Voltage\(Voc\)\s*([+\-]?\d+(?:\.\d+)?)\s*%/°C", blob, re.IGNORECASE)
    if m:
        temp["coeff_voc_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"Nominal Max\. Power\(Pmax\)\s*([+\-]?\d+(?:\.\d+)?)\s*%/°C", blob, re.IGNORECASE)
    if m:
        temp["coeff_pmax_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"\bNMOT\b\s*(\d+)\s*±\s*(\d+)\s*°C", blob, re.IGNORECASE)
    if m:
        temp["nmot_c"] = int(m.group(1))
        temp["nmot_tol_c"] = int(m.group(2))

    nmot = {p: d for p, d in nmot.items() if d}
    temp = {k: v for k, v in temp.items() if v is not None}
    return nmot, temp


def _parse_ratings_block(rows: List[str]) -> Dict[str, Any]:
    """
    Parse ratings / packaging. Normalize key names to schema v1.
    """
    blob = "\n".join(rows)
    out: Dict[str, Any] = {}

    m = re.search(r"Max\.?\s*System Voltage\s*DC\s*(\d{3,5})\s*V", blob, re.IGNORECASE)
    if m:
        out["max_system_voltage_v"] = int(m.group(1))

    # Some DAS PDFs express tolerance in W; keep a raw string key (won't break others)
    m = re.search(r"Power Tolerance\s*([0-9]+\s*~\s*\+\s*[0-9]+)\s*W", blob, re.IGNORECASE)
    if m:
        out["power_tolerance_w"] = m.group(1).replace(" ", "")

    m = re.search(r"Operating Temperature\s*(-?\d+)\s*°C\s*~\s*\+?(\d+)\s*°C", blob, re.IGNORECASE)
    if m:
        out["operating_temp_c"] = {"min": int(m.group(1)), "max": int(m.group(2))}

    m = re.search(r"Max\.?\s*Fuse Rated Current\s*(\d{1,3})\s*A", blob, re.IGNORECASE)
    if m:
        # Standard key
        out["max_series_fuse_a"] = int(m.group(1))

    m = re.search(r"Bifaciality\s*(\d+)\s*%\s*±\s*(\d+)\s*%", blob, re.IGNORECASE)
    if m:
        out["bifaciality_pct"] = float(m.group(1))
        out["bifaciality_tol_pct"] = float(m.group(2))

    m = re.search(r"Static Load\s*Front\s*(\d+)\s*Pa,\s*Back\s*(\d+)\s*Pa", blob, re.IGNORECASE)
    if m:
        out["static_load_pa"] = {"front": int(m.group(1)), "back": int(m.group(2))}

    m = re.search(r"Packing Data\s*(.+)$", blob, re.IGNORECASE | re.MULTILINE)
    if m:
        out["packing_data_raw"] = m.group(1).strip()

    return {k: v for k, v in out.items() if v not in (None, "", {}, [])}


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
    family: Optional[str],
    power_range: Optional[Tuple[int, int]],
    powers: List[int],
    stc_by_power: Dict[str, Dict[str, float]],
    nmot_by_power: Dict[str, Dict[str, float]],
    mechanical_raw: Dict[str, Any],
    operating_raw: Dict[str, Any],
    temperature_raw: Dict[str, Any],
) -> Dict[str, Any]:
    manufacturer = "DAS Solar"
    variant_ids = _build_variant_ids(family, powers)

    # Variants
    variants: List[Dict[str, Any]] = []
    for p, vid in zip(powers, variant_ids):
        stc = stc_by_power.get(str(p), {}) or {}
        nmot = nmot_by_power.get(str(p), {}) or {}

        nameplate = {k: stc.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a", "eff_pct") if stc.get(k) is not None}
        nmot_std = {k: nmot.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a") if nmot.get(k) is not None}

        variants.append(
            {
                "variant_id": vid,
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
        "reader_id": "das_pdf_v1",
        "source_pdf": str(pdf_path),
        "technical_page_used": tech_page,
        "manufacturer": manufacturer,
    }
    if family:
        meta["family"] = family
    if power_range:
        meta["power_range_w"] = {"min": int(power_range[0]), "max": int(power_range[1])}

    # Mechanical normalization
    mech: Dict[str, Any] = {}
    if mechanical_raw.get("dimensions_mm") is not None:
        mech["dimensions_mm"] = mechanical_raw.get("dimensions_mm")
    if mechanical_raw.get("weight_kg") is not None:
        mech["weight_kg"] = mechanical_raw.get("weight_kg")
    if mechanical_raw.get("cell_type_raw") is not None:
        mech["cell_type_raw"] = mechanical_raw.get("cell_type_raw")
    if mechanical_raw.get("connector_type") is not None:
        mech["connector_type"] = mechanical_raw.get("connector_type")
    if mechanical_raw.get("output_cable_raw") is not None:
        mech["output_cable_raw"] = mechanical_raw.get("output_cable_raw")

    # Keep useful raw extras without breaking other modules
    for k in ("glass_thickness_raw", "dimensions_raw", "packing_data_raw"):
        if mechanical_raw.get(k) is not None:
            mech[k] = mechanical_raw.get(k)

    # Operating normalization
    op: Dict[str, Any] = {}
    for k in ("max_system_voltage_v", "max_series_fuse_a", "operating_temp_c", "bifaciality_pct", "bifaciality_tol_pct", "static_load_pa"):
        if operating_raw.get(k) is not None:
            op[k] = operating_raw.get(k)
    # keep tolerance if present
    if operating_raw.get("power_tolerance_w") is not None:
        op["power_tolerance_w"] = operating_raw.get("power_tolerance_w")

    # Temperature normalization
    temp: Dict[str, Any] = {}
    for k in ("coeff_pmax_pct_per_c", "coeff_voc_pct_per_c", "coeff_isc_pct_per_c", "nmot_c", "nmot_tol_c"):
        if temperature_raw.get(k) is not None:
            temp[k] = temperature_raw.get(k)

    return {
        "meta": meta,
        "variants": variants,
        "temperature": temp,
        "operating": op,
        "mechanical": mech,
        "validation": validation,
    }


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def read_das_solar_datasheet(pdf_path: str) -> Dict[str, Any]:
    pdfplumber = _require_pdfplumber()
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(pdf_path)

    with pdfplumber.open(str(p)) as pdf:
        pages_text = [(page.extract_text() or "") for page in pdf.pages]
        tech_page = _find_best_technical_page(pages_text)

        page1_text = pages_text[0] if pages_text else ""
        tech_words = pdf.pages[tech_page - 1].extract_words()

    family, power_range = _extract_family_and_power_range(page1_text)

    rows = _rows_text(tech_words, tol=2.0)

    # STC table start
    idx_stc = _find_row_idx(rows, r"Electrical Parameters\s*\(STC")
    if idx_stc is None:
        idx_stc = _find_row_idx(rows, r"Nominal Max\. Power\(Pmax/W\)\s+575\s+580")

    idx_stc_tbl = _find_row_idx(rows, r"Nominal Max\. Power\(Pmax/W\)\s+575")
    if idx_stc_tbl is None:
        idx_stc_tbl = idx_stc if idx_stc is not None else 0

    stc_by_power, mech_raw, powers = _parse_stc_block(rows, idx_stc_tbl)

    # NMOT table start (second occurrence of Pmax row with ~43x / 44x / 45x values)
    nmot_candidates = [i for i, r in enumerate(rows) if "Nominal Max. Power(Pmax/W)" in r]
    idx_nmot_tbl = None
    if nmot_candidates:
        for i in nmot_candidates:
            if i > idx_stc_tbl + 2 and re.search(r"\b43\d\b|\b44\d\b|\b45\d\b", rows[i]):
                idx_nmot_tbl = i
                break

    nmot_by_power: Dict[str, Dict[str, float]] = {}
    temp_raw: Dict[str, Any] = {}
    if idx_nmot_tbl is not None and powers:
        nmot_by_power, temp_raw = _parse_nmot_and_temp_block(rows, idx_nmot_tbl, powers)

    op_raw = _parse_ratings_block(rows)

    standardized = _build_standard_output(
        pdf_path=pdf_path,
        tech_page=tech_page,
        family=family,
        power_range=power_range,
        powers=powers,
        stc_by_power=stc_by_power,
        nmot_by_power=nmot_by_power,
        mechanical_raw=mech_raw,
        operating_raw=op_raw,
        temperature_raw=temp_raw,
    )

    standardized["raw"] = {
        "rows_excerpt": rows[:40],
        "electrical_stc_by_power": stc_by_power,
        "electrical_nmot_by_power": nmot_by_power,
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

def print_das_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("DAS SOLAR DATASHEET READER — PVInsight schema v1 (ALL VARIANTS)")
    print("=" * 110)

    meta = data.get("meta", {}) or {}
    print(f"PDF: {meta.get('source_pdf')}")
    print(f"Technical page used: {meta.get('technical_page_used')}")
    print("-" * 110)

    print("[META]")
    for k in ("schema", "reader_id", "manufacturer", "family", "power_range_w"):
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

    op = data.get("operating", {}) or {}
    if op:
        print("\n[OPERATING]")
        for k, v in op.items():
            print(f"  - {k}: {v}")

    temp = data.get("temperature", {}) or {}
    print("\n[TEMPERATURE]")
    if temp:
        for k, v in temp.items():
            print(f"  - {k}: {v}")
    else:
        print("  - (not found)")

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
    ap = argparse.ArgumentParser(description="DAS Solar datasheet reader (PVInsight schema v1)")
    ap.add_argument("pdf", help="Path to DAS datasheet PDF")
    ap.add_argument("--json", dest="json_out", help="Optional JSON output path")
    args = ap.parse_args()

    data = read_das_solar_datasheet(args.pdf)
    print_das_report(data)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved JSON: {args.json_out}")


if __name__ == "__main__":
    main()
