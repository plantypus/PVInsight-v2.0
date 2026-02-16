# utils/readers/pdf_reader_ds_canadian_solar.py
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# CANADIAN SOLAR DATASHEET READER — PVInsight schema v1
#
# Supports 2 common Canadian Solar layouts:
#
# (A) "row_models" (HiKu6 / TOPBiHiKu6, etc.)
#     - STC rows: each line starts with full model id: CS6.1-72TB-585 ...
#     - NMOT may appear:
#         * as a separate section "ELECTRICAL DATA | NMOT"
#         * OR side-by-side on the same line (STC block on left, NMOT block on right)
#
# (B) "header_variants" (HiKu5 CS3Y-P, etc.)
#     - Header line: "CS3Y 435P 440P 445P ..."
#     - STC table, then a separate NMOT table (same column variants)
#
# Output schema (PVInsight v1):
# {
#   "meta": {...},
#   "variants": [ { "variant_id", "power_class_w", "nameplate", "noct", ... }, ... ],
#   "temperature": {...},
#   "operating": {...},
#   "mechanical": {...},
#   "validation": {...},
#   "raw": {... debug ...}
# }
# =============================================================================


# -----------------------------------------------------------------------------#
# Helpers
# -----------------------------------------------------------------------------#

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
    s = s.replace("ˣ", "x").replace("×", "x")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\r\n?", "\n", s)
    return s


def _to_float(s: str) -> Optional[float]:
    s = (s or "").strip().replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", s):
        return None
    try:
        return float(s)
    except Exception:
        return None


def _split_lines(text: str) -> List[str]:
    return [l.strip() for l in _norm(text).splitlines() if l.strip()]


def _find_best_technical_page(pages_text: List[str]) -> int:
    best_i, best_score = 0, -1
    for i, raw in enumerate(pages_text):
        t = _norm(raw)
        score = 0
        score += 5 if re.search(r"\bELECTRICAL DATA\s*\|\s*STC\b", t, re.IGNORECASE) else 0
        score += 5 if re.search(r"\bELECTRICAL DATA\s*\|\s*NMOT\b", t, re.IGNORECASE) else 0
        score += 3 if re.search(r"\bMECHANICAL DATA\b", t, re.IGNORECASE) else 0
        score += 3 if re.search(r"\bTEMPERATURE CHARACTERISTICS\b", t, re.IGNORECASE) else 0
        score += 1 if re.search(r"\bPmax\b|\bVoc\b|\bIsc\b|\bVmp\b|\bImp\b", t) else 0
        if score > best_score:
            best_score = score
            best_i = i
    return best_i + 1


# -----------------------------------------------------------------------------#
# Identification (2 layouts)
# -----------------------------------------------------------------------------#

# Layout A (row_models): full model per row (ends with -585 etc.)
CS_MODEL_RE_A = r"\bCS\d+(?:\.\d+)?-[0-9A-Z]+-\d{3,4}\b"

# Layout B (header_variants): family + variants in header columns (CS3Y 435P 440P ...)
CS_FAMILY_RE_B = r"\bCS[0-9A-Z\.]{2,}\b"
CS_VARIANT_TOKEN_RE_B = r"\b\d{3}P\b"


def _infer_power_class_from_variant_id(variant_id: str) -> Optional[int]:
    # Works for both:
    # - CS6.1-72TB-585 -> 585
    # - CS3Y-435P -> 435
    m = re.search(r"-(\d{3,4})(?:P)?$", variant_id)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _extract_series_family_from_page1(page1_text: str) -> Dict[str, Any]:
    t = _norm(page1_text)
    out: Dict[str, Any] = {"manufacturer": "Canadian Solar"}

    m = re.search(r"\bTOPBiHiKu\d+\b", t, re.IGNORECASE)
    if m:
        out["series"] = m.group(0)

    m = re.search(r"\b(\d{3})\s*W\s*[~\-]\s*(\d{3})\s*W\b", t, re.IGNORECASE)
    if m:
        out["power_range_w"] = {"min": int(m.group(1)), "max": int(m.group(2))}

    # Try to detect a family like "CS6.1-72TB" or "CS3Y-P"
    m = re.search(r"\b(CS\d+(?:\.\d+)?-[0-9A-Z]+)\b", t)
    if m:
        out["family"] = m.group(1)

    return out


