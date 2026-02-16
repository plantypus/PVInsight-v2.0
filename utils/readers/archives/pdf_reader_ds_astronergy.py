from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# ASTRONERGY (CHINT) DATASHEET READER — specialized
# Target PDF example:
#   (600~620)ASTRO N7_CHSM66RN(DG)F-BH_2382x1134x30_Europe_20240312.pdf
#
# Parsing strategy (v1):
# - Find technical page (usually page 2) by keyword scoring
# - Prefer page.extract_text() (Astronergy tables are text-friendly here)
# - Parse:
#   * Electrical STC table (600/605/610/615/620)
#   * Electrical NMOT table
#   * Temperature ratings + operating parameters
#   * Mechanical specifications
#   * (Optional) Rear power gain table (Integrated power)
# - Physical validation: Pmpp ≈ Vmpp * Impp (STC & NMOT)
# - Console prints ALL models (by power)
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
    x = x.strip().replace(",", ".")
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

def _find_all_starts(lines: List[str]) -> List[int]:
    """Return indices of lines that start the electrical table (Rated output...)."""
    out = []
    for i, l in enumerate(lines):
        if re.search(r"Rated output\s*\(Pmpp\s*/\s*Wp\)", l, re.IGNORECASE):
            out.append(i)
    return out


def _parse_stc_table(lines: List[str]) -> Tuple[Dict[str, Dict[str, float]], List[int], Optional[int]]:
    """
    STC table: header line contains the power columns (600..620).
    Returns (stc_by_power, powers, start_idx).
    """
    starts = _find_all_starts(lines)
    for start in starts:
        powers = _extract_powers_from_header(lines[start])
        if len(powers) >= 3:  # STC header has powers
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

                # Pmpp line includes power header numbers: remove them
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


def _parse_nmot_table_using_powers(lines: List[str], powers: List[int], after_idx: int) -> Tuple[Dict[str, Dict[str, float]], Optional[int]]:
    """
    NMOT table: header line does NOT contain powers (it contains NMOT Pmpp values).
    We map the 5 values by index onto the STC powers.
    Returns (nmot_by_power, start_idx).
    """
    starts = _find_all_starts(lines)
    # choose the first start strictly after STC start (or after_idx)
    start = None
    for s in starts:
        if s is not None and s > after_idx:
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
        # NMOT rows are purely values (no powers to strip)
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
# Table parsing helpers (row-based, 5 columns)
# -----------------------------------------------------------------------------

def _extract_powers_from_header(line: str) -> List[int]:
    # Expect: 600 605 610 615 620
    nums = [int(x) for x in re.findall(r"\b(\d{3})\b", line)]
    out: List[int] = []
    for n in nums:
        if 300 <= n <= 800 and n not in out:
            out.append(n)
    # keep only if it looks like a power header
    return out


def _extract_row_values(line: str) -> List[float]:
    vals: List[float] = []
    for n in re.findall(r"[-+]?\d+(?:\.\d+)?", line):
        f = _to_float(n)
        if f is not None:
            vals.append(f)
    return vals


def _parse_electrical_table_by_occurrence(lines: List[str], occurrence: int = 1) -> Tuple[Dict[str, Dict[str, float]], List[int]]:
    """
    Parse an electrical table (STC or NMOT) by taking the Nth occurrence of the header row:
      Rated output (Pmpp / Wp) 600 605 610 615 620
    occurrence=1 -> STC table
    occurrence=2 -> NMOT table
    """
    # find all header rows
    headers = []
    for i, l in enumerate(lines):
        if re.search(r"Rated output\s*\(Pmpp\s*/\s*Wp\)", l, re.IGNORECASE):
            # must contain the power columns
            if len(_extract_powers_from_header(l)) >= 3:
                headers.append(i)

    if len(headers) < occurrence:
        return {}, []

    start = headers[occurrence - 1]
    header = lines[start]
    powers = _extract_powers_from_header(header)
    if len(powers) < 3:
        return {}, []

    out: Dict[str, Dict[str, float]] = {str(p): {} for p in powers}

    def take_row(pat: str, key: str, idx_hint: int) -> None:
        row = None
        # search near expected row position
        for k in range(start + idx_hint - 1, start + idx_hint + 2):
            if 0 <= k < len(lines) and re.search(pat, lines[k], re.IGNORECASE):
                row = lines[k]
                break
        # fallback: scan forward
        if row is None:
            for k in range(start, min(start + 20, len(lines))):
                if re.search(pat, lines[k], re.IGNORECASE):
                    row = lines[k]
                    break
        if row is None:
            return

        vals = _extract_row_values(row)

        # Pmpp row includes the power header numbers: remove them
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
                out[str(p)][key] = float(vals[i_p])

    take_row(r"Rated output\s*\(Pmpp\s*/\s*Wp\)", "pmax_w", 0)
    take_row(r"Rated voltage\s*\(Vmpp\s*/\s*V\)", "vmp_v", 1)
    take_row(r"Rated current\s*\(Impp\s*/\s*A\)", "imp_a", 2)
    take_row(r"Open circuit voltage\s*\(Voc\s*/\s*V\)", "voc_v", 3)
    take_row(r"Short circuit current\s*\(Isc\s*/\s*A\)", "isc_a", 4)
    take_row(r"Module efficiency", "eff_pct", 5)

    out = {p: d for p, d in out.items() if d}
    return out, powers


