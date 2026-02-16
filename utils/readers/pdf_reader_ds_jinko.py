# utils/readers/pdf_reader_ds_jinko.py
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# JINKO DATASHEET READER — standardized output (PVInsight schema v1)
# Target PDF example: JKM550-570N-72HL4-BDV.pdf
#
# Why coord-based:
# - Electrical STC/NOCT table values + temp coefficients are not reliable via extract_text()
# - They are present as positioned "words" -> we reconstruct rows by y and read values by x order
#
# Standard output schema (core):
# {
#   "meta": {...},
#   "variants": [ { "variant_id", "power_class_w", "nameplate", "noct", ... }, ... ],
#   "temperature": {...},
#   "operating": {...},
#   "mechanical": {...},
#   "validation": {...},
#   "raw": {... optional debug ...}
# }
#
# Standard keys:
# - STC/nameplate:  pmax_w, vmp_v, imp_a, voc_v, isc_a, eff_pct(optional)
# - NOCT:           pmax_w, vmp_v, imp_a, voc_v, isc_a
# - temperature:    coeff_pmax_pct_per_c, coeff_voc_pct_per_c, coeff_isc_pct_per_c, noct_c, noct_tol_c
# - operating:      max_system_voltage_v, max_series_fuse_a, operating_temp_c{min,max}, bifaciality_pct(optional)
# - mechanical:     dimensions_mm{length,width,thickness}, weight_kg, cell_type_raw, connector_type, output_cable_raw, cells_count(optional)
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


def _to_float(s: str) -> Optional[float]:
    s = (s or "").strip().replace(",", ".")
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


def _find_label_row_top(words: List[dict], label_regex: str) -> Optional[float]:
    rows = _cluster_by_y(words, tol=2.0)
    for r in rows:
        t = _row_text(r)
        if re.search(label_regex, t, re.IGNORECASE):
            return r[0]["top"]
    return None


def _values_near_y(words: List[dict], y_top: float, y_tol: float = 2.5) -> List[str]:
    sel = [w for w in words if abs(w["top"] - y_top) <= y_tol]
    sel.sort(key=lambda w: w["x0"])
    return [_norm(w["text"]) for w in sel if _norm(w["text"])]


# -----------------------------------------------------------------------------
# Identification (models)
# -----------------------------------------------------------------------------

JINKO_MODEL_RE = r"\bJKM\d{3,4}[A-Z]?\-[0-9]{2}HL[0-9]\-[A-Z0-9\-]+"

def _extract_models_from_words(words: List[dict]) -> List[str]:
    joined = " ".join(_norm(w["text"]) for w in sorted(words, key=lambda w: (w["top"], w["x0"])))
    ms = re.findall(JINKO_MODEL_RE, joined)
    uniq: List[str] = []
    for m in ms:
        if m not in uniq:
            uniq.append(m)
    return uniq


def _infer_power_class_from_model(model: str) -> Optional[int]:
    """
    For Jinko naming like JKM565N-72HL4-BDV, extract 565 as power class.
    """
    m = re.search(r"\bJKM(\d{3,4})", model)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Electrical table reconstruction (STC/NOCT multi-model)
# -----------------------------------------------------------------------------

