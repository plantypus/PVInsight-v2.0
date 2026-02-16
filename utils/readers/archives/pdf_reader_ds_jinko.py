# utils/readers/pdf_reader_ds_jinko.py
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# JINKO DATASHEET READER — coord-based (works on JKM550-570N-72HL4-BDV.pdf)
#
# Why this version works:
# - Electrical STC/NOCT table values + temp coefficients are NOT reliably returned by extract_text()
# - They ARE present as positioned "words" → we reconstruct tables using x/y coordinates.
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
    s = s.replace("℃", "°C")  # keep a normalized display
    s = re.sub(r"[ \t]+", " ", s)
    return s


def _to_float(s: str) -> Optional[float]:
    s = s.strip().replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", s):
        return None
    try:
        return float(s)
    except Exception:
        return None


def _find_best_technical_page(pages_text: List[str]) -> int:
    """
    Jinko: technical page contains "SPECIFICATIONS", "Module Type", "STC", "NOCT".
    Returns 1-based page number.
    """
    best_i, best_score = 0, -1
    for i, raw in enumerate(pages_text):
        t = _norm(raw)
        score = 0
        score += 3 if re.search(r"\bSPECIFICATIONS\b", t, re.IGNORECASE) else 0
        score += 3 if re.search(r"\bModule Type\b", t, re.IGNORECASE) else 0
        score += 2 if re.search(r"\bSTC\b", t) else 0
        score += 2 if re.search(r"\bNOCT\b", t) else 0
        score += 1 if re.search(r"\bPmax\b|\bVoc\b|\bIsc\b|\bVmp\b|\bImp\b", t) else 0
        if score > best_score:
            best_score = score
            best_i = i
    return best_i + 1


# -----------------------------------------------------------------------------
# Word selection + grouping
# -----------------------------------------------------------------------------

def _words_in_bbox(words: List[dict], x0: float, y0: float, x1: float, y1: float) -> List[dict]:
    out = []
    for w in words:
        if w["x0"] >= x0 and w["x1"] <= x1 and w["top"] >= y0 and w["bottom"] <= y1:
            out.append(w)
    return out


def _cluster_by_y(words: List[dict], tol: float = 2.0) -> List[List[dict]]:
    """
    Cluster words into rows by their 'top' coordinate (y).
    """
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
    # sort each row by x
    for r in rows:
        r.sort(key=lambda w: w["x0"])
    return rows


def _row_text(row: List[dict]) -> str:
    return " ".join(_norm(w["text"]) for w in row if _norm(w["text"]))


def _find_label_row_top(words: List[dict], label_regex: str) -> Optional[float]:
    """
    Find the y(top) of the row containing the label (based on clustered rows).
    """
    rows = _cluster_by_y(words, tol=2.0)
    for r in rows:
        t = _row_text(r)
        if re.search(label_regex, t, re.IGNORECASE):
            return r[0]["top"]
    return None


def _values_near_y(words: List[dict], y_top: float, y_tol: float = 2.5) -> List[str]:
    """
    Return ordered (by x) word texts near a given y(top).
    """
    sel = [w for w in words if abs(w["top"] - y_top) <= y_tol]
    sel.sort(key=lambda w: w["x0"])
    return [_norm(w["text"]) for w in sel if _norm(w["text"])]


# -----------------------------------------------------------------------------
# Identification (models)
# -----------------------------------------------------------------------------

JINKO_MODEL_RE = r"\bJKM\d{3,4}[A-Z]?\-[0-9]{2}HL[0-9]\-[A-Z0-9\-]+"

def _extract_models_from_words(words: List[dict]) -> List[str]:
    # Scan all words (joined) for model codes, keep unique in appearance order
    joined = " ".join(_norm(w["text"]) for w in sorted(words, key=lambda w: (w["top"], w["x0"])))
    ms = re.findall(JINKO_MODEL_RE, joined)
    uniq: List[str] = []
    for m in ms:
        if m not in uniq:
            uniq.append(m)
    return uniq


# -----------------------------------------------------------------------------
# Electrical table reconstruction (STC/NOCT multi-model)
# -----------------------------------------------------------------------------