# -----------------------------------------------------------------------------
# Other sections parsing
# -----------------------------------------------------------------------------

def _parse_temperature_and_operating(lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Parse Temperature Ratings (STC) and Operating Parameters.
    """
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

    m = re.search(r"Max\.\s*system\s*voltage\s*\(IEC/UL\)\s*(\d+)\s*VDC", blob, re.IGNORECASE)
    if m:
        operating["max_system_voltage_vdc"] = int(m.group(1))

    m = re.search(r"No\.\s*of\s*diodes\s*(\d+)", blob, re.IGNORECASE)
    if m:
        operating["diodes_count"] = int(m.group(1))

    m = re.search(r"Junction\s*box\s*IP\s*rating\s*IP\s*([0-9A-Za-z]+)", blob, re.IGNORECASE)
    if m:
        operating["junction_box_ip"] = m.group(1)

    return temperature, operating


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

    m = re.search(r"Frame technology\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["frame_technology"] = m.group(1).strip()

    m = re.search(r"Front\s*/\s*Back\s*glass\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["glass"] = m.group(1).strip()

    m = re.search(r"Cable length\s*\(Including connector\)\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["cable_length_raw"] = m.group(1).strip()

    m = re.search(r"Cable diameter\s*\(IEC/UL\)\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["cable_diameter"] = m.group(1).strip()

    m = re.search(r"Connector type\s*\(IEC/UL\)\s*([^\n]+)", blob, re.IGNORECASE)
    if m:
        mech["connector_type"] = m.group(1).strip()

    m = re.search(r"Module weight\s*([0-9.]+)\s*kg", blob, re.IGNORECASE)
    if m:
        mech["weight_kg"] = _to_float(m.group(1))

    m = re.search(r"Packing unit\s*([0-9]+)\s*pcs\s*/\s*box", blob, re.IGNORECASE)
    if m:
        mech["packing_unit_pcs_per_box"] = int(m.group(1))

    m = re.search(r"Modules per 40'\s*HQ\s*container\s*([0-9]+)\s*pcs", blob, re.IGNORECASE)
    if m:
        mech["modules_per_40hq"] = int(m.group(1))

    # Mechanical test load (if present as sentence)
    m = re.search(r"Maximum mechanical test load\s*([0-9]+)\s*Pa\s*\(front\)\s*/\s*([0-9]+)\s*Pa\s*\(back\)", blob, re.IGNORECASE)
    if m:
        mech["mechanical_test_load_pa"] = {"front": int(m.group(1)), "back": int(m.group(2))}

    return {k: v for k, v in mech.items() if v not in (None, "", {}, [])}


def _parse_identification(page1_text: str, page2_text: str, powers: List[int]) -> Dict[str, Any]:
    t1 = _norm(page1_text)
    t2 = _norm(page2_text)
    ident: Dict[str, Any] = {"manufacturer": "Astronergy (CHINT)"}

    # Family/model line
    m = re.search(r"\bCHSM[0-9A-Z\(\)\-/]+", t1)
    if not m:
        m = re.search(r"\bCHSM[0-9A-Z\(\)\-/]+", t2)
    if m:
        ident["family"] = m.group(0)

    # Series / marketing name
    if re.search(r"\bASTRO\s*N7\b", t1, re.IGNORECASE):
        ident["series"] = "ASTRO N7"

    # Power range
    m = re.search(r"\b(\d{3})\s*~\s*(\d{3})W\b", t1)
    if m:
        ident["power_range_w"] = {"min": int(m.group(1)), "max": int(m.group(2))}
    else:
        # fallback from page2 header line
        m = re.search(r"\b(\d{3})~(\d{3})W\b", t2)
        if m:
            ident["power_range_w"] = {"min": int(m.group(1)), "max": int(m.group(2))}

    ident["powers_w"] = powers
    if ident.get("family") and powers:
        ident["models"] = [f"{ident['family']}-{p}" for p in powers]
    else:
        ident["models"] = [str(p) for p in powers] if powers else []

    return ident


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

def _validate_physics(block_by_power: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    rep: Dict[str, Any] = {"by_power": {}, "warnings": []}
    for p, d in block_by_power.items():
        pmax = d.get("pmax_w")
        vmp = d.get("vmp_v")
        imp = d.get("imp_a")
        if pmax is None or vmp is None or imp is None:
            rep["by_power"][p] = {"status": "missing"}
            continue
        p_est = vmp * imp
        rel = (p_est - pmax) / pmax if pmax else None
        ok = (rel is not None) and (abs(rel) <= 0.05)
        rep["by_power"][p] = {
            "status": "ok" if ok else "check",
            "pmax_w": float(pmax),
            "vmp_v": float(vmp),
            "imp_a": float(imp),
            "p_est_w": float(p_est),
            "rel_err": float(rel) if rel is not None else None,
        }
        if not ok and rel is not None:
            rep["warnings"].append(f"[{p}W] Pmpp={pmax:.2f} vs Vmpp*Impp={p_est:.2f} (rel={rel:+.2%})")
    return rep


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

    # Parse STC + NMOT
    stc_by_power, powers, stc_start = _parse_stc_table(lines)
    nmot_by_power = {}

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

    out: Dict[str, Any] = {
        "source_pdf": str(pdf_path),
        "reader": "astronergy_pdf_v1",
        "technical_page_used": tech_page,
        "identification": ident,
        "mechanical": mechanical,
        "temperature": temperature,
        "operating": operating,
        "electrical": {
            "stc_by_power": stc_by_power,
            "nmot_by_power": nmot_by_power,
        },
        "validation": {
            "stc": _validate_physics(stc_by_power) if stc_by_power else {},
            "nmot": _validate_physics(nmot_by_power) if nmot_by_power else {},
        },
    }

    # prune empties
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

def print_astronergy_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("ASTRONERGY (CHINT) DATASHEET READER — CONSOLE REPORT (ALL MODELS)")
    print("=" * 110)
    print(f"PDF: {data.get('source_pdf')}")
    print(f"Technical page used: {data.get('technical_page_used')}")
    print("-" * 110)

    ident = data.get("identification", {}) or {}
    models = ident.get("models", []) or []
    print("[IDENTIFICATION]")
    for k in ("manufacturer", "series", "family", "power_range_w"):
        if ident.get(k) is not None:
            print(f"  - {k}: {ident.get(k)}")
    print(f"  - powers_w: {ident.get('powers_w')}")
    print(f"  - models ({len(models)}):")
    for m in models:
        print(f"      • {m}")

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

    elec = data.get("electrical", {}) or {}
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
            f"  - {p} W: Vmpp={fmt(d.get('vmp_v'))} V | Impp={fmt(d.get('imp_a'))} A | "
            f"Voc={fmt(d.get('voc_v'))} V | Isc={fmt(d.get('isc_a'))} A | Eff={fmt(d.get('eff_pct'))} %"
        )

    print("\n[ELECTRICAL — NMOT (ALL POWERS)]")
    if nmot:
        for p in ident.get("powers_w", []) or []:
            d = nmot.get(str(p), {})
            if not d:
                print(f"  - {p} W: (not parsed)")
                continue
            print(
                f"  - {p} W: Pmpp={fmt(d.get('pmax_w'))} W | Vmpp={fmt(d.get('vmp_v'))} V | Impp={fmt(d.get('imp_a'))} A | "
                f"Voc={fmt(d.get('voc_v'))} V | Isc={fmt(d.get('isc_a'))} A"
            )
    else:
        print("  - (not found)")

    val = data.get("validation", {}) or {}
    for name in ("stc", "nmot"):
        vv = val.get(name, {}) or {}
        warns = vv.get("warnings", []) or []
        if warns:
            print(f"\n[VALIDATION WARNINGS — {name.upper()}]")
            for w in warns:
                print(f"  - {w}")

    print("\n" + "=" * 110)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Astronergy datasheet reader (specialized)")
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