def _parse_electrical_table_from_words(words: List[dict], models: List[str]) -> Dict[str, Any]:
    """
    Jinko layout used here:
    - Each metric row contains values left-to-right:
        model1 STC, model1 NOCT, model2 STC, model2 NOCT, ... (pairs)
      Efficiency row is STC only (one value per model).
    """
    # Table bbox (tuned for the known datasheet)
    tbl = _words_in_bbox(words, x0=50, y0=380, x1=545, y1=520)

    y_pmax = _find_label_row_top(tbl, r"\bMaximum\s+Power\s*\(Pmax\)")
    y_vmp  = _find_label_row_top(tbl, r"\bMaximum\s+Power\s+Voltage\s*\(Vmp\)")
    y_imp  = _find_label_row_top(tbl, r"\bMaximum\s+Power\s+Current\s*\(Imp\)")
    y_voc  = _find_label_row_top(tbl, r"\bOpen-?circuit\s+Voltage\s*\(Voc\)")
    y_isc  = _find_label_row_top(tbl, r"\bShort-?circuit\s+Current\s*\(Isc\)")
    y_eff  = _find_label_row_top(tbl, r"\bModule\s+Efficiency\b")

    core = {"pmax": y_pmax, "vmp": y_vmp, "imp": y_imp, "voc": y_voc, "isc": y_isc}
    if any(v is None for v in core.values()):
        return {
            "mode_used": "coord_table_failed",
            "diagnostic": {"label_rows_y": core, "eff_y": y_eff},
            "stc_by_model": {},
            "noct_by_model": {},
        }

    def parse_row_values(y: float, unit_suffix: str, expect_pairs: bool) -> Tuple[List[float], List[float]]:
        tokens = _values_near_y(tbl, y, y_tol=2.5)
        vals: List[float] = []
        for t in tokens:
            if unit_suffix and not t.endswith(unit_suffix):
                continue
            m = re.search(r"[-+]?\d+(?:\.\d+)?", t)
            if not m:
                continue
            fv = _to_float(m.group(0))
            if fv is not None:
                vals.append(fv)

        if expect_pairs:
            needed = 2 * len(models)
            vals = vals[:needed]
            return vals[0::2], vals[1::2]

        vals = vals[:len(models)]
        return vals, []

    stc_pmax, noct_pmax = parse_row_values(y_pmax, "Wp", expect_pairs=True)
    stc_vmp,  noct_vmp  = parse_row_values(y_vmp,  "V",  expect_pairs=True)
    stc_imp,  noct_imp  = parse_row_values(y_imp,  "A",  expect_pairs=True)
    stc_voc,  noct_voc  = parse_row_values(y_voc,  "V",  expect_pairs=True)
    stc_isc,  noct_isc  = parse_row_values(y_isc,  "A",  expect_pairs=True)

    eff: List[float] = []
    if y_eff is not None:
        eff_tokens = _values_near_y(tbl, y_eff, y_tol=2.5)
        for t in eff_tokens:
            if not t.endswith("%"):
                continue
            m = re.search(r"\d+(?:\.\d+)?", t)
            if not m:
                continue
            fv = _to_float(m.group(0))
            if fv is not None:
                eff.append(fv)
        eff = eff[:len(models)]

    stc_by: Dict[str, Dict[str, float]] = {}
    noct_by: Dict[str, Dict[str, float]] = {}

    for i, model in enumerate(models):
        if i < len(stc_pmax): stc_by.setdefault(model, {})["pmax_w"] = float(stc_pmax[i])
        if i < len(stc_vmp):  stc_by.setdefault(model, {})["vmp_v"] = float(stc_vmp[i])
        if i < len(stc_imp):  stc_by.setdefault(model, {})["imp_a"]  = float(stc_imp[i])
        if i < len(stc_voc):  stc_by.setdefault(model, {})["voc_v"]  = float(stc_voc[i])
        if i < len(stc_isc):  stc_by.setdefault(model, {})["isc_a"]  = float(stc_isc[i])
        if i < len(eff):      stc_by.setdefault(model, {})["eff_pct"] = float(eff[i])

        if i < len(noct_pmax): noct_by.setdefault(model, {})["pmax_w"] = float(noct_pmax[i])
        if i < len(noct_vmp):  noct_by.setdefault(model, {})["vmp_v"]  = float(noct_vmp[i])
        if i < len(noct_imp):  noct_by.setdefault(model, {})["imp_a"]  = float(noct_imp[i])
        if i < len(noct_voc):  noct_by.setdefault(model, {})["voc_v"]  = float(noct_voc[i])
        if i < len(noct_isc):  noct_by.setdefault(model, {})["isc_a"]  = float(noct_isc[i])

    return {
        "mode_used": "coord_table_ok",
        "stc_by_model": {k: v for k, v in stc_by.items() if v},
        "noct_by_model": {k: v for k, v in noct_by.items() if v},
        "diagnostic": {"label_rows_y": {**core, "eff": y_eff}},
    }


