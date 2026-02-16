# PATCH COMPLET — DAS SOLAR (corrige NMOT Isc + nettoyage STC parsing)
#
# Problèmes corrigés :
# 1) NMOT Isc prenait Pmax : la ligne Pmax contenait aussi "Isc" côté droit (coeffs température).
#    -> Fix : matching ANCRÉ en début de ligne + extraction des 6 valeurs UNIQUEMENT à gauche des marqueurs.
# 2) STC parsing : tu appelais _parse_6_values_left_of_markers(row, CUT_MARKERS) mais CUT_MARKERS n’existait pas.
#    -> Fix : ajout d’un CUT_MARKERS_STC local au bloc STC (moins strict que NMOT).


from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# DAS SOLAR DATASHEET READER — specialized
# Target PDF example: DAS-DH144NA 575W~600W (2 pages)
#
# Core approach:
# - pdfplumber.extract_words() on technical page
# - cluster words into text rows by Y coordinate
# - parse the 3 key blocks:
#   (1) Electrical Parameters (STC) + Mechanical (right side)
#   (2) Electrical Parameters (NMOT) + Temperature coefficients + NMOT value
#   (3) Ratings / Bifacial gain / Packaging (right side items)
#
# Console print shows ALL models (variants by power).
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
    s = re.sub(r"[ \t]+", " ", s)
    return s


def _to_float(x: str) -> Optional[float]:
    x = x.strip().replace(",", ".")
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


def _build_models(family: Optional[str], powers: List[int]) -> List[str]:
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
    This prevents false matches where the same row contains 'Isc'/'Voc' text on the right side.
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
    # STC header row contains 6 power columns: 575 580 585 590 595 600
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

    # STC rows sometimes carry mechanical fields on the right; we cut before those to isolate the 6 numeric values.
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
    r_voc  = assign(r"Open Circuit Voltage.*Voc", "voc_v")
    r_isc  = assign(r"Short Circuit Current.*Isc", "isc_a")
    r_vmp  = assign(r"Operating Voltage.*Vmp", "vmp_v")
    r_imp  = assign(r"Operating Current.*Imp", "imp_a")
    r_eff  = assign(r"Efficiency", "eff_pct")

    joined = "\n".join([r_pmax, r_voc, r_isc, r_vmp, r_imp, r_eff])

    m = re.search(r"\bCell Type\b\s+([A-Za-z0-9 \-]+)", joined, re.IGNORECASE)
    if m:
        mech["cell_type_raw"] = m.group(1).strip()

    m = re.search(r"\bModule Size\b\s+([0-9×x]+\s*×\s*[0-9×x]+\s*×\s*[0-9]+mm)", joined, re.IGNORECASE)
    if m:
        raw = m.group(1).replace(" ", "")
        mech["module_size_raw"] = raw
        mm = re.search(r"(\d{3,5})×(\d{3,5})×(\d{1,4})mm", raw)
        if mm:
            mech["dimensions_mm"] = {"length": int(mm.group(1)), "width": int(mm.group(2)), "thickness": int(mm.group(3))}

    m = re.search(r"\bGlass Thickness\b\s+([0-9.]+mm\s*\+\s*[0-9.]+mm)", joined, re.IGNORECASE)
    if m:
        mech["glass_thickness"] = m.group(1).replace(" ", "")

    m = re.search(r"\bModule Weight\b\s+([0-9.]+)\s*Kg", joined, re.IGNORECASE)
    if m:
        mech["weight_kg"] = _to_float(m.group(1))

    m = re.search(r"\bOutput Cable\b\s+(.+?)(?:\n|$)", joined, re.IGNORECASE)
    if m:
        mech["output_cable"] = m.group(1).strip()

    m = re.search(r"\bConnector\b\s+(.+?)(?:\n|$)", joined, re.IGNORECASE)
    if m:
        mech["connector"] = m.group(1).strip()

    stc = {p: d for p, d in stc.items() if d}
    mech = {k: v for k, v in mech.items() if v not in (None, "", {})}
    return stc, mech, powers


