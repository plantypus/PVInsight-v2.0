# utils/readers/pdf_reader_ds_dmegc.py
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


# =============================================================================
# DMEGC DATASHEET READER — standardized output (PVInsight schema v1)
#
# Goal:
# - Keep the DMEGC-specific parsing logic (paired STC/NMOT table in one block),
# - BUT return a fully standardized dict that other modules can consume reliably.
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
# Naming normalization (consistent across suppliers):
# - STC block:      pmax_w, vmp_v, imp_a, voc_v, isc_a, eff_pct(optional)
# - NMOT block:     pmax_w, vmp_v, imp_a, voc_v, isc_a
# - temperature:    coeff_pmax_pct_per_c, coeff_voc_pct_per_c, coeff_isc_pct_per_c, nmot_c, nmot_tol_c
# - operating:      max_system_voltage_v, max_series_fuse_a, operating_temp_c{min,max}, power_tolerance_pct,
#                   junction_box_ip (optional), protection_class (optional)
# - mechanical:     dimensions_mm{length,width,thickness}, weight_kg, cell_type_raw, connector_type, output_cable_raw, junction_box_raw
#
# Console: prints ALL variants (STC + NMOT).
# =============================================================================


# -----------------------------------------------------------------------------
# PDF text extraction
# -----------------------------------------------------------------------------

def _extract_pages_text(pdf_path: str) -> List[str]:
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(pdf_path)

    # 1) pdfplumber (preferred)
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

    # 2) PyMuPDF fallback
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


# -----------------------------------------------------------------------------
# Normalization helpers
# -----------------------------------------------------------------------------

def _norm_text(s: str) -> str:
    s = (s or "").replace("\u00a0", " ")
    s = s.replace("℃", "°C").replace("º", "°")
    s = s.replace("deg.C", "°C").replace("degC", "°C").replace("DEG.C", "°C")
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+\n", "\n", s)
    return s.strip()


def _to_float(x: str) -> Optional[float]:
    x = (x or "").strip().replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", x):
        return None
    try:
        return float(x)
    except Exception:
        return None


def _split_lines(text: str) -> List[str]:
    return [l.strip() for l in (text or "").splitlines() if l.strip()]


def _find_best_technical_page(pages: List[str]) -> Tuple[int, str]:
    best_idx = 0
    best_score = -1
    for i, raw in enumerate(pages):
        t = _norm_text(raw)
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
    return best_idx + 1, _norm_text(pages[best_idx])


def _find_line_index(lines: List[str], pattern: str) -> Optional[int]:
    for i, l in enumerate(lines):
        if re.search(pattern, l, re.IGNORECASE):
            return i
    return None