def _parse_electrical_table_from_words(words: List[dict], models: List[str]) -> Dict[str, Any]:
    """
    For this Jinko layout:
    - Each metric row contains values left-to-right as:
        model1 STC, model1 NOCT, model2 STC, model2 NOCT, ... model5 STC, model5 NOCT
      except Efficiency row which is only STC (one value per model).
    - Row labels are present on the left side.
    """
    # Focus bbox around the SPECIFICATIONS / Electrical table area
    # These bounds are generous and work on the provided PDF.
    tbl = _words_in_bbox(words, x0=50, y0=380, x1=545, y1=520)

    # Find y of each label row
    y_pmax = _find_label_row_top(tbl, r"\bMaximum\s+Power\s*\(Pmax\)")
    y_vmp  = _find_label_row_top(tbl, r"\bMaximum\s+Power\s+Voltage\s*\(Vmp\)")
    y_imp  = _find_label_row_top(tbl, r"\bMaximum\s+Power\s+Current\s*\(Imp\)")
    y_voc  = _find_label_row_top(tbl, r"\bOpen-?circuit\s+Voltage\s*\(Voc\)")
    y_isc  = _find_label_row_top(tbl, r"\bShort-?circuit\s+Current\s*\(Isc\)")
    y_eff  = _find_label_row_top(tbl, r"\bModule\s+Efficiency\b")

    # If any of core rows missing, return diagnostic to help you see failure quickly
    core = {"pmax": y_pmax, "vmp": y_vmp, "imp": y_imp, "voc": y_voc, "isc": y_isc}
    if any(v is None for v in core.values()):
        return {
            "mode_used": "coord_table_failed",
            "diagnostic": {"label_rows_y": core, "eff_y": y_eff},
            "stc_by_model": {},
            "noct_by_model": {},
        }

    def parse_row_values(y: float, unit_suffix: str, expect_pairs: bool) -> Tuple[List[float], List[float]]:
        """
        Return (stc_vals, noct_vals)
        - expect_pairs=True: we parse 2*len(models) values and split odd/even → STC/NOCT.
        - expect_pairs=False: we parse len(models) values → STC only.
        """
        tokens = _values_near_y(tbl, y, y_tol=2.5)
        # keep only value-like tokens with suffix
        vals = []
        for t in tokens:
            if unit_suffix and not t.endswith(unit_suffix):
                continue
            # extract numeric part
            m = re.search(r"[-+]?\d+(?:\.\d+)?", t)
            if not m:
                continue
            fv = _to_float(m.group(0))
            if fv is None:
                continue
            vals.append(fv)

        if expect_pairs:
            # if extraction returned extra noise, trim to expected 2N by taking left-to-right earliest
            needed = 2 * len(models)
            vals = vals[:needed]
            stc = vals[0::2]
            noct = vals[1::2]
            return stc, noct

        # STC only
        vals = vals[:len(models)]
        return vals, []

    stc_pmax, noct_pmax = parse_row_values(y_pmax, "Wp", expect_pairs=True)
    stc_vmp,  noct_vmp  = parse_row_values(y_vmp,  "V",  expect_pairs=True)
    stc_imp,  noct_imp  = parse_row_values(y_imp,  "A",  expect_pairs=True)
    stc_voc,  noct_voc  = parse_row_values(y_voc,  "V",  expect_pairs=True)
    stc_isc,  noct_isc  = parse_row_values(y_isc,  "A",  expect_pairs=True)

    # Efficiency row: "21.29%" etc (STC only)
    eff = []
    if y_eff is not None:
        eff_tokens = _values_near_y(tbl, y_eff, y_tol=2.5)
        for t in eff_tokens:
            if not t.endswith("%"):
                continue
            m = re.search(r"\d+(?:\.\d+)?", t)
            if not m:
                continue
            fv = _to_float(m.group(0))
            if fv is None:
                continue
            eff.append(fv)
        eff = eff[:len(models)]

    # Build by-model dicts in declared model order
    stc_by: Dict[str, Dict[str, float]] = {}
    noct_by: Dict[str, Dict[str, float]] = {}

    for i, model in enumerate(models):
        if i < len(stc_pmax):
            stc_by.setdefault(model, {})["pmax_w"] = float(stc_pmax[i])
        if i < len(stc_vmp):
            stc_by.setdefault(model, {})["vmp_v"] = float(stc_vmp[i])
        if i < len(stc_imp):
            stc_by.setdefault(model, {})["imp_a"] = float(stc_imp[i])
        if i < len(stc_voc):
            stc_by.setdefault(model, {})["voc_v"] = float(stc_voc[i])
        if i < len(stc_isc):
            stc_by.setdefault(model, {})["isc_a"] = float(stc_isc[i])
        if i < len(eff):
            stc_by.setdefault(model, {})["eff_pct"] = float(eff[i])

        if i < len(noct_pmax):
            noct_by.setdefault(model, {})["pmax_w"] = float(noct_pmax[i])
        if i < len(noct_vmp):
            noct_by.setdefault(model, {})["vmp_v"] = float(noct_vmp[i])
        if i < len(noct_imp):
            noct_by.setdefault(model, {})["imp_a"] = float(noct_imp[i])
        if i < len(noct_voc):
            noct_by.setdefault(model, {})["voc_v"] = float(noct_voc[i])
        if i < len(noct_isc):
            noct_by.setdefault(model, {})["isc_a"] = float(noct_isc[i])

    return {
        "mode_used": "coord_table_ok",
        "stc_by_model": {k: v for k, v in stc_by.items() if v},
        "noct_by_model": {k: v for k, v in noct_by.items() if v},
        "diagnostic": {
            "label_rows_y": {
                "pmax": y_pmax, "vmp": y_vmp, "imp": y_imp, "voc": y_voc, "isc": y_isc, "eff": y_eff
            }
        },
    }