def _detect_layout(lines: List[str]) -> str:
    # If any full model ids appear, it's layout A
    for l in lines:
        if re.search(CS_MODEL_RE_A, l):
            return "row_models"
    # Else if a header contains family + N variants (435P etc.), it's layout B
    for l in lines:
        if re.search(CS_FAMILY_RE_B, l) and len(re.findall(CS_VARIANT_TOKEN_RE_B, l)) >= 3:
            return "header_variants"
    return "unknown"


# -----------------------------------------------------------------------------#
# Parsing — Layout A (row_models)
# -----------------------------------------------------------------------------#

def _parse_stc_table_row_models(lines: List[str]) -> Tuple[Dict[str, Dict[str, float]], List[str], Dict[str, Any]]:
    """
    Parse STC rows of layout A:
      CS6.1-72TB-585 585 W 42.1 V 13.90 A 51.7 V 14.35 A 21.7%
    Also captures bifacial-gain rows (leading percent) into raw.
    """
    diag: Dict[str, Any] = {"layout": "row_models", "stc_table_found": False}
    stc_by_model: Dict[str, Dict[str, float]] = {}
    models: List[str] = []
    bifacial_gain: Dict[str, Any] = {}

    start_idx = None
    for i, l in enumerate(lines):
        if re.search(r"ELECTRICAL DATA\s*\|\s*STC", l, re.IGNORECASE):
            start_idx = i
            break
    if start_idx is None:
        return {}, [], diag

    diag["stc_table_found"] = True

    stop_re = re.compile(
        r"(TEMPERATURE CHARACTERISTICS|MECHANICAL DATA|ENGINEERING DRAWING|I-V CURVES)",
        re.IGNORECASE,
    )

    i = start_idx + 1
    current_model: Optional[str] = None

    row_re = re.compile(
        r"^(?P<model>" + CS_MODEL_RE_A + r")\s+"
        r"(?P<pmax>\d+(?:\.\d+)?)\s*W\s+"
        r"(?P<vmp>\d+(?:\.\d+)?)\s*V\s+"
        r"(?P<imp>\d+(?:\.\d+)?)\s*A\s+"
        r"(?P<voc>\d+(?:\.\d+)?)\s*V\s+"
        r"(?P<isc>\d+(?:\.\d+)?)\s*A\s+"
        r"(?P<eff>\d+(?:\.\d+)?)\s*%.*$",
        re.IGNORECASE,
    )

    bif_re = re.compile(
        r"^(?P<gain>\d+)%\s+"
        r"(?P<pmax>\d+(?:\.\d+)?)\s*W\s+"
        r"(?P<vmp>\d+(?:\.\d+)?)\s*V\s+"
        r"(?P<imp>\d+(?:\.\d+)?)\s*A\s+"
        r"(?P<voc>\d+(?:\.\d+)?)\s*V\s+"
        r"(?P<isc>\d+(?:\.\d+)?)\s*A\s+"
        r"(?P<eff>\d+(?:\.\d+)?)\s*%.*$",
        re.IGNORECASE,
    )

    while i < len(lines):
        l = lines[i]
        if stop_re.search(l):
            break

        m = row_re.match(l)
        if m:
            current_model = m.group("model")
            if current_model not in models:
                models.append(current_model)
            stc_by_model[current_model] = {
                "pmax_w": float(m.group("pmax")),
                "vmp_v": float(m.group("vmp")),
                "imp_a": float(m.group("imp")),
                "voc_v": float(m.group("voc")),
                "isc_a": float(m.group("isc")),
                "eff_pct": float(m.group("eff")),
            }
            i += 1
            continue

        if current_model:
            mm = bif_re.match(l)
            if mm:
                gain = int(mm.group("gain"))
                bifacial_gain.setdefault(current_model, {})
                bifacial_gain[current_model][str(gain)] = {
                    "pmax_w": float(mm.group("pmax")),
                    "vmp_v": float(mm.group("vmp")),
                    "imp_a": float(mm.group("imp")),
                    "voc_v": float(mm.group("voc")),
                    "isc_a": float(mm.group("isc")),
                    "eff_pct": float(mm.group("eff")),
                }
                i += 1
                continue

        i += 1

    diag["stc_models_count"] = len(models)
    return stc_by_model, models, {"diagnostic": diag, "bifacial_gain_stc": bifacial_gain}


