# utils/readers/pdf_reader_ds_dmegc.py
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


# =============================================================================
# DMEGC DATASHEET READER — v1.1
# - Specialized for DMEGC layout where STC/NMOT values are paired in one table.
# - Adds:
#   * physical validation (Pmax ≈ Vmp*Imp)
#   * console print shows ALL models (STC + NMOT)
# =============================================================================


# ---------------------------- PDF text extraction -----------------------------

def extract_pages_text(pdf_path: str) -> List[str]:
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(pdf_path)

    try:
        import pdfplumber  # type: ignore
        pages: List[str] = []
        with pdfplumber.open(str(p)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        if any(t.strip() for t in pages):
            return pages
    except Exception:
        pass

    try:
        import fitz  # type: ignore
        doc = fitz.open(str(p))
        pages = [page.get_text("text") or "" for page in doc]
        doc.close()
        return pages
    except Exception as e:
        raise RuntimeError(
            "No PDF text extractor available. Install pdfplumber (recommended) or pymupdf."
        ) from e


# ------------------------------- Normalization -------------------------------

def normalize_text(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = s.replace("℃", "°C").replace("º", "°")
    s = s.replace("deg.C", "°C").replace("degC", "°C").replace("DEG.C", "°C")
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+\n", "\n", s)
    return s.strip()


def to_float(x: str) -> Optional[float]:
    x = x.strip().replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", x):
        return None
    try:
        return float(x)
    except Exception:
        return None


def split_lines(text: str) -> List[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]


def find_best_technical_page(pages: List[str]) -> Tuple[int, str]:
    best_idx = 0
    best_score = -1
    for i, raw in enumerate(pages):
        t = normalize_text(raw)
        score = 0
        score += 3 if re.search(r"Electrical Specifications", t, re.IGNORECASE) else 0
        score += 2 if re.search(r"\bModule Specification\b", t, re.IGNORECASE) else 0
        score += 2 if re.search(r"\bSTC\b", t) else 0
        score += 2 if re.search(r"\bNMOT\b|\bNOCT\b", t) else 0
        score += 2 if re.search(r"Temperature Characteristics", t, re.IGNORECASE) else 0
        score += 1 if re.search(r"\bVoc\b|\bIsc\b|\bVmp\b|\bImp\b", t) else 0
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx + 1, normalize_text(pages[best_idx])


# ------------------------------ DMEGC parsing -------------------------------

def find_line_index(lines: List[str], pattern: str) -> Optional[int]:
    for i, l in enumerate(lines):
        if re.search(pattern, l, re.IGNORECASE):
            return i
    return None


def clamp_line_value(line: str, label_pattern: str) -> Optional[str]:
    """
    Return the text after the label, but only on the same line (prevents capturing whole PDF).
    """
    m = re.search(label_pattern + r"\s*[: ]*\s*([^\n\r]+)$", line, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


def extract_module_spec(lines: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    i0 = find_line_index(lines, r"\bModule Specification\b")
    if i0 is None:
        return out

    i1rel = find_line_index(lines[i0:], r"\bElectrical Specifications\b")
    end = i0 + i1rel if i1rel is not None else min(i0 + 40, len(lines))
    block = lines[i0:end]

    for l in block:
        v = clamp_line_value(l, r"\bCell Type\b")
        if v:
            out["cell_type_raw"] = v

        v = clamp_line_value(l, r"\bDimensions\b")
        if v:
            m = re.search(r"(\d{3,5})\s*[*x×]\s*(\d{3,5})\s*[*x×]\s*(\d{1,4})", v)
            if m:
                out["dimensions_mm"] = {"length": int(m.group(1)), "width": int(m.group(2)), "thickness": int(m.group(3))}
            else:
                out["dimensions_raw"] = v

        v = clamp_line_value(l, r"\bWeight\b")
        if v:
            m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", v)
            out["weight_kg"] = to_float(m.group(1)) if m else v

        v = clamp_line_value(l, r"\bJunction Box\b")
        if v:
            out["junction_box"] = v

        v = clamp_line_value(l, r"\bCables\b")
        if v:
            out["cables"] = v

        v = clamp_line_value(l, r"\bConnector\b(?:\s*Type)?\b")
        if v:
            out["connector"] = v

    return out


def parse_dmegc_electrical_table(lines: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"models": [], "stc_by_model": {}, "nmot_by_model": {}}

    idx = find_line_index(lines, r"^\s*Module Type\b")
    if idx is None:
        idx = find_line_index(lines, r"\bModule Type\b.*\bDM\d{3}")
    if idx is None:
        return out

    header = lines[idx]
    models = re.findall(r"\bDM\d{3}[A-Z0-9\-]+", header)
    if len(models) < 3:
        return out

    out["models"] = models
    out["stc_by_model"] = {m: {} for m in models}
    out["nmot_by_model"] = {m: {} for m in models}

    def assign_pairs(key: str, nums: List[float]) -> None:
        n = len(models)
        if len(nums) < 2 * n:
            return
        nums = nums[-2 * n:]
        for i, m in enumerate(models):
            out["stc_by_model"][m][key] = float(nums[2 * i])
            out["nmot_by_model"][m][key] = float(nums[2 * i + 1])

    stop_patterns = [
        r"Measurements according",
        r"Electrical Specifications.*BNPI",
        r"Operating Conditions",
        r"Temperature Characteristics",
    ]

    row_map = {
        "pmax_w": r"Maximum Power\s*\(Pmax/W\)",
        "imp_a": r"Maximum Power Current\s*\(Imp/A\)",
        "vmp_v": r"Maximum Power Voltage\s*\(Vmp/V\)",
        "isc_a": r"Short-?circuit Current\s*\(Isc/A\)",
        "voc_v": r"Open-?circuit Voltage\s*\(Voc/V\)",
        "eff_pct": r"Module Efficiency.*\(%\)",
    }

    for l in lines[idx + 1 : idx + 70]:
        if any(re.search(p, l, re.IGNORECASE) for p in stop_patterns):
            break

        # Efficiency: STC only
        if re.search(row_map["eff_pct"], l, re.IGNORECASE):
            nums = [to_float(x) for x in re.findall(r"[-+]?\d+(?:[.,]\d+)?", l)]
            nums = [x for x in nums if x is not None]
            if len(nums) >= len(models):
                nums = nums[-len(models):]
                for m, v in zip(models, nums):
                    out["stc_by_model"][m]["eff_pct"] = float(v)
            continue

        for key, pat in row_map.items():
            if key == "eff_pct":
                continue
            if re.search(pat, l, re.IGNORECASE):
                nums = [to_float(x) for x in re.findall(r"[-+]?\d+(?:[.,]\d+)?", l)]
                nums = [x for x in nums if x is not None]
                assign_pairs(key, nums)
                break

    out["stc_by_model"] = {m: d for m, d in out["stc_by_model"].items() if d}
    out["nmot_by_model"] = {m: d for m, d in out["nmot_by_model"].items() if d}
    return out


def parse_operating_conditions(lines: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    idx = find_line_index(lines, r"\bOperating Conditions\b")
    if idx is None:
        return out

    block = lines[idx : idx + 30]
    for l in block:
        m = re.search(r"Operating Temperature.*?([-+0-9]+)\s*(?:to|~)\s*([+0-9]+)", l, re.IGNORECASE)
        if m:
            out["operating_temp_c"] = {"min": int(m.group(1)), "max": int(m.group(2))}

        m = re.search(r"Maximum System Voltage.*?(\d{3,5})", l, re.IGNORECASE)
        if m:
            out["max_system_voltage_v"] = int(m.group(1))

        m = re.search(r"Overcurrent Protection Rating.*?(\d{1,3})\s*A", l, re.IGNORECASE)
        if m:
            out["overcurrent_protection_a"] = int(m.group(1))

        m = re.search(r"Power Output Tolerance.*?([0-9]+\s*~\s*[0-9]+)", l, re.IGNORECASE)
        if m:
            out["power_tolerance_pct"] = m.group(1).replace(" ", "")

        m = re.search(r"Protection Class\s*(.+)$", l, re.IGNORECASE)
        if m:
            out["protection_class"] = m.group(1).strip()

        m = re.search(r"Max\. Test Load.*?Front\s*(\d+)\s*/\s*Back\s*(\d+)", l, re.IGNORECASE)
        if m:
            out["max_test_load_pa"] = {"front": int(m.group(1)), "back": int(m.group(2))}

        m = re.search(r"Max\. Design Load.*?Front\s*(\d+)\s*/\s*Back\s*(\d+)", l, re.IGNORECASE)
        if m:
            out["max_design_load_pa"] = {"front": int(m.group(1)), "back": int(m.group(2))}

    return out


def parse_temperature_characteristics(lines: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    idx = find_line_index(lines, r"\bTemperature Characteristics\b")
    if idx is None:
        return out

    block = lines[idx : idx + 20]
    for l in block:
        m = re.search(r"Nominal Module Operating Temperature\s*\(NMOT\)\s*([0-9]+)\s*±\s*([0-9]+)", l, re.IGNORECASE)
        if m:
            out["nmot_c"] = int(m.group(1))
            out["nmot_tol_c"] = int(m.group(2))

        m = re.search(r"Temperature Coefficient(?:s)? of Pmax.*?([-+0-9.,]+)", l, re.IGNORECASE)
        if m:
            out["coeff_pmax_pct_per_c"] = to_float(m.group(1))

        m = re.search(r"Temperature Coefficient(?:s)? of Voc.*?([-+0-9.,]+)", l, re.IGNORECASE)
        if m:
            out["coeff_voc_pct_per_c"] = to_float(m.group(1))

        m = re.search(r"Temperature Coefficient(?:s)? of Isc.*?([-+0-9.,]+)", l, re.IGNORECASE)
        if m:
            out["coeff_isc_pct_per_c"] = to_float(m.group(1))

    return {k: v for k, v in out.items() if v is not None}


# ------------------------------ Physical validation ------------------------------

def validate_physics(stc_by_model: Dict[str, Dict[str, float]],
                     nmot_by_model: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Validation: Pmax ≈ Vmp * Imp
    Returns a report per model (STC and NMOT), with relative error.
    """
    report: Dict[str, Any] = {"stc": {}, "nmot": {}, "warnings": []}

    def check_block(name: str, block: Dict[str, Dict[str, float]]) -> None:
        for model, d in block.items():
            p = d.get("pmax_w")
            vmp = d.get("vmp_v")
            imp = d.get("imp_a")
            if p is None or vmp is None or imp is None:
                report[name][model] = {"status": "missing", "pmax_w": p, "vmp_v": vmp, "imp_a": imp}
                continue
            p_est = vmp * imp
            rel_err = (p_est - p) / p if p != 0 else None
            ok = (rel_err is not None) and (abs(rel_err) <= 0.05)  # ±5%
            report[name][model] = {
                "status": "ok" if ok else "check",
                "pmax_w": float(p),
                "vmp_v": float(vmp),
                "imp_a": float(imp),
                "p_est_w": float(p_est),
                "rel_err": float(rel_err) if rel_err is not None else None,
            }
            if not ok:
                report["warnings"].append(
                    f"[{name.upper()}] {model}: Pmax={p:.2f}W vs Vmp*Imp={p_est:.2f}W (rel_err={rel_err:+.2%})"
                )

    check_block("stc", stc_by_model)
    check_block("nmot", nmot_by_model)
    return report


# ------------------------------- Public API ---------------------------------

def read_dmegc_datasheet(pdf_path: str) -> Dict[str, Any]:
    pages_raw = extract_pages_text(pdf_path)
    pages = [normalize_text(p) for p in pages_raw]

    tech_page_no, tech_text = find_best_technical_page(pages)
    lines = split_lines(tech_text)

    module_spec = extract_module_spec(lines)
    electrical = parse_dmegc_electrical_table(lines)
    operating = parse_operating_conditions(lines)
    temperature = parse_temperature_characteristics(lines)

    stc_by_model = electrical.get("stc_by_model", {}) or {}
    nmot_by_model = electrical.get("nmot_by_model", {}) or {}

    validation = validate_physics(stc_by_model, nmot_by_model)

    out: Dict[str, Any] = {
        "source_pdf": str(pdf_path),
        "reader": "dmegc_v1_1",
        "technical_page_used": tech_page_no,
        "identification": {
            "manufacturer": "DMEGC",
            "models": electrical.get("models", []),
        },
        "module_spec": module_spec,
        "electrical": {
            "stc_by_model": stc_by_model,
            "nmot_by_model": nmot_by_model,
        },
        "operating": operating,
        "temperature": temperature,
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


# ------------------------------ Console output ------------------------------

def print_dmegc_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("DMEGC DATASHEET READER v1.1 — CONSOLE REPORT (ALL MODELS)")
    print("=" * 110)
    print(f"PDF: {data.get('source_pdf')}")
    print(f"Technical page used: {data.get('technical_page_used')}")
    print("-" * 110)

    ident = data.get("identification", {})
    models: List[str] = ident.get("models", []) or []
    print("[IDENTIFICATION]")
    print(f"  - manufacturer: {ident.get('manufacturer')}")
    print(f"  - models ({len(models)}):")
    for m in models:
        print(f"      • {m}")

    ms = data.get("module_spec", {})
    if ms:
        print("\n[MODULE SPEC]")
        for k, v in ms.items():
            print(f"  - {k}: {v}")

    op = data.get("operating", {})
    if op:
        print("\n[OPERATING CONDITIONS]")
        for k, v in op.items():
            print(f"  - {k}: {v}")

    temp = data.get("temperature", {})
    print("\n[TEMPERATURE CHARACTERISTICS]")
    if temp:
        for k, v in temp.items():
            print(f"  - {k}: {v}")
    else:
        print("  - (not found)")

    elec = data.get("electrical", {})
    stc = elec.get("stc_by_model", {}) or {}
    nmot = elec.get("nmot_by_model", {}) or {}

    def fmt(v: Any) -> str:
        return "-" if v is None else str(v)

    if stc:
        print("\n[ELECTRICAL — STC (ALL MODELS)]")
        for m in models:
            d = stc.get(m, {})
            print(
                f"  - {m}: Pmax={fmt(d.get('pmax_w'))} W | Voc={fmt(d.get('voc_v'))} V | Isc={fmt(d.get('isc_a'))} A | "
                f"Vmp={fmt(d.get('vmp_v'))} V | Imp={fmt(d.get('imp_a'))} A | Eff={fmt(d.get('eff_pct'))} %"
            )
    else:
        print("\n[ELECTRICAL — STC]\n  - (not found)")

    if nmot:
        print("\n[ELECTRICAL — NMOT (ALL MODELS)]")
        for m in models:
            d = nmot.get(m, {})
            print(
                f"  - {m}: Pmax={fmt(d.get('pmax_w'))} W | Voc={fmt(d.get('voc_v'))} V | Isc={fmt(d.get('isc_a'))} A | "
                f"Vmp={fmt(d.get('vmp_v'))} V | Imp={fmt(d.get('imp_a'))} A"
            )
    else:
        print("\n[ELECTRICAL — NMOT]\n  - (not found)")

    val = data.get("validation", {})
    if val:
        print("\n[PHYSICAL VALIDATION: Pmax ≈ Vmp×Imp]")
        # print per model for STC and NMOT
        stc_r = val.get("stc", {})
        nmot_r = val.get("nmot", {})

        print("  STC:")
        for m in models:
            r = stc_r.get(m, {})
            status = r.get("status", "missing")
            rel_err = r.get("rel_err")
            if rel_err is None:
                print(f"    - {m}: {status}")
            else:
                print(f"    - {m}: {status} (rel_err={rel_err:+.2%})")

        print("  NMOT:")
        for m in models:
            r = nmot_r.get(m, {})
            status = r.get("status", "missing")
            rel_err = r.get("rel_err")
            if rel_err is None:
                print(f"    - {m}: {status}")
            else:
                print(f"    - {m}: {status} (rel_err={rel_err:+.2%})")

        warns = val.get("warnings", [])
        if warns:
            print("\n  WARNINGS:")
            for w in warns:
                print(f"   - {w}")

    print("\n" + "=" * 110)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="DMEGC datasheet PDF reader v1.1 (specialized)")
    ap.add_argument("pdf", help="Path to DMEGC datasheet PDF")
    ap.add_argument("--json", dest="json_out", help="Optional JSON output path")
    args = ap.parse_args()

    data = read_dmegc_datasheet(args.pdf)
    print_dmegc_report(data)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved JSON: {args.json_out}")


if __name__ == "__main__":
    main()