# -----------------------------------------------------------------------------
# Operating + temperature (label -> nearest right-side value, coord-based)
# -----------------------------------------------------------------------------

def _nearest_value_right(words: List[dict], label_regex: str, x_min_value: float = 250.0) -> Optional[str]:
    rows = _cluster_by_y(words, tol=2.0)
    for r in rows:
        t = _row_text(r)
        if not re.search(label_regex, t, re.IGNORECASE):
            continue
        y = r[0]["top"]
        cands = [w for w in words if abs(w["top"] - y) <= 2.5 and w["x0"] >= x_min_value]
        cands.sort(key=lambda w: w["x0"])
        if not cands:
            return None
        return _norm(cands[0]["text"])
    return None


def _parse_operating_and_temperature(words: List[dict]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    block = _words_in_bbox(words, x0=50, y0=500, x1=545, y1=660)

    operating: Dict[str, Any] = {}
    temperature: Dict[str, Any] = {}

    v = _nearest_value_right(block, r"\bOperating Temp", x_min_value=250)
    if v:
        m = re.search(r"(-?\d+)\s*~\s*\+?(\d+)", v.replace("°C", "℃"))
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
        # keep raw string (varies by datasheet)
        operating["power_tolerance_raw"] = v.replace(" ", "")

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

    return (
        {k: v for k, v in operating.items() if v is not None and v != ""},
        {k: v for k, v in temperature.items() if v is not None and v != ""},
    )


# -----------------------------------------------------------------------------
# Mechanical (text is OK here, keep minimal + normalized keys)
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

    # keep raw info but map to stable names when possible
    mm = re.search(r"\bOutput Cables\b\s*(.+)", t, re.IGNORECASE)
    if mm:
        out["output_cable_raw"] = mm.group(1).split("\n")[0].strip()

    mm = re.search(r"\bConnector\b\s*(.+)", t, re.IGNORECASE)
    if mm:
        out["connector_type"] = mm.group(1).split("\n")[0].strip()

    return {k: v for k, v in out.items() if v is not None and v != ""}


# -----------------------------------------------------------------------------
# Validation (standard)
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
    models: List[str],
    stc_by_model: Dict[str, Dict[str, float]],
    noct_by_model: Dict[str, Dict[str, float]],
    mechanical_raw: Dict[str, Any],
    operating_raw: Dict[str, Any],
    temperature_raw: Dict[str, Any],
    diagnostic: Dict[str, Any],
    mode_used: Optional[str],
) -> Dict[str, Any]:
    manufacturer = "Jinko Solar"

    # Variants in model order
    variants: List[Dict[str, Any]] = []
    for m in models:
        power_class = _infer_power_class_from_model(m)

        stc = stc_by_model.get(m, {}) or {}
        noct = noct_by_model.get(m, {}) or {}

        nameplate = {k: stc.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a", "eff_pct") if stc.get(k) is not None}
        noct_std = {k: noct.get(k) for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a") if noct.get(k) is not None}

        variants.append(
            {
                "variant_id": m,
                "power_class_w": power_class,
                "nameplate": nameplate,
                "noct": noct_std,
                "efficiency_stc_pct": nameplate.get("eff_pct"),
            }
        )

    # Validation
    stc_flat = {v["variant_id"]: v.get("nameplate", {}) for v in variants}
    noct_flat = {v["variant_id"]: v.get("noct", {}) for v in variants}
    validation = {
        "stc": _validate_pmax_relation(stc_flat) if stc_flat else {},
        "noct": _validate_pmax_relation(noct_flat) if noct_flat else {},
    }

    # Meta
    meta: Dict[str, Any] = {
        "schema": "pvinsight.module_datasheet.v1",
        "reader_id": "jinko_coord_v1",
        "source_pdf": str(pdf_path),
        "technical_page_used": tech_page,
        "manufacturer": manufacturer,
        "parse_mode": mode_used or "unknown",
    }

    # Mechanical
    mech: Dict[str, Any] = {}
    for k in ("dimensions_mm", "weight_kg", "cell_type_raw", "connector_type", "output_cable_raw", "cells_count"):
        if mechanical_raw.get(k) is not None:
            mech[k] = mechanical_raw.get(k)

    # Operating
    op: Dict[str, Any] = {}
    for k in ("operating_temp_c", "max_system_voltage_v", "max_series_fuse_a", "bifaciality_pct", "bifaciality_tol_pct"):
        if operating_raw.get(k) is not None:
            op[k] = operating_raw.get(k)
    if operating_raw.get("power_tolerance_raw") is not None:
        op["power_tolerance_raw"] = operating_raw.get("power_tolerance_raw")

    # Temperature
    temp: Dict[str, Any] = {}
    for k in ("coeff_pmax_pct_per_c", "coeff_voc_pct_per_c", "coeff_isc_pct_per_c", "noct_c", "noct_tol_c"):
        if temperature_raw.get(k) is not None:
            temp[k] = temperature_raw.get(k)

    out = {
        "meta": meta,
        "variants": variants,
        "temperature": temp,
        "operating": op,
        "mechanical": mech,
        "validation": validation,
        "raw": {
            "diagnostic": diagnostic or {},
        },
    }
    return out


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
    operating_raw, temperature_raw = _parse_operating_and_temperature(words)
    mechanical_raw = _parse_mechanical_from_text(page_text)

    out = _build_standard_output(
        pdf_path=pdf_path,
        tech_page=tech_page_no,
        models=models,
        stc_by_model=electrical.get("stc_by_model", {}) or {},
        noct_by_model=electrical.get("noct_by_model", {}) or {},
        mechanical_raw=mechanical_raw,
        operating_raw=operating_raw,
        temperature_raw=temperature_raw,
        diagnostic=electrical.get("diagnostic", {}) or {},
        mode_used=electrical.get("mode_used"),
    )

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


# -----------------------------------------------------------------------------
# Console report (standard schema)
# -----------------------------------------------------------------------------

def print_jinko_report(data: Dict[str, Any]) -> None:
    print("=" * 110)
    print("JINKO DATASHEET READER — PVInsight schema v1 (ALL VARIANTS)")
    print("=" * 110)

    meta = data.get("meta", {}) or {}
    print(f"PDF: {meta.get('source_pdf')}")
    print(f"Technical page used: {meta.get('technical_page_used')}")
    print("-" * 110)

    print("[META]")
    for k in ("schema", "reader_id", "manufacturer", "parse_mode"):
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

    print("\n[ELECTRICAL — NOCT]")
    for v in variants:
        vid = v.get("variant_id")
        noct = (v.get("noct") or {})
        if not noct:
            print(f"  - {vid}: (not parsed)")
            continue
        print(
            f"  - {vid}: Pmax={fmt(noct.get('pmax_w'))} W | Voc={fmt(noct.get('voc_v'))} V | Isc={fmt(noct.get('isc_a'))} A | "
            f"Vmp={fmt(noct.get('vmp_v'))} V | Imp={fmt(noct.get('imp_a'))} A"
        )

    val = data.get("validation", {}) or {}
    if val:
        print("\n[VALIDATION: Pmax ≈ Vmp×Imp]")
        for name in ("stc", "noct"):
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

    raw = data.get("raw", {}) or {}
    diag = raw.get("diagnostic")
    if diag:
        print("\n[DEBUG]")
        print(f"  - diagnostic: {diag}")

    print("\n" + "=" * 110)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Jinko datasheet reader (PVInsight schema v1, coord-based)")
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