def _parse_nmot_table_row_models(lines: List[str]) -> Tuple[Dict[str, Dict[str, float]], List[str], Dict[str, Any]]:
    """
    Parse NMOT rows of layout A.
    Two strategies:
      (1) Standalone section "ELECTRICAL DATA | NMOT" with model rows.
      (2) Fallback: scan ANY line for "model + 5 values" patterns that do NOT end with '%' (so not STC).
          This captures side-by-side tables on the same line (STC left, NMOT right).
    """
    diag: Dict[str, Any] = {"layout": "row_models", "nmot_table_found": False, "nmot_mode": None}
    nmot_by_model: Dict[str, Dict[str, float]] = {}
    models: List[str] = []

    # --- (1) try standalone header first
    start_idx = None
    for i, l in enumerate(lines):
        if re.search(r"^ELECTRICAL DATA\s*\|\s*NMOT", l, re.IGNORECASE):
            start_idx = i
            break

    stop_re = re.compile(
        r"^(TEMPERATURE CHARACTERISTICS|MECHANICAL DATA|ELECTRICAL DATA\b|ENGINEERING DRAWING|Frame Cross Section|I-V CURVES)",
        re.IGNORECASE,
    )

    row_re = re.compile(
        r"^(?P<model>" + CS_MODEL_RE_A + r")\s+"
        r"(?P<pmax>\d+(?:\.\d+)?)\s*W\s+"
        r"(?P<vmp>\d+(?:\.\d+)?)\s*V\s+"
        r"(?P<imp>\d+(?:\.\d+)?)\s*A\s+"
        r"(?P<voc>\d+(?:\.\d+)?)\s*V\s+"
        r"(?P<isc>\d+(?:\.\d+)?)\s*A\s*$",
        re.IGNORECASE,
    )

    if start_idx is not None:
        diag["nmot_table_found"] = True
        diag["nmot_mode"] = "standalone_section"
        i = start_idx + 1
        while i < len(lines):
            l = lines[i]
            if stop_re.search(l):
                break
            m = row_re.match(l)
            if m:
                model = m.group("model")
                if model not in models:
                    models.append(model)
                nmot_by_model[model] = {
                    "pmax_w": float(m.group("pmax")),
                    "vmp_v": float(m.group("vmp")),
                    "imp_a": float(m.group("imp")),
                    "voc_v": float(m.group("voc")),
                    "isc_a": float(m.group("isc")),
                }
            i += 1

        diag["nmot_models_count"] = len(models)
        return nmot_by_model, models, {"diagnostic": diag}

    # --- (2) fallback: side-by-side NMOT tokens on same line
    # Match: model + 5 values, NOT followed by percent (filters STC/bifacial blocks)
    # Works even if the line contains STC before it.
    diag["nmot_mode"] = "side_by_side_scan"

    scan_re = re.compile(
        r"(?P<model>" + CS_MODEL_RE_A + r")\s+"
        r"(?P<pmax>\d+(?:\.\d+)?)\s*W\s+"
        r"(?P<vmp>\d+(?:\.\d+)?)\s*V\s+"
        r"(?P<imp>\d+(?:\.\d+)?)\s*A\s+"
        r"(?P<voc>\d+(?:\.\d+)?)\s*V\s+"
        r"(?P<isc>\d+(?:\.\d+)?)\s*A(?!\s*\d+(?:\.\d+)?\s*%)",
        re.IGNORECASE,
    )

    for l in lines:
        for m in scan_re.finditer(l):
            model = m.group("model")
            # Heuristic: STC rows end with "%", NMOT block does not. This scan excludes "%".
            # Still, sometimes other lines could match — keep first for each model.
            if model in nmot_by_model:
                continue
            nmot_by_model[model] = {
                "pmax_w": float(m.group("pmax")),
                "vmp_v": float(m.group("vmp")),
                "imp_a": float(m.group("imp")),
                "voc_v": float(m.group("voc")),
                "isc_a": float(m.group("isc")),
            }

    if nmot_by_model:
        diag["nmot_table_found"] = True
        diag["nmot_models_count"] = len(nmot_by_model)
        models = list(nmot_by_model.keys())

    return nmot_by_model, models, {"diagnostic": diag}