def _clamp_line_value(line: str, label_pattern: str) -> Optional[str]:
    """
    Return the text after the label, but only on the same line.
    Prevents runaway capture across the full PDF.
    """
    m = re.search(label_pattern + r"\s*[: ]*\s*([^\n\r]+)$", line, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


# -----------------------------------------------------------------------------
# DMEGC parsing (supplier-specific)
# -----------------------------------------------------------------------------

def _extract_mechanical_from_module_spec(lines: List[str]) -> Dict[str, Any]:
    """
    Parses DMEGC 'Module Specification' block -> returns standardized mechanical keys.
    """
    out: Dict[str, Any] = {}
    i0 = _find_line_index(lines, r"\bModule Specification\b")
    if i0 is None:
        return out

    i1rel = _find_line_index(lines[i0:], r"\bElectrical Specifications\b")
    end = i0 + i1rel if i1rel is not None else min(i0 + 40, len(lines))
    block = lines[i0:end]

    for l in block:
        v = _clamp_line_value(l, r"\bCell Type\b")
        if v:
            out["cell_type_raw"] = v

        v = _clamp_line_value(l, r"\bDimensions\b")
        if v:
            m = re.search(r"(\d{3,5})\s*[*x×]\s*(\d{3,5})\s*[*x×]\s*(\d{1,4})", v)
            if m:
                out["dimensions_mm"] = {
                    "length": int(m.group(1)),
                    "width": int(m.group(2)),
                    "thickness": int(m.group(3)),
                }
            else:
                # keep raw if unparseable
                out["dimensions_raw"] = v

        v = _clamp_line_value(l, r"\bWeight\b")
        if v:
            m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", v)
            out["weight_kg"] = _to_float(m.group(1)) if m else None

        v = _clamp_line_value(l, r"\bJunction Box\b")
        if v:
            out["junction_box_raw"] = v

        v = _clamp_line_value(l, r"\bCables\b")
        if v:
            out["output_cable_raw"] = v

        v = _clamp_line_value(l, r"\bConnector\b(?:\s*Type)?\b")
        if v:
            out["connector_type"] = v

    # prune Nones and empties
    return {k: v for k, v in out.items() if v not in (None, "", {}, [])}


def _parse_dmegc_electrical_table(lines: List[str]) -> Dict[str, Any]:
    """
    DMEGC layout: header line contains multiple models and each subsequent row contains pairs:
      [STC value, NMOT value] repeated per model.
    Efficiency row is often STC only.
    """
    out: Dict[str, Any] = {"models": [], "stc_by_model": {}, "nmot_by_model": {}}

    idx = _find_line_index(lines, r"^\s*Module Type\b")
    if idx is None:
        idx = _find_line_index(lines, r"\bModule Type\b.*\bDM\d{3}")
    if idx is None:
        return out

    header = lines[idx]
    # Example models like: DM610-635G12RT-B66HSW-LRF ...
    models = re.findall(r"\bDM\d{3}[A-Z0-9\-]+", header)
    if len(models) < 2:
        return out

    out["models"] = models
    out["stc_by_model"] = {m: {} for m in models}
    out["nmot_by_model"] = {m: {} for m in models}

    def assign_pairs(key: str, nums: List[float]) -> None:
        n = len(models)
        if len(nums) < 2 * n:
            return
        nums = nums[-2 * n:]  # keep last pairs
        for i, m in enumerate(models):
            out["stc_by_model"][m][key] = float(nums[2 * i])
            out["nmot_by_model"][m][key] = float(nums[2 * i + 1])

    stop_patterns = [
        r"Measurements according",
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

    # scan a reasonable window after header
    for l in lines[idx + 1 : idx + 80]:
        if any(re.search(p, l, re.IGNORECASE) for p in stop_patterns):
            break

        # Efficiency: STC only
        if re.search(row_map["eff_pct"], l, re.IGNORECASE):
            nums = [_to_float(x) for x in re.findall(r"[-+]?\d+(?:[.,]\d+)?", l)]
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
                nums = [_to_float(x) for x in re.findall(r"[-+]?\d+(?:[.,]\d+)?", l)]
                nums = [x for x in nums if x is not None]
                assign_pairs(key, nums)
                break

    out["stc_by_model"] = {m: d for m, d in out["stc_by_model"].items() if d}
    out["nmot_by_model"] = {m: d for m, d in out["nmot_by_model"].items() if d}
    return out


def _parse_operating(lines: List[str]) -> Dict[str, Any]:
    """
    Standardized operating keys.
    Note: DMEGC uses "Overcurrent Protection Rating" -> map to max_series_fuse_a.
    """
    out: Dict[str, Any] = {}
    idx = _find_line_index(lines, r"\bOperating Conditions\b")
    if idx is None:
        return out

    block = lines[idx : idx + 35]
    for l in block:
        m = re.search(r"Operating Temperature.*?([-+0-9]+)\s*(?:to|~)\s*([+0-9]+)", l, re.IGNORECASE)
        if m:
            out["operating_temp_c"] = {"min": int(m.group(1)), "max": int(m.group(2))}

        m = re.search(r"Maximum System Voltage.*?(\d{3,5})", l, re.IGNORECASE)
        if m:
            out["max_system_voltage_v"] = int(m.group(1))

        m = re.search(r"Overcurrent Protection Rating.*?(\d{1,3})\s*A", l, re.IGNORECASE)
        if m:
            out["max_series_fuse_a"] = int(m.group(1))

        # DMEGC sometimes expresses tolerance in % or range; keep as string normalized
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

    return {k: v for k, v in out.items() if v not in (None, "", {}, [])}


def _parse_temperature(lines: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    idx = _find_line_index(lines, r"\bTemperature Characteristics\b")
    if idx is None:
        return out

    block = lines[idx : idx + 25]
    for l in block:
        m = re.search(r"Nominal Module Operating Temperature\s*\(NMOT\)\s*([0-9]+)\s*±\s*([0-9]+)", l, re.IGNORECASE)
        if m:
            out["nmot_c"] = int(m.group(1))
            out["nmot_tol_c"] = int(m.group(2))

        # Handle variants: "Temperature Coefficient of Pmax" / "Temperature Coefficients"
        m = re.search(r"Temperature Coefficient(?:s)? of Pmax.*?([-+0-9.,]+)", l, re.IGNORECASE)
        if m:
            out["coeff_pmax_pct_per_c"] = _to_float(m.group(1))

        m = re.search(r"Temperature Coefficient(?:s)? of Voc.*?([-+0-9.,]+)", l, re.IGNORECASE)
        if m:
            out["coeff_voc_pct_per_c"] = _to_float(m.group(1))

        m = re.search(r"Temperature Coefficient(?:s)? of Isc.*?([-+0-9.,]+)", l, re.IGNORECASE)
        if m:
            out["coeff_isc_pct_per_c"] = _to_float(m.group(1))

    return {k: v for k, v in out.items() if v is not None}


# -----------------------------------------------------------------------------
# Validation (physics + sanity)
# -----------------------------------------------------------------------------

def _validate_pmax_relation(block_by_variant: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Validation: Pmax ≈ Vmp * Imp
    """
    report: Dict[str, Any] = {"by_variant": {}, "warnings": []}
    for vid, d in block_by_variant.items():
        p = d.get("pmax_w")
        vmp = d.get("vmp_v")
        imp = d.get("imp_a")
        if p is None or vmp is None or imp is None:
            report["by_variant"][vid] = {"status": "missing", "pmax_w": p, "vmp_v": vmp, "imp_a": imp}
            continue
        p_est = vmp * imp
        rel_err = (p_est - p) / p if p != 0 else None
        ok = (rel_err is not None) and (abs(rel_err) <= 0.05)
        report["by_variant"][vid] = {
            "status": "ok" if ok else "check",
            "pmax_w": float(p),
            "vmp_v": float(vmp),
            "imp_a": float(imp),
            "p_est_w": float(p_est),
            "rel_err": float(rel_err) if rel_err is not None else None,
        }
        if not ok:
            report["warnings"].append(
                f"{vid}: Pmax={p:.2f}W vs Vmp*Imp={p_est:.2f}W (rel_err={rel_err:+.2%})"
            )
    return report


def _infer_power_class_w(model: str, stc: Dict[str, float]) -> Optional[int]:
    """
    Attempt to infer nominal power class (W) from model string or STC pmax.
    - Preferred: DM610... -> 610
    - Fallback: round(pmax_w) if present
    """
    m = re.search(r"\bDM(\d{3})\b", model)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    p = stc.get("pmax_w")
    if isinstance(p, (int, float)):
        try:
            return int(round(float(p)))
        except Exception:
            return None
    return None


# -----------------------------------------------------------------------------
# Standardization (schema v1)
# -----------------------------------------------------------------------------

def _build_standard_output(
    pdf_path: str,
    tech_page_no: int,
    manufacturer: str,
    models: List[str],
    stc_by_model: Dict[str, Dict[str, float]],
    nmot_by_model: Dict[str, Dict[str, float]],
    mechanical: Dict[str, Any],
    operating: Dict[str, Any],
    temperature: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert DMEGC-specific parsing dicts into the unified PVInsight schema v1.
    """

    # Build variants list
    variants: List[Dict[str, Any]] = []
    for model in models:
        stc = stc_by_model.get(model, {}) or {}
        nmot = nmot_by_model.get(model, {}) or {}

        # Ensure only standard keys are carried forward
        nameplate = {k: stc.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a", "eff_pct") if stc.get(k) is not None}
        nmot_std = {k: nmot.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a") if nmot.get(k) is not None}

        power_class_w = _infer_power_class_w(model, stc)

        variants.append(
            {
                "variant_id": model,  # stable, already unique
                "power_class_w": power_class_w,
                "nameplate": nameplate,
                "nmot": nmot_std,
                "efficiency_stc_pct": nameplate.get("eff_pct"),
            }
        )

    # Validation per variant_id for STC and NMOT
    stc_flat = {v["variant_id"]: v.get("nameplate", {}) for v in variants}
    nmot_flat = {v["variant_id"]: v.get("nmot", {}) for v in variants}

    validation = {
        "stc": _validate_pmax_relation(stc_flat),
        "nmot": _validate_pmax_relation(nmot_flat),
    }

    # Meta
    meta = {
        "schema": "pvinsight.module_datasheet.v1",
        "reader_id": "dmegc_pdf_v1",
        "source_pdf": str(pdf_path),
        "technical_page_used": tech_page_no,
        "manufacturer": manufacturer,
        # DMEGC: no strong family/series extraction in this reader; keep optional fields absent
    }

    # Mechanical standardization: keep only normalized keys
    mech_std: Dict[str, Any] = {}
    for k in ("dimensions_mm", "weight_kg", "cell_type_raw", "connector_type", "output_cable_raw", "junction_box_raw"):
        if mechanical.get(k) is not None:
            mech_std[k] = mechanical.get(k)

    # Operating standardization: map/keep standardized keys
    op_std: Dict[str, Any] = {}
    # already standardized by our parser: max_system_voltage_v, max_series_fuse_a, operating_temp_c, power_tolerance_pct
    for k in ("max_system_voltage_v", "max_series_fuse_a", "operating_temp_c", "power_tolerance_pct", "protection_class", "max_test_load_pa", "max_design_load_pa"):
        if operating.get(k) is not None:
            op_std[k] = operating.get(k)

    # Temperature standardization: already standardized
    temp_std: Dict[str, Any] = {}
    for k in ("coeff_pmax_pct_per_c", "coeff_voc_pct_per_c", "coeff_isc_pct_per_c", "nmot_c", "nmot_tol_c"):
        if temperature.get(k) is not None:
            temp_std[k] = temperature.get(k)

    # Best-effort extra sanity: sort variants by power_class_w then id
    def _sort_key(v: Dict[str, Any]) -> Tuple[int, str]:
        pc = v.get("power_class_w")
        return (pc if isinstance(pc, int) else 10**9, str(v.get("variant_id") or ""))

    variants.sort(key=_sort_key)

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

def read_dmegc_datasheet(pdf_path: str) -> Dict[str, Any]:
    pages_raw = _extract_pages_text(pdf_path)
    pages = [_norm_text(p) for p in pages_raw]

    tech_page_no, tech_text = _find_best_technical_page(pages)
    lines = _split_lines(tech_text)

    mechanical = _extract_mechanical_from_module_spec(lines)
    electrical = _parse_dmegc_electrical_table(lines)
    operating = _parse_operating(lines)
    temperature = _parse_temperature(lines)

    models: List[str] = electrical.get("models", []) or []
    stc_by_model: Dict[str, Dict[str, float]] = electrical.get("stc_by_model", {}) or {}
    nmot_by_model: Dict[str, Dict[str, float]] = electrical.get("nmot_by_model", {}) or {}

    standardized = _build_standard_output(
        pdf_path=pdf_path,
        tech_page_no=tech_page_no,
        manufacturer="DMEGC",
        models=models,
        stc_by_model=stc_by_model,
        nmot_by_model=nmot_by_model,
        mechanical=mechanical,
        operating=operating,
        temperature=temperature,
    )

    # For debugging / traceability, we keep a small raw section (optional).
    standardized["raw"] = {
        "models": models,
        "electrical_stc_by_model": stc_by_model,
        "electrical_nmot_by_model": nmot_by_model,
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
# Console output (standard schema)
# -----------------------------------------------------------------------------

def print_dmegc_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("DMEGC DATASHEET READER — PVInsight schema v1 (ALL VARIANTS)")
    print("=" * 110)

    meta = data.get("meta", {}) or {}
    print(f"PDF: {meta.get('source_pdf')}")
    print(f"Technical page used: {meta.get('technical_page_used')}")
    print("-" * 110)

    print("[META]")
    for k in ("schema", "reader_id", "manufacturer"):
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
    ap = argparse.ArgumentParser(description="DMEGC datasheet PDF reader (standardized PVInsight schema v1)")
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