def _parse_nmot_and_temp_block(rows: List[str], start_idx: int, powers: List[int]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any]]:
    """
    Parse NMOT electrical table + temperature coefficients/NMOT value on the right side.

    Fix:
    - Anchor matching on the *left label* (start of line) to avoid picking Pmax row when 'Isc' appears on the right.
    - Parse only the left part of the line (cut before right-side markers).
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

    def assign(label_anchored: str, key: str) -> str:
        row = find_row_left(label_anchored)
        if not row:
            return ""
        vals = _parse_6_values_left_of_markers(row, CUT_MARKERS_NMOT)
        vals = vals[: len(powers)]
        for i, p in enumerate(powers):
            if i < len(vals):
                nmot[str(p)][key] = float(vals[i])
        return row

    # ANCHORED labels (left side)
    r_pmax = assign(r"^Nominal Max\. Power\(Pmax/W\)", "pmax_w")
    r_voc  = assign(r"^Open Circuit Voltage\(Voc/V\)", "voc_v")
    r_isc  = assign(r"^Short Circuit Current\(Isc/A\)", "isc_a")
    r_vmp  = assign(r"^Operating Voltage\(Vmp/V\)", "vmp_v")
    r_imp  = assign(r"^Operating Current\(Imp/A\)", "imp_a")

    # Temperature coefficients + NMOT value on the right side (parse from full block)
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
    blob = "\n".join(rows)
    out: Dict[str, Any] = {}

    m = re.search(r"Max\.?\s*System Voltage\s*DC\s*(\d{3,5})\s*V", blob, re.IGNORECASE)
    if m:
        out["max_system_voltage_v"] = int(m.group(1))

    m = re.search(r"Power Tolerance\s*([0-9]+\s*~\s*\+\s*[0-9]+)\s*W", blob, re.IGNORECASE)
    if m:
        out["power_tolerance_w"] = m.group(1).replace(" ", "")

    m = re.search(r"Operating Temperature\s*(-?\d+)\s*°C\s*~\s*\+?(\d+)\s*°C", blob, re.IGNORECASE)
    if m:
        out["operating_temp_c"] = {"min": int(m.group(1)), "max": int(m.group(2))}

    m = re.search(r"Max\.?\s*Fuse Rated Current\s*(\d{1,3})\s*A", blob, re.IGNORECASE)
    if m:
        out["max_fuse_a"] = int(m.group(1))

    m = re.search(r"Bifaciality\s*(\d+)\s*%\s*±\s*(\d+)\s*%", blob, re.IGNORECASE)
    if m:
        out["bifaciality_pct"] = float(m.group(1))
        out["bifaciality_tol_pct"] = float(m.group(2))

    m = re.search(r"Static Load\s*Front\s*(\d+)\s*Pa,\s*Back\s*(\d+)\s*Pa", blob, re.IGNORECASE)
    if m:
        out["static_load_pa"] = {"front": int(m.group(1)), "back": int(m.group(2))}

    m = re.search(r"Packing Data\s*(.+)$", blob, re.IGNORECASE | re.MULTILINE)
    if m:
        out["packing_data"] = m.group(1).strip()

    return out


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

def _validate_physics(stc_by_power: Dict[str, Dict[str, float]], nmot_by_power: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    rep: Dict[str, Any] = {"stc": {}, "nmot": {}, "warnings": []}

    def check(name: str, block: Dict[str, Dict[str, float]]) -> None:
        for p, d in block.items():
            pmax = d.get("pmax_w")
            vmp = d.get("vmp_v")
            imp = d.get("imp_a")
            if pmax is None or vmp is None or imp is None:
                rep[name][p] = {"status": "missing", "pmax_w": pmax, "vmp_v": vmp, "imp_a": imp}
                continue
            p_est = vmp * imp
            rel = (p_est - pmax) / pmax if pmax else None
            ok = (rel is not None) and (abs(rel) <= 0.05)
            rep[name][p] = {
                "status": "ok" if ok else "check",
                "pmax_w": float(pmax),
                "vmp_v": float(vmp),
                "imp_a": float(imp),
                "p_est_w": float(p_est),
                "rel_err": float(rel) if rel is not None else None,
            }
            if not ok and rel is not None:
                rep["warnings"].append(f"[{name.upper()}] {p}W: Pmax={pmax:.2f} vs Vmp*Imp={p_est:.2f} (rel={rel:+.2%})")

    check("stc", stc_by_power)
    check("nmot", nmot_by_power)
    return rep


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def read_das_datasheet(pdf_path: str) -> Dict[str, Any]:
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

    idx_stc = _find_row_idx(rows, r"Electrical Parameters\s*\(STC")
    if idx_stc is None:
        idx_stc = _find_row_idx(rows, r"Nominal Max\. Power\(Pmax/W\)\s+575\s+580")

    idx_stc_tbl = _find_row_idx(rows, r"Nominal Max\. Power\(Pmax/W\)\s+575")
    if idx_stc_tbl is None:
        idx_stc_tbl = idx_stc if idx_stc is not None else 0

    stc_by_power, mechanical, powers = _parse_stc_block(rows, idx_stc_tbl)

    nmot_candidates = [i for i, r in enumerate(rows) if "Nominal Max. Power(Pmax/W)" in r]
    idx_nmot_tbl = None
    if nmot_candidates:
        for i in nmot_candidates:
            if i > idx_stc_tbl + 2:
                if re.search(r"\b43\d\b|\b44\d\b|\b45\d\b", rows[i]):
                    idx_nmot_tbl = i
                    break

    nmot_by_power: Dict[str, Dict[str, float]] = {}
    temperature: Dict[str, Any] = {}
    if idx_nmot_tbl is not None and powers:
        nmot_by_power, temperature = _parse_nmot_and_temp_block(rows, idx_nmot_tbl, powers)

    operating = _parse_ratings_block(rows)

    models = _build_models(family, powers)

    validation = _validate_physics(stc_by_power, nmot_by_power)

    out: Dict[str, Any] = {
        "source_pdf": str(pdf_path),
        "reader": "das_pdf_v1",
        "technical_page_used": tech_page,
        "identification": {
            "manufacturer": "DAS Solar",
            "family": family,
            "power_range_w": {"min": power_range[0], "max": power_range[1]} if power_range else None,
            "powers_w": powers,
            "models": models,
        },
        "mechanical": mechanical,
        "operating": operating,
        "temperature": temperature,
        "electrical": {
            "stc_by_power": stc_by_power,
            "nmot_by_power": nmot_by_power,
        },
        "validation": validation,
    }

    def prune(x: Any) -> Any:
        if isinstance(x, dict):
            dd = {k: prune(v) for k, v in x.items()}
            return {k: v for k, v in dd.items() if v not in (None, "", {}, [], [""])}
        if isinstance(x, list):
            ll = [prune(v) for v in x]
            return [v for v in ll if v not in (None, "", {}, [], [""])]
        return x

    return prune(out)


# -----------------------------------------------------------------------------
# Console report
# -----------------------------------------------------------------------------

def print_das_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("DAS SOLAR DATASHEET READER — CONSOLE REPORT (ALL MODELS)")
    print("=" * 110)
    print(f"PDF: {data.get('source_pdf')}")
    print(f"Technical page used: {data.get('technical_page_used')}")
    print("-" * 110)

    ident = data.get("identification", {})
    print("[IDENTIFICATION]")
    print(f"  - manufacturer: {ident.get('manufacturer')}")
    print(f"  - family: {ident.get('family')}")
    pr = ident.get("power_range_w")
    if pr:
        print(f"  - power range: {pr.get('min')}–{pr.get('max')} W")
    print(f"  - powers: {ident.get('powers_w')}")
    models = ident.get("models", []) or []
    print(f"  - models ({len(models)}):")
    for m in models:
        print(f"      • {m}")

    mech = data.get("mechanical", {})
    if mech:
        print("\n[MECHANICAL]")
        for k, v in mech.items():
            print(f"  - {k}: {v}")

    op = data.get("operating", {})
    if op:
        print("\n[OPERATING / RATINGS]")
        for k, v in op.items():
            print(f"  - {k}: {v}")

    temp = data.get("temperature", {})
    print("\n[TEMPERATURE]")
    if temp:
        for k, v in temp.items():
            print(f"  - {k}: {v}")
    else:
        print("  - (not found)")

    elec = data.get("electrical", {})
    stc = elec.get("stc_by_power", {}) or {}
    nmot = elec.get("nmot_by_power", {}) or {}

    def fmt(v: Any) -> str:
        return "-" if v is None else str(v)

    print("\n[ELECTRICAL — STC (ALL POWERS)]")
    for p in ident.get("powers_w", []) or []:
        d = stc.get(str(p), {})
        if not d:
            print(f"  - {p} W: (not parsed)")
            continue
        print(
            f"  - {p} W: Voc={fmt(d.get('voc_v'))} V | Isc={fmt(d.get('isc_a'))} A | "
            f"Vmp={fmt(d.get('vmp_v'))} V | Imp={fmt(d.get('imp_a'))} A | Eff={fmt(d.get('eff_pct'))} %"
        )

    print("\n[ELECTRICAL — NMOT (ALL POWERS)]")
    if nmot:
        for p in ident.get("powers_w", []) or []:
            d = nmot.get(str(p), {})
            if not d:
                print(f"  - {p} W: (not parsed)")
                continue
            print(
                f"  - {p} W: Pmax={fmt(d.get('pmax_w'))} W | Voc={fmt(d.get('voc_v'))} V | Isc={fmt(d.get('isc_a'))} A | "
                f"Vmp={fmt(d.get('vmp_v'))} V | Imp={fmt(d.get('imp_a'))} A"
            )
    else:
        print("  - (not found)")

    val = data.get("validation", {})
    if val:
        print("\n[VALIDATION: Pmax ≈ Vmp×Imp]")
        for name in ("stc", "nmot"):
            block = val.get(name, {}) or {}
            print(f"  {name.upper()}:")
            for p in ident.get("powers_w", []) or []:
                r = block.get(str(p), {})
                status = r.get("status", "missing")
                rel = r.get("rel_err")
                if rel is None:
                    print(f"    - {p} W: {status}")
                else:
                    print(f"    - {p} W: {status} (rel_err={rel:+.2%})")

        warns = val.get("warnings", []) or []
        if warns:
            print("\n  WARNINGS:")
            for w in warns:
                print(f"   - {w}")

    print("\n" + "=" * 110)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="DAS Solar datasheet reader (specialized)")
    ap.add_argument("pdf", help="Path to DAS datasheet PDF")
    ap.add_argument("--json", dest="json_out", help="Optional JSON output path")
    args = ap.parse_args()

    data = read_das_datasheet(args.pdf)
    print_das_report(data)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved JSON: {args.json_out}")


if __name__ == "__main__":
    main()