# -----------------------------------------------------------------------------
# Operating + temperature (label → nearest right-side value, coord-based)
# -----------------------------------------------------------------------------

def _nearest_value_right(words: List[dict], label_regex: str, x_min_value: float = 250.0) -> Optional[str]:
    """
    Find label row and return the closest value token to the right (same y band).
    """
    rows = _cluster_by_y(words, tol=2.0)
    for r in rows:
        t = _row_text(r)
        if not re.search(label_regex, t, re.IGNORECASE):
            continue
        y = r[0]["top"]
        # candidates near same y and on the right
        cands = [w for w in words if abs(w["top"] - y) <= 2.5 and w["x0"] >= x_min_value]
        cands.sort(key=lambda w: w["x0"])
        if not cands:
            return None
        return _norm(cands[0]["text"])
    return None


def _parse_operating_and_temperature(words: List[dict]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    In this PDF, these values are on the lower-right of the SPECIFICATIONS block.
    """
    block = _words_in_bbox(words, x0=50, y0=500, x1=545, y1=660)

    operating: Dict[str, Any] = {}
    temperature: Dict[str, Any] = {}

    v = _nearest_value_right(block, r"\bOperating Temp", x_min_value=250)
    if v and re.search(r"-?\d+", v):
        m = re.search(r"(-?\d+).*(\+?\d+)", v.replace("°C", "℃"))
        if m:
            operating["operating_temp_c"] = {"min": int(m.group(1)), "max": int(m.group(2))}

    v = _nearest_value_right(block, r"\bMaximum system voltage\b", x_min_value=250)
    if v:
        m = re.search(r"(\d{3,5})", v)
        if m:
            operating["max_system_voltage_v"] = int(m.group(1))

    v = _nearest_value_right(block, r"\bMaximum series fuse rating\b", x_min_value=250)
    if v:
        m = re.search(r"(\d{1,3})", v)
        if m:
            operating["max_series_fuse_a"] = int(m.group(1))

    v = _nearest_value_right(block, r"\bPower tolerance\b", x_min_value=250)
    if v:
        operating["power_tolerance"] = v.replace(" ", "")

    # Temperature coefficients rows (3 lines)
    v = _nearest_value_right(block, r"Temperature coefficients? of Pmax", x_min_value=250)
    if v:
        m = re.search(r"[-+]?\d+(?:\.\d+)?", v)
        if m:
            temperature["coeff_pmax_pct_per_c"] = _to_float(m.group(0))

    v = _nearest_value_right(block, r"Temperature coefficients? of Voc", x_min_value=250)
    if v:
        m = re.search(r"[-+]?\d+(?:\.\d+)?", v)
        if m:
            temperature["coeff_voc_pct_per_c"] = _to_float(m.group(0))

    v = _nearest_value_right(block, r"Temperature coefficients? of Isc", x_min_value=250)
    if v:
        m = re.search(r"[-+]?\d+(?:\.\d+)?", v)
        if m:
            temperature["coeff_isc_pct_per_c"] = _to_float(m.group(0))

    v = _nearest_value_right(block, r"Nominal operating cell temperature\s*\(NOCT\)", x_min_value=250)
    if v:
        # example in this pdf: "45±2℃"
        m = re.search(r"(\d+)\s*±\s*(\d+)", v.replace("°C", "℃"))
        if m:
            temperature["noct_c"] = int(m.group(1))
            temperature["noct_tol_c"] = int(m.group(2))

    v = _nearest_value_right(block, r"Refer\.\s*Bifacial Factor", x_min_value=250)
    if v:
        m = re.search(r"(\d+)\s*±\s*(\d+)", v)
        if m:
            operating["bifaciality_pct"] = float(m.group(1))
            operating["bifaciality_tol_pct"] = float(m.group(2))

    # prune
    operating = {k: v for k, v in operating.items() if v is not None}
    temperature = {k: v for k, v in temperature.items() if v is not None}
    return operating, temperature


# -----------------------------------------------------------------------------
# Mechanical (this part is actually fine with text, but we keep it simple)
# -----------------------------------------------------------------------------

def _parse_mechanical_from_text(page_text: str) -> Dict[str, Any]:
    t = _norm(page_text)
    out: Dict[str, Any] = {}

    m = re.search(r"\bCell Type\b\s*([A-Za-z0-9 \-]+)", t, re.IGNORECASE)
    if m:
        out["cell_type_raw"] = m.group(1).strip()

    m = re.search(r"\bNo\.\s*of\s*cells\b\s*(\d{2,4})", t, re.IGNORECASE)
    if m:
        out["cells_count"] = int(m.group(1))

    m = re.search(r"\bDimensions\b\s*(\d{3,5})[×x]\s*(\d{3,5})[×x]\s*(\d{1,4})\s*mm", t, re.IGNORECASE)
    if m:
        out["dimensions_mm"] = {"length": int(m.group(1)), "width": int(m.group(2)), "thickness": int(m.group(3))}

    m = re.search(r"\bWeight\b\s*([0-9]+(?:\.\d+)?)\s*kg", t, re.IGNORECASE)
    if m:
        out["weight_kg"] = _to_float(m.group(1))

    for key, pat in [
        ("front_glass", r"\bFront Glass\b\s*(.+)"),
        ("back_glass", r"\bBack Glass\b\s*(.+)"),
        ("frame", r"\bFrame\b\s*(.+)"),
        ("junction_box", r"\bJunction Box\b\s*(.+)"),
        ("output_cables", r"\bOutput Cables\b\s*(.+)"),
    ]:
        mm = re.search(pat, t, re.IGNORECASE)
        if mm:
            # stop at newline if present
            out[key] = mm.group(1).split("\n")[0].strip()

    return {k: v for k, v in out.items() if v is not None and v != ""}


# -----------------------------------------------------------------------------
# Physical validation
# -----------------------------------------------------------------------------

def _validate_stc(stc_by_model: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    rep: Dict[str, Any] = {"stc": {}, "warnings": []}
    for model, d in stc_by_model.items():
        p = d.get("pmax_w")
        v = d.get("vmp_v")
        i = d.get("imp_a")
        if p is None or v is None or i is None:
            rep["stc"][model] = {"status": "missing", "pmax_w": p, "vmp_v": v, "imp_a": i}
            continue
        p_est = v * i
        rel = (p_est - p) / p if p else None
        ok = (rel is not None) and (abs(rel) <= 0.05)
        rep["stc"][model] = {
            "status": "ok" if ok else "check",
            "pmax_w": float(p),
            "vmp_v": float(v),
            "imp_a": float(i),
            "p_est_w": float(p_est),
            "rel_err": float(rel) if rel is not None else None,
        }
        if not ok and rel is not None:
            rep["warnings"].append(f"[STC] {model}: Pmax={p:.2f} vs Vmp*Imp={p_est:.2f} (rel={rel:+.2%})")
    return rep


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def read_jinko_datasheet(pdf_path: str) -> Dict[str, Any]:
    pdfplumber = _require_pdfplumber()
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(pdf_path)

    with pdfplumber.open(str(p)) as pdf:
        pages_text = [(page.extract_text() or "") for page in pdf.pages]
        tech_page_no = _find_best_technical_page(pages_text)

        page = pdf.pages[tech_page_no - 1]
        page_text = page.extract_text() or ""
        words = page.extract_words()

    models = _extract_models_from_words(words)

    electrical = _parse_electrical_table_from_words(words, models)
    operating, temperature = _parse_operating_and_temperature(words)
    mechanical = _parse_mechanical_from_text(page_text)

    validation = _validate_stc(electrical.get("stc_by_model", {}) or {})

    out: Dict[str, Any] = {
        "source_pdf": str(pdf_path),
        "reader": "pdf_reader_ds_jinko_coord_v1",
        "technical_page_used": tech_page_no,
        "identification": {
            "manufacturer": "Jinko Solar",
            "models": models,
        },
        "mechanical": mechanical,
        "operating": operating,
        "temperature": temperature,
        "electrical": {
            "mode_used": electrical.get("mode_used"),
            "diagnostic": electrical.get("diagnostic", {}),
            "stc_by_model": electrical.get("stc_by_model", {}),
            "noct_by_model": electrical.get("noct_by_model", {}),
        },
        "validation": validation,
    }

    # prune empties
    def prune(x: Any) -> Any:
        if isinstance(x, dict):
            d = {k: prune(v) for k, v in x.items()}
            return {k: v for k, v in d.items() if v not in (None, "", {}, [], [""])}
        if isinstance(x, list):
            l = [prune(v) for v in x]
            return [v for v in l if v not in (None, "", {}, [], [""])]
        return x

    return prune(out)


def print_jinko_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("JINKO DATASHEET READER — COORD BASED (ALL MODELS)")
    print("=" * 110)
    print(f"PDF: {data.get('source_pdf')}")
    print(f"Technical page used: {data.get('technical_page_used')}")
    print("-" * 110)

    models = (data.get("identification", {}) or {}).get("models", []) or []
    print("[MODELS]")
    print(f"  count: {len(models)}")
    for m in models:
        print(f"   - {m}")

    mech = data.get("mechanical", {})
    if mech:
        print("\n[MECHANICAL]")
        for k, v in mech.items():
            print(f"  - {k}: {v}")

    op = data.get("operating", {})
    if op:
        print("\n[OPERATING]")
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
    print("\n[ELECTRICAL]")
    print(f"  - mode_used: {elec.get('mode_used')}")
    if elec.get("diagnostic"):
        print(f"  - diagnostic: {elec.get('diagnostic')}")

    stc = elec.get("stc_by_model", {}) or {}
    noct = elec.get("noct_by_model", {}) or {}

    def fmt(v: Any) -> str:
        return "-" if v is None else str(v)

    print("\n[ELECTRICAL — STC]")
    for m in models:
        d = stc.get(m, {})
        if not d:
            print(f"  - {m}: (not parsed)")
            continue
        print(
            f"  - {m}: Pmax={fmt(d.get('pmax_w'))} W | Voc={fmt(d.get('voc_v'))} V | Isc={fmt(d.get('isc_a'))} A | "
            f"Vmp={fmt(d.get('vmp_v'))} V | Imp={fmt(d.get('imp_a'))} A | Eff={fmt(d.get('eff_pct'))} %"
        )

    print("\n[ELECTRICAL — NOCT]")
    for m in models:
        d = noct.get(m, {})
        if not d:
            print(f"  - {m}: (not parsed)")
            continue
        print(
            f"  - {m}: Pmax={fmt(d.get('pmax_w'))} W | Voc={fmt(d.get('voc_v'))} V | Isc={fmt(d.get('isc_a'))} A | "
            f"Vmp={fmt(d.get('vmp_v'))} V | Imp={fmt(d.get('imp_a'))} A"
        )

    val = data.get("validation", {})
    if val:
        print("\n[VALIDATION: Pmax ≈ Vmp×Imp (STC)]")
        stc_r = val.get("stc", {}) or {}
        for m in models:
            r = stc_r.get(m, {})
            status = r.get("status", "missing")
            rel = r.get("rel_err")
            if rel is None:
                print(f"  - {m}: {status}")
            else:
                print(f"  - {m}: {status} (rel_err={rel:+.2%})")

        warns = val.get("warnings", []) or []
        if warns:
            print("\n  WARNINGS:")
            for w in warns:
                print(f"   - {w}")

    print("\n" + "=" * 110)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Jinko datasheet reader (coord-based)")
    ap.add_argument("pdf", help="Path to Jinko datasheet PDF")
    ap.add_argument("--json", dest="json_out", help="Optional JSON output path")
    args = ap.parse_args()

    data = read_jinko_datasheet(args.pdf)
    print_jinko_report(data)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved JSON: {args.json_out}")


if __name__ == "__main__":
    main()