# -----------------------------------------------------------------------------#
# Parsing — Layout B (header_variants: CS3Y 435P 440P ...)
# -----------------------------------------------------------------------------#

def _extract_family_and_variants_from_header(line: str) -> Tuple[Optional[str], List[str]]:
    """
    Example: "CS3Y 435P 440P 445P 450P 455P 460P"
    returns ("CS3Y", ["435P","440P",...])
    """
    tokens = re.findall(r"\b[A-Za-z0-9\.\-]+\b", line)
    if not tokens:
        return None, []
    family = tokens[0] if re.fullmatch(CS_FAMILY_RE_B, tokens[0]) else None
    variants = [t for t in tokens[1:] if re.fullmatch(CS_VARIANT_TOKEN_RE_B, t)]
    return family, variants


def _parse_table_header_variants(
    lines: List[str],
    header_pat: str,
    max_lookahead: int = 6,
) -> Tuple[Optional[int], Optional[str], List[str]]:
    """
    Find section header (STC or NMOT), then find the header line containing family + variants.
    Returns (header_line_index, family, variants).
    """
    start = None
    for i, l in enumerate(lines):
        if re.search(header_pat, l, re.IGNORECASE):
            start = i
            break
    if start is None:
        return None, None, []

    for j in range(start, min(start + max_lookahead, len(lines))):
        fam, vars_ = _extract_family_and_variants_from_header(lines[j])
        if fam and len(vars_) >= 3:
            return j, fam, vars_
    return start, None, []


def _parse_values_row_for_variants(line: str, n: int, want_pct: bool = False) -> List[float]:
    """
    Extract N numeric values from a row like:
      "Opt. Operating Current (Imp)10.41 A10.48 A..."
    We just find numbers in appearance order.
    """
    if want_pct:
        # often "18.4% 18.6% ..."
        nums = re.findall(r"[-+]?\d+(?:\.\d+)?(?=%)", line)
    else:
        nums = re.findall(r"[-+]?\d+(?:\.\d+)?", line)
    vals: List[float] = []
    for x in nums:
        fx = _to_float(x)
        if fx is not None:
            vals.append(fx)
    return vals[:n]


def _parse_stc_table_header_variants(lines: List[str]) -> Tuple[Dict[str, Dict[str, float]], List[str], Dict[str, Any]]:
    diag: Dict[str, Any] = {"layout": "header_variants", "stc_table_found": False}
    stc_by_model: Dict[str, Dict[str, float]] = {}
    models: List[str] = []

    header_idx, family, variants = _parse_table_header_variants(lines, r"ELECTRICAL DATA\s*\|\s*STC")
    if header_idx is None or not family or not variants:
        return {}, [], diag

    diag["stc_table_found"] = True
    diag["family"] = family
    diag["variants"] = variants

    # Build model ids like "CS3Y-435P"
    models = [f"{family}-{v}" for v in variants]
    for mid in models:
        stc_by_model[mid] = {}

    stop_re = re.compile(r"^(ELECTRICAL DATA\s*\|\s*NMOT|TEMPERATURE CHARACTERISTICS|MECHANICAL DATA|ENGINEERING DRAWING|I-V CURVES)", re.IGNORECASE)

    # Scan rows after header line
    i = header_idx + 1
    while i < len(lines):
        l = lines[i]
        if stop_re.search(l):
            break

        # Map known labels -> key
        if re.search(r"Nominal Max\. Power.*Pmax", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                stc_by_model[k]["pmax_w"] = float(v)

        elif re.search(r"Opt\.\s*Operating Voltage.*Vmp", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                stc_by_model[k]["vmp_v"] = float(v)

        elif re.search(r"Opt\.\s*Operating Current.*Imp", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                stc_by_model[k]["imp_a"] = float(v)

        elif re.search(r"Open Circuit Voltage.*Voc", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                stc_by_model[k]["voc_v"] = float(v)

        elif re.search(r"Short Circuit Current.*Isc", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                stc_by_model[k]["isc_a"] = float(v)

        elif re.search(r"Module Efficiency", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models), want_pct=True)
            for k, v in zip(models, vals):
                stc_by_model[k]["eff_pct"] = float(v)

        i += 1

    # prune empties
    stc_by_model = {k: v for k, v in stc_by_model.items() if v}
    diag["stc_models_count"] = len(stc_by_model)
    return stc_by_model, models, {"diagnostic": diag}


def _parse_nmot_table_header_variants(lines: List[str], family_hint: Optional[str], variants_hint: List[str]) -> Tuple[Dict[str, Dict[str, float]], List[str], Dict[str, Any]]:
    diag: Dict[str, Any] = {"layout": "header_variants", "nmot_table_found": False}
    nmot_by_model: Dict[str, Dict[str, float]] = {}
    models: List[str] = []

    header_idx, family, variants = _parse_table_header_variants(lines, r"ELECTRICAL DATA\s*\|\s*NMOT")
    if header_idx is None:
        return {}, [], diag

    # Some PDFs repeat family/variants, some don't. Use hints if missing.
    if not family or not variants:
        family = family_hint
        variants = variants_hint

    if not family or not variants:
        return {}, [], diag

    diag["nmot_table_found"] = True
    diag["family"] = family
    diag["variants"] = variants

    models = [f"{family}-{v}" for v in variants]
    for mid in models:
        nmot_by_model[mid] = {}

    stop_re = re.compile(r"^(TEMPERATURE CHARACTERISTICS|MECHANICAL DATA|ENGINEERING DRAWING|I-V CURVES|ELECTRICAL DATA\s*\|)", re.IGNORECASE)

    i = header_idx + 1
    while i < len(lines):
        l = lines[i]
        if stop_re.search(l):
            break

        if re.search(r"Nominal Max\. Power.*Pmax", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                nmot_by_model[k]["pmax_w"] = float(v)

        elif re.search(r"Opt\.\s*Operating Voltage.*Vmp", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                nmot_by_model[k]["vmp_v"] = float(v)

        elif re.search(r"Opt\.\s*Operating Current.*Imp", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                nmot_by_model[k]["imp_a"] = float(v)

        elif re.search(r"Open Circuit Voltage.*Voc", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                nmot_by_model[k]["voc_v"] = float(v)

        elif re.search(r"Short Circuit Current.*Isc", l, re.IGNORECASE):
            vals = _parse_values_row_for_variants(l, len(models))
            for k, v in zip(models, vals):
                nmot_by_model[k]["isc_a"] = float(v)

        i += 1

    nmot_by_model = {k: v for k, v in nmot_by_model.items() if v}
    diag["nmot_models_count"] = len(nmot_by_model)
    return nmot_by_model, models, {"diagnostic": diag}


# -----------------------------------------------------------------------------#
# Other sections parsing (unchanged)
# -----------------------------------------------------------------------------#

def _parse_temperature_characteristics(text: str) -> Dict[str, Any]:
    t = _norm(text)
    out: Dict[str, Any] = {}

    m = re.search(r"Temperature Coefficient\s*\(Pmax\)\s*([-+]?\d+(?:\.\d+)?)\s*%?\s*/\s*°C", t, re.IGNORECASE)
    if m: out["coeff_pmax_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"Temperature Coefficient\s*\(Voc\)\s*([-+]?\d+(?:\.\d+)?)\s*%?\s*/\s*°C", t, re.IGNORECASE)
    if m: out["coeff_voc_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"Temperature Coefficient\s*\(Isc\)\s*([-+]?\d+(?:\.\d+)?)\s*%?\s*/\s*°C", t, re.IGNORECASE)
    if m: out["coeff_isc_pct_per_c"] = _to_float(m.group(1))

    m = re.search(r"Nominal Module Operating Temperature\s*(\d+)\s*±\s*(\d+)\s*°C", t, re.IGNORECASE)
    if m:
        out["nmot_c"] = int(m.group(1))
        out["nmot_tol_c"] = int(m.group(2))

    return {k: v for k, v in out.items() if v is not None}


def _parse_operating_block(text: str) -> Dict[str, Any]:
    t = _norm(text)
    out: Dict[str, Any] = {}

    m = re.search(r"Operating Temperature\s*(-?\d+)\s*°C\s*~\s*\+?(\d+)\s*°C", t, re.IGNORECASE)
    if m: out["operating_temp_c"] = {"min": int(m.group(1)), "max": int(m.group(2))}

    m = re.search(r"Max\.\s*System Voltage\s*(\d{3,5})\s*V", t, re.IGNORECASE)
    if m: out["max_system_voltage_v"] = int(m.group(1))

    m = re.search(r"Max\.\s*Series Fuse Rating\s*(\d{1,3})\s*A", t, re.IGNORECASE)
    if m: out["max_series_fuse_a"] = int(m.group(1))

    m = re.search(r"Power Tolerance\s*([^\n]+)", t, re.IGNORECASE)
    if m: out["power_tolerance_raw"] = m.group(1).strip().replace(" ", "")

    m = re.search(r"Power Bifaciality\*?\s*(\d+(?:\.\d+)?)\s*%", t, re.IGNORECASE)
    if m: out["bifaciality_pct"] = _to_float(m.group(1))

    return {k: v for k, v in out.items() if v is not None and v != ""}


def _parse_mechanical_block(text: str) -> Dict[str, Any]:
    t = _norm(text)
    out: Dict[str, Any] = {}

    m = re.search(r"Cell Type\s*([^\n]+)", t, re.IGNORECASE)
    if m: out["cell_type_raw"] = m.group(1).strip()

    m = re.search(r"Cell Arrangement\s*(\d{2,4})", t, re.IGNORECASE)
    if m: out["cells_count"] = int(m.group(1))

    m = re.search(r"Dimensions\s*(\d{3,5})\s*[x×]\s*(\d{3,5})\s*[x×]\s*(\d{1,4})\s*mm", t, re.IGNORECASE)
    if m:
        out["dimensions_mm"] = {"length": int(m.group(1)), "width": int(m.group(2)), "thickness": int(m.group(3))}

    m = re.search(r"Weight\s*([0-9]+(?:\.\d+)?)\s*kg", t, re.IGNORECASE)
    if m: out["weight_kg"] = _to_float(m.group(1))

    m = re.search(r"Cable Length.*?\n([^\n]+)", t, re.IGNORECASE)
    if m: out["output_cable_raw"] = m.group(1).strip()

    m = re.search(r"Connector\s*([^\n]+)", t, re.IGNORECASE)
    if m: out["connector_type"] = m.group(1).strip()

    return {k: v for k, v in out.items() if v is not None and v != ""}


# -----------------------------------------------------------------------------#
# Validation
# -----------------------------------------------------------------------------#

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


# -----------------------------------------------------------------------------#
# Standardization (schema v1)
# -----------------------------------------------------------------------------#

def _build_standard_output(
    pdf_path: str,
    tech_page: int,
    ident: Dict[str, Any],
    models: List[str],
    stc_by_model: Dict[str, Dict[str, float]],
    nmot_by_model: Dict[str, Dict[str, float]],
    mechanical_raw: Dict[str, Any],
    operating_raw: Dict[str, Any],
    temperature_raw: Dict[str, Any],
    raw_debug: Dict[str, Any],
) -> Dict[str, Any]:
    manufacturer = "Canadian Solar"

    variants: List[Dict[str, Any]] = []
    for m in models:
        power_class = _infer_power_class_from_variant_id(m)

        stc = stc_by_model.get(m, {}) or {}
        nmot = nmot_by_model.get(m, {}) or {}

        nameplate = {k: stc.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a", "eff_pct") if stc.get(k) is not None}
        nmot_std = {k: nmot.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a") if nmot.get(k) is not None}

        variants.append(
            {
                "variant_id": m,
                "power_class_w": power_class,
                "nameplate": nameplate,
                "noct": nmot_std,  # keep key for downstream uniformity
                "efficiency_stc_pct": nameplate.get("eff_pct"),
            }
        )

    stc_flat = {v["variant_id"]: v.get("nameplate", {}) for v in variants}
    noct_flat = {v["variant_id"]: v.get("noct", {}) for v in variants}
    validation = {
        "stc": _validate_pmax_relation(stc_flat) if stc_flat else {},
        "noct": _validate_pmax_relation(noct_flat) if noct_flat else {},
    }

    meta: Dict[str, Any] = {
        "schema": "pvinsight.module_datasheet.v1",
        "reader_id": "canadian_solar_text_v2",
        "source_pdf": str(pdf_path),
        "technical_page_used": tech_page,
        "manufacturer": manufacturer,
        "parse_mode": "text",
    }
    for k in ("family", "series", "power_range_w"):
        if ident.get(k) is not None:
            meta[k] = ident.get(k)

    mech: Dict[str, Any] = {}
    for k in ("dimensions_mm", "weight_kg", "cell_type_raw", "connector_type", "output_cable_raw", "cells_count"):
        if mechanical_raw.get(k) is not None:
            mech[k] = mechanical_raw.get(k)

    op: Dict[str, Any] = {}
    for k in ("operating_temp_c", "max_system_voltage_v", "max_series_fuse_a", "bifaciality_pct"):
        if operating_raw.get(k) is not None:
            op[k] = operating_raw.get(k)
    if operating_raw.get("power_tolerance_raw") is not None:
        op["power_tolerance_raw"] = operating_raw.get("power_tolerance_raw")

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
        "raw": raw_debug or {},
    }


# -----------------------------------------------------------------------------#
# Public API
# -----------------------------------------------------------------------------#

def read_canadian_solar_datasheet(pdf_path: str) -> Dict[str, Any]:
    pdfplumber = _require_pdfplumber()
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(pdf_path)

    with pdfplumber.open(str(p)) as pdf:
        pages_text = [(page.extract_text() or "") for page in pdf.pages]
        tech_page_no = _find_best_technical_page(pages_text)

        page1_text = pages_text[0] if pages_text else ""
        tech_text = pages_text[tech_page_no - 1] if tech_page_no - 1 < len(pages_text) else ""
        full_text = "\n".join(pages_text)

    ident = _extract_series_family_from_page1(page1_text)
    lines = _split_lines(tech_text)

    layout = _detect_layout(lines)

    stc_by_model: Dict[str, Dict[str, float]] = {}
    nmot_by_model: Dict[str, Dict[str, float]] = {}
    models: List[str] = []

    raw_debug: Dict[str, Any] = {
        "tech_page": tech_page_no,
        "layout_detected": layout,
    }

    if layout == "row_models":
        stc_by_model, stc_models, stc_raw = _parse_stc_table_row_models(lines)
        nmot_by_model, nmot_models, nmot_raw = _parse_nmot_table_row_models(lines)

        models = stc_models[:] if stc_models else nmot_models[:]
        # If NMOT parsed but model order missing, keep STC order and fill nmot by key.
        if not models and (stc_by_model or nmot_by_model):
            models = list(stc_by_model.keys()) or list(nmot_by_model.keys())

        raw_debug["stc_debug"] = stc_raw
        raw_debug["nmot_debug"] = nmot_raw

    elif layout == "header_variants":
        stc_by_model, stc_models, stc_raw = _parse_stc_table_header_variants(lines)

        # For NMOT, reuse family/variants hints from STC parsing to be robust
        family_hint = (stc_raw.get("diagnostic") or {}).get("family")
        variants_hint = (stc_raw.get("diagnostic") or {}).get("variants") or []
        nmot_by_model, nmot_models, nmot_raw = _parse_nmot_table_header_variants(lines, family_hint, variants_hint)

        models = stc_models[:] if stc_models else nmot_models[:]
        raw_debug["stc_debug"] = stc_raw
        raw_debug["nmot_debug"] = nmot_raw

    else:
        # Fallback: try row_models anyway
        stc_by_model, stc_models, stc_raw = _parse_stc_table_row_models(lines)
        nmot_by_model, nmot_models, nmot_raw = _parse_nmot_table_row_models(lines)
        models = stc_models[:] if stc_models else nmot_models[:]
        raw_debug["layout_fallback"] = True
        raw_debug["stc_debug"] = stc_raw
        raw_debug["nmot_debug"] = nmot_raw

    raw_debug["models_order"] = models

    # Other blocks
    temperature = _parse_temperature_characteristics(tech_text)
    operating = _parse_operating_block(tech_text)
    mechanical = _parse_mechanical_block(tech_text)

    out = _build_standard_output(
        pdf_path=pdf_path,
        tech_page=tech_page_no,
        ident=ident,
        models=models,
        stc_by_model=stc_by_model,
        nmot_by_model=nmot_by_model,
        mechanical_raw=mechanical,
        operating_raw=operating,
        temperature_raw=temperature,
        raw_debug=raw_debug,
    )

    def prune(x: Any) -> Any:
        if isinstance(x, dict):
            d = {k: prune(v) for k, v in x.items()}
            return {k: v for k, v in d.items() if v not in (None, "", {}, [], [""])}
        if isinstance(x, list):
            l = [prune(v) for v in x]
            return [v for v in l if v not in (None, "", {}, [], [""])]
        return x

    return prune(out)


# -----------------------------------------------------------------------------#
# Console report (schema v1)
# -----------------------------------------------------------------------------#

def print_canadian_solar_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("CANADIAN SOLAR DATASHEET READER — PVInsight schema v1 (ALL VARIANTS)")
    print("=" * 110)

    meta = data.get("meta", {}) or {}
    print(f"PDF: {meta.get('source_pdf')}")
    print(f"Technical page used: {meta.get('technical_page_used')}")
    print("-" * 110)

    print("[META]")
    for k in ("schema", "reader_id", "manufacturer", "parse_mode", "series", "family", "power_range_w"):
        if meta.get(k) is not None:
            print(f"  - {k}: {meta.get(k)}")

    variants: List[Dict[str, Any]] = data.get("variants", []) or []
    print("\n[VARIANTS]")
    print(f"  - count: {len(variants)}")
    for v in variants:
        print(f"      • {v.get('variant_id')} (power_class_w={v.get('power_class_w')})")

    def fmt(v: Any) -> str:
        return "-" if v is None else str(v)

    print("\n[ELECTRICAL — STC (nameplate)]")
    for v in variants:
        vid = v.get("variant_id")
        stc = (v.get("nameplate") or {})
        if not stc:
            print(f"  - {vid}: (not parsed)")
            continue
        print(
            f"  - {vid}: Pmax={fmt(stc.get('pmax_w'))} W | Voc={fmt(stc.get('voc_v'))} V | Isc={fmt(stc.get('isc_a'))} A | "
            f"Vmp={fmt(stc.get('vmp_v'))} V | Imp={fmt(stc.get('imp_a'))} A | Eff={fmt(stc.get('eff_pct'))} %"
        )

    print("\n[ELECTRICAL — NMOT (stored under 'noct' key)]")
    for v in variants:
        vid = v.get("variant_id")
        nmot = (v.get("noct") or {})
        if not nmot:
            print(f"  - {vid}: (not parsed)")
            continue
        print(
            f"  - {vid}: Pmax={fmt(nmot.get('pmax_w'))} W | Voc={fmt(nmot.get('voc_v'))} V | Isc={fmt(nmot.get('isc_a'))} A | "
            f"Vmp={fmt(nmot.get('vmp_v'))} V | Imp={fmt(nmot.get('imp_a'))} A"
        )

    raw = data.get("raw", {}) or {}
    if raw:
        print("\n[DEBUG]")
        print(f"  - layout_detected: {raw.get('layout_detected')}")
        print(f"  - models_order: {raw.get('models_order')}")
        # If needed, you can print raw['nmot_debug'] etc.

    print("\n" + "=" * 110)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Canadian Solar datasheet reader (PVInsight schema v1, text-based)")
    ap.add_argument("pdf", help="Path to Canadian Solar datasheet PDF")
    ap.add_argument("--json", dest="json_out", help="Optional JSON output path")
    args = ap.parse_args()

    data = read_canadian_solar_datasheet(args.pdf)
    print_canadian_solar_report(data)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved JSON: {args.json_out}")


if __name__ == "__main__":
    main()
