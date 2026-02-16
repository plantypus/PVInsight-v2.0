# core/module/compare_pan_to_ds.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from utils.readers.bytes_to_path import call_with_path
from utils.readers.reader_pan_file import read_pan_file

from utils.readers.pdf_reader_ds_jinko import read_jinko_datasheet
from utils.readers.pdf_reader_ds_dmegc import read_dmegc_datasheet
from utils.readers.pdf_reader_ds_astronergy import read_astronergy_datasheet
from utils.readers.pdf_reader_ds_das_solar import read_das_solar_datasheet
from utils.readers.pdf_reader_ds_canadian_solar import read_canadian_solar_datasheet


BytesLike = bytes

# Manufacturer registry (path-based readers)
DS_READERS_BY_MFR: Dict[str, Callable[[str], Dict[str, Any]]] = {
    "jinko": read_jinko_datasheet,
    "dmegc": read_dmegc_datasheet,
    "astronergy": read_astronergy_datasheet,
    "das_solar": read_das_solar_datasheet,
    "canadian_solar": read_canadian_solar_datasheet,
}

# Strict brand gating tokens
EXPECTED_BRAND_TOKEN: Dict[str, str] = {
    "jinko": "JINKO",
    "dmegc": "DMEGC",
    "astronergy": "ASTRONERGY",
    "das_solar": "DAS",
    "canadian_solar": "CANADIAN SOLAR",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _safe_get(d: Dict[str, Any], path: List[str]) -> Any:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        s = str(x).strip().replace(",", ".")
        return float(s)
    except Exception:
        return None


def _as_int_w(x: Any) -> Optional[int]:
    v = _as_float(x)
    if v is None:
        return None
    return int(round(v))


def _norm_token(s: Any) -> str:
    return str(s or "").strip().upper()


def _norm_model(s: Any) -> str:
    return str(s or "").strip().replace(" ", "").upper()


def _delta(pan: Optional[float], ds: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    deviation_abs = pan - ds
    deviation_pct = (pan - ds) / ds * 100
    """
    if pan is None or ds is None:
        return None, None
    da = pan - ds
    if ds == 0:
        return da, None
    return da, da / ds * 100.0


def _to_mm(m: Optional[float]) -> Optional[float]:
    if m is None:
        return None
    return m * 1000.0


def _pct_from_mu_and_ref(mu_per_c: Optional[float], ref: Optional[float], *, mu_unit: str) -> Optional[float]:
    """
    Convert absolute temp coefficient to %/°C.
      - mu_unit="mA_per_C": mu is mA/°C, ref in A
      - mu_unit="mV_per_C": mu is mV/°C, ref in V
    """
    if mu_per_c is None or ref is None or ref == 0:
        return None
    if mu_unit == "mA_per_C":
        return (mu_per_c / 1000.0) / ref * 100.0
    if mu_unit == "mV_per_C":
        return (mu_per_c / 1000.0) / ref * 100.0
    return None


def _mu_from_pct_and_ref(pct_per_c: Optional[float], ref: Optional[float], *, out_unit: str) -> Optional[float]:
    """
    Convert %/°C to absolute coefficient.
      - out_unit="mA_per_C": returns mA/°C using ref current A
      - out_unit="mV_per_C": returns mV/°C using ref voltage V
    """
    if pct_per_c is None or ref is None:
        return None
    per_c = pct_per_c / 100.0
    if out_unit == "mA_per_C":
        return per_c * ref * 1000.0
    if out_unit == "mV_per_C":
        return per_c * ref * 1000.0
    return None


def _rshunt_default_pvsyst(vmp_v: Optional[float], isc_a: Optional[float], imp_a: Optional[float]) -> Optional[float]:
    """
    PVsyst help:
      Rshunt(default) = Vmp / (0.2 * (Isc - Imp))
    """
    if vmp_v is None or isc_a is None or imp_a is None:
        return None
    denom = 0.2 * (isc_a - imp_a)
    if denom <= 0:
        return None
    return vmp_v / denom


def _make_run_dir(outputs_dir: Union[str, Path], tool_id: str = "compare_pan_to_ds") -> Path:
    base = Path(outputs_dir)
    base.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base / f"{tool_id}_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


# -----------------------------------------------------------------------------
# Extraction: PAN identity + PAN technical numbers
# -----------------------------------------------------------------------------

def _extract_pan_identity(pan_ds: Dict[str, Any]) -> Dict[str, Any]:
    manufacturer = _safe_get(pan_ds, ["standard", "module", "manufacturer"])
    model = _safe_get(pan_ds, ["standard", "module", "model"])
    pmp_w = _safe_get(pan_ds, ["standard", "electrical", "stc", "pmp_w"])
    return {
        "manufacturer": manufacturer,
        "model": model,
        "pmp_w": pmp_w,
        "pmp_w_int": _as_int_w(pmp_w),
    }


def _pan_get_stc(pan_ds: Dict[str, Any], key: str) -> Optional[float]:
    return _as_float(_safe_get(pan_ds, ["standard", "electrical", "stc", key]))


def _pan_get_stc_ref(pan_ds: Dict[str, Any], key: str) -> Optional[float]:
    return _as_float(_safe_get(pan_ds, ["standard", "electrical", "stc_ref", key]))


def _pan_get_module(pan_ds: Dict[str, Any], path: List[str]) -> Any:
    return _safe_get(pan_ds, ["standard", "module"] + path)


def _pan_get_cells_total(pan_ds: Dict[str, Any]) -> Optional[int]:
    ns = _as_float(_pan_get_module(pan_ds, ["cells", "series"]))
    np = _as_float(_pan_get_module(pan_ds, ["cells", "parallel"]))
    if ns is None or np is None:
        return None
    return int(round(ns * np))


def _pan_get_limit_vmax(pan_ds: Dict[str, Any]) -> Optional[float]:
    for p in (
        ["standard", "electrical", "limits", "vmax_iec_v"],
        ["standard", "electrical", "limits", "vmax_ul_v"],
        ["standard", "electrical", "limits", "vmax_v"],
    ):
        v = _as_float(_safe_get(pan_ds, p))
        if v is not None:
            return v
    return None


def _pan_get_bifaciality_factor(pan_ds: Dict[str, Any]) -> Optional[float]:
    return _as_float(_pan_get_module(pan_ds, ["bifaciality_factor"]))


def _pan_get_model_param(pan_ds: Dict[str, Any], key: str) -> Optional[float]:
    key_norm = key.strip().lower()

    # chemins principaux attendus
    candidate_paths = [
        ["standard", "electrical", "model_params", key],
        ["standard", "electrical", "model_params", key_norm],
        ["standard", "electrical", "model_params", key_norm.capitalize()],
        ["standard", "model_params", key],
        ["model_params", key],
    ]

    for path in candidate_paths:
        v = _as_float(_safe_get(pan_ds, path))
        if v is not None:
            return v

    # fallback: recherche globale dans le dict
    def recursive_search(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if str(k).strip().lower() == key_norm:
                    return _as_float(v)
                res = recursive_search(v)
                if res is not None:
                    return res
        return None

    return recursive_search(pan_ds)


def _pan_get_temp_coeffs(pan_ds: Dict[str, Any]) -> Dict[str, Optional[float]]:
    mu_isc_ma = _as_float(_safe_get(pan_ds, ["standard", "electrical", "temp_coeff", "mu_isc"]))
    mu_voc_mv = _as_float(_safe_get(pan_ds, ["standard", "electrical", "temp_coeff", "mu_voc_spec"]))
    gamma_pct = _as_float(_safe_get(pan_ds, ["standard", "electrical", "temp_coeff", "mu_pmp_req"]))

    isc = _pan_get_stc(pan_ds, "isc_a")
    voc = _pan_get_stc(pan_ds, "voc_v")

    alpha_pct = _pct_from_mu_and_ref(mu_isc_ma, isc, mu_unit="mA_per_C")
    beta_pct = _pct_from_mu_and_ref(mu_voc_mv, voc, mu_unit="mV_per_C")

    # Prefer already standardized percent coefficients if present
    for p in (
        ["standard", "electrical", "temp_coeff", "coeff_isc_pct_per_c"],
        ["standard", "electrical", "temp_coeff", "alpha_isc_pct_per_c"],
    ):
        v = _as_float(_safe_get(pan_ds, p))
        if v is not None:
            alpha_pct = v

    for p in (
        ["standard", "electrical", "temp_coeff", "coeff_voc_pct_per_c"],
        ["standard", "electrical", "temp_coeff", "beta_voc_pct_per_c"],
    ):
        v = _as_float(_safe_get(pan_ds, p))
        if v is not None:
            beta_pct = v

    for p in (
        ["standard", "electrical", "temp_coeff", "coeff_pmax_pct_per_c"],
        ["standard", "electrical", "temp_coeff", "gamma_pmax_pct_per_c"],
    ):
        v = _as_float(_safe_get(pan_ds, p))
        if v is not None:
            gamma_pct = v

    return {
        "alpha_isc_pct_per_c": alpha_pct,
        "mu_isc_ma_per_c": mu_isc_ma,
        "gamma_pmax_pct_per_c": gamma_pct,
        "beta_voc_pct_per_c": beta_pct,
        "mu_voc_spec_mv_per_c": mu_voc_mv,
    }


# -----------------------------------------------------------------------------
# Extraction: Datasheet variant + derived values
# -----------------------------------------------------------------------------

def _variant_power_int(v: Dict[str, Any]) -> Optional[int]:
    pc = _as_int_w(v.get("power_class_w"))
    if pc is not None:
        return pc
    return _as_int_w(_safe_get(v, ["nameplate", "pmax_w"]))


def _select_variant_strict(
    ds_data: Dict[str, Any],
    *,
    pan_model: Optional[str],
    pan_power_w_int: Optional[int],
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    STRICT selection:
      - power match must be exact integer W
      - if multiple variants share same power:
          require exact model match, else ambiguous -> None
    """
    variants: List[Dict[str, Any]] = ds_data.get("variants", []) or []
    debug: Dict[str, Any] = {
        "mode": None,
        "n_variants": len(variants),
        "target_power_w": pan_power_w_int,
        "candidates_power_match": 0,
        "selected_variant_id": None,
        "ambiguous_variants": [],
    }

    if not variants:
        debug["mode"] = "no_variants"
        return None, debug

    if pan_power_w_int is None:
        debug["mode"] = "missing_pan_power"
        return None, debug

    power_matches = [v for v in variants if _variant_power_int(v) == pan_power_w_int]
    debug["candidates_power_match"] = len(power_matches)

    if not power_matches:
        debug["mode"] = "no_power_match"
        return None, debug

    if len(power_matches) == 1:
        debug["mode"] = "power_match_unique"
        debug["selected_variant_id"] = power_matches[0].get("variant_id")
        return power_matches[0], debug

    pm = _norm_model(pan_model)
    if pm:
        for v in power_matches:
            if _norm_model(v.get("variant_id")) == pm:
                debug["mode"] = "power_and_model_match"
                debug["selected_variant_id"] = v.get("variant_id")
                return v, debug

    debug["mode"] = "power_match_ambiguous_no_model_match"
    debug["ambiguous_variants"] = [vv.get("variant_id") for vv in power_matches]
    return None, debug


def _ds_ctx_from_variant(ds_data: Dict[str, Any], variant: Dict[str, Any]) -> Dict[str, Any]:
    nameplate = variant.get("nameplate") or {}
    mech = ds_data.get("mechanical") or {}
    op = ds_data.get("operating") or {}
    temp = ds_data.get("temperature") or {}

    dims_mm = mech.get("dimensions_mm") or {}
    length_mm = _as_float(dims_mm.get("length"))
    width_mm = _as_float(dims_mm.get("width"))
    thickness_mm = _as_float(dims_mm.get("thickness"))

    isc = _as_float(nameplate.get("isc_a"))
    voc = _as_float(nameplate.get("voc_v"))
    vmp = _as_float(nameplate.get("vmp_v"))
    imp = _as_float(nameplate.get("imp_a"))

    alpha_pct = _as_float(temp.get("coeff_isc_pct_per_c"))
    beta_pct = _as_float(temp.get("coeff_voc_pct_per_c"))
    gamma_pct = _as_float(temp.get("coeff_pmax_pct_per_c"))

    mu_isc_ma = _mu_from_pct_and_ref(alpha_pct, isc, out_unit="mA_per_C")
    mu_voc_mv = _mu_from_pct_and_ref(beta_pct, voc, out_unit="mV_per_C")

    bif_pct = _as_float(op.get("bifaciality_pct"))
    bif_factor = (bif_pct / 100.0) if isinstance(bif_pct, (int, float)) else None

    rsh_default = _rshunt_default_pvsyst(vmp, isc, imp)

    return {
        "variant_id": variant.get("variant_id"),
        "power_w_int": _variant_power_int(variant),
        "stc_ref": {"gref_w_m2": 1000.0, "tref_c": 25.0},
        "sizes": {"length_mm": length_mm, "width_mm": width_mm, "thickness_mm": thickness_mm},
        "cells": {"total": mech.get("cells_count")},  # optional
        "limits": {"max_system_voltage_v": _as_float(op.get("max_system_voltage_v"))},
        "bifaciality_factor": bif_factor,
        "stc": {"isc_a": isc, "imp_a": imp, "voc_v": voc, "vmp_v": vmp},
        "temperature": {
            "alpha_isc_pct_per_c": alpha_pct,
            "mu_isc_ma_per_c": mu_isc_ma,
            "gamma_pmax_pct_per_c": gamma_pct,
            "beta_voc_pct_per_c": beta_pct,
            "mu_voc_spec_mv_per_c": mu_voc_mv,
        },
        "model_params": {"rshunt_default_ohm": rsh_default},
    }


# -----------------------------------------------------------------------------
# Checklist fields
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class ChecklistItem:
    section: str
    key: str
    label: str
    unit: str
    pan_get: Callable[[Dict[str, Any]], Any]
    ds_get: Callable[[Dict[str, Any]], Any]
    tol_abs: Optional[float] = None
    tol_pct: Optional[float] = None


def _build_checklist() -> List[ChecklistItem]:
    """
    Temp coeffs: 2 lignes par grandeur (même info, deux unités)
      - Isc: alpha (%/°C) + muIsc (mA/°C)
      - Voc: beta  (%/°C) + muVocSpec (mV/°C)
      - Pmax: gamma (%/°C) uniquement (pas d'équivalent absolu robuste sans Pmp)
    Chaque ligne compare PAN vs DS dans LA MÊME unité (conversion si nécessaire).
    """

    # --- Helpers: PAN values (preferred) ---
    def pan_mu_isc_ma(pan: Dict[str, Any]) -> Optional[float]:
        return _pan_get_temp_coeffs(pan).get("mu_isc_ma_per_c")

    def pan_alpha_isc_pct(pan: Dict[str, Any]) -> Optional[float]:
        return _pan_get_temp_coeffs(pan).get("alpha_isc_pct_per_c")

    def pan_mu_voc_mv(pan: Dict[str, Any]) -> Optional[float]:
        return _pan_get_temp_coeffs(pan).get("mu_voc_spec_mv_per_c")

    def pan_beta_voc_pct(pan: Dict[str, Any]) -> Optional[float]:
        return _pan_get_temp_coeffs(pan).get("beta_voc_pct_per_c")

    def pan_gamma_pmax_pct(pan: Dict[str, Any]) -> Optional[float]:
        return _pan_get_temp_coeffs(pan).get("gamma_pmax_pct_per_c")

    def pan_isc(pan: Dict[str, Any]) -> Optional[float]:
        return _pan_get_stc(pan, "isc_a")

    def pan_voc(pan: Dict[str, Any]) -> Optional[float]:
        return _pan_get_stc(pan, "voc_v")

    # --- Helpers: DS values (preferred) ---
    def ds_alpha_isc_pct(ds: Dict[str, Any]) -> Optional[float]:
        return _as_float(_safe_get(ds, ["temperature", "alpha_isc_pct_per_c"]))

    def ds_mu_isc_ma(ds: Dict[str, Any]) -> Optional[float]:
        return _as_float(_safe_get(ds, ["temperature", "mu_isc_ma_per_c"]))

    def ds_beta_voc_pct(ds: Dict[str, Any]) -> Optional[float]:
        return _as_float(_safe_get(ds, ["temperature", "beta_voc_pct_per_c"]))

    def ds_mu_voc_mv(ds: Dict[str, Any]) -> Optional[float]:
        return _as_float(_safe_get(ds, ["temperature", "mu_voc_spec_mv_per_c"]))

    def ds_gamma_pmax_pct(ds: Dict[str, Any]) -> Optional[float]:
        return _as_float(_safe_get(ds, ["temperature", "gamma_pmax_pct_per_c"]))

    def ds_isc(ds: Dict[str, Any]) -> Optional[float]:
        return _as_float(_safe_get(ds, ["stc", "isc_a"]))

    def ds_voc(ds: Dict[str, Any]) -> Optional[float]:
        return _as_float(_safe_get(ds, ["stc", "voc_v"]))

    # --- Conversions (always same unit output) ---
    # PAN -> %/°C: if PAN already has pct use it, else compute from mu + ref
    def pan_alpha_pct_out(pan: Dict[str, Any]) -> Optional[float]:
        v = pan_alpha_isc_pct(pan)
        if v is not None:
            return v
        return _pct_from_mu_and_ref(pan_mu_isc_ma(pan), pan_isc(pan), mu_unit="mA_per_C")

    def pan_beta_pct_out(pan: Dict[str, Any]) -> Optional[float]:
        v = pan_beta_voc_pct(pan)
        if v is not None:
            return v
        return _pct_from_mu_and_ref(pan_mu_voc_mv(pan), pan_voc(pan), mu_unit="mV_per_C")

    # PAN -> absolute: if PAN already has mu use it, else compute from pct + ref
    def pan_mu_isc_ma_out(pan: Dict[str, Any]) -> Optional[float]:
        v = pan_mu_isc_ma(pan)
        if v is not None:
            return v
        return _mu_from_pct_and_ref(pan_alpha_isc_pct(pan), pan_isc(pan), out_unit="mA_per_C")

    def pan_mu_voc_mv_out(pan: Dict[str, Any]) -> Optional[float]:
        v = pan_mu_voc_mv(pan)
        if v is not None:
            return v
        return _mu_from_pct_and_ref(pan_beta_voc_pct(pan), pan_voc(pan), out_unit="mV_per_C")

    # DS -> %/°C: DS is normally pct, but support absolute if ever present
    def ds_alpha_pct_out(ds: Dict[str, Any]) -> Optional[float]:
        v = ds_alpha_isc_pct(ds)
        if v is not None:
            return v
        return _pct_from_mu_and_ref(ds_mu_isc_ma(ds), ds_isc(ds), mu_unit="mA_per_C")

    def ds_beta_pct_out(ds: Dict[str, Any]) -> Optional[float]:
        v = ds_beta_voc_pct(ds)
        if v is not None:
            return v
        return _pct_from_mu_and_ref(ds_mu_voc_mv(ds), ds_voc(ds), mu_unit="mV_per_C")

    # DS -> absolute: compute from pct + ref if needed
    def ds_mu_isc_ma_out(ds: Dict[str, Any]) -> Optional[float]:
        v = ds_mu_isc_ma(ds)
        if v is not None:
            return v
        return _mu_from_pct_and_ref(ds_alpha_isc_pct(ds), ds_isc(ds), out_unit="mA_per_C")

    def ds_mu_voc_mv_out(ds: Dict[str, Any]) -> Optional[float]:
        v = ds_mu_voc_mv(ds)
        if v is not None:
            return v
        return _mu_from_pct_and_ref(ds_beta_voc_pct(ds), ds_voc(ds), out_unit="mV_per_C")

    return [
        # -----------------------------
        # Basic data
        # -----------------------------
        ChecklistItem(
            section="basic_data",
            key="gref",
            label="Reference Conditions - Gref",
            unit="W/m²",
            pan_get=lambda pan: _pan_get_stc_ref(pan, "irradiance_w_m2"),
            ds_get=lambda ds: _safe_get(ds, ["stc_ref", "gref_w_m2"]),
            tol_pct=0.0,
        ),
        ChecklistItem(
            section="basic_data",
            key="tref",
            label="Reference Conditions - Tref",
            unit="°C",
            pan_get=lambda pan: _pan_get_stc_ref(pan, "cell_temp_c"),
            ds_get=lambda ds: _safe_get(ds, ["stc_ref", "tref_c"]),
            tol_abs=0.0,
        ),

        # -----------------------------
        # Sizes and technology
        # -----------------------------
        ChecklistItem(
            section="sizes_tech",
            key="length_mm",
            label="Module length",
            unit="mm",
            pan_get=lambda pan: _to_mm(_as_float(_pan_get_module(pan, ["dimensions_m", "height"]))),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["sizes", "length_mm"])),
            tol_abs=1.0,
        ),
        ChecklistItem(
            section="sizes_tech",
            key="width_mm",
            label="Module width",
            unit="mm",
            pan_get=lambda pan: _to_mm(_as_float(_pan_get_module(pan, ["dimensions_m", "width"]))),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["sizes", "width_mm"])),
            tol_abs=1.0,
        ),
        ChecklistItem(
            section="sizes_tech",
            key="thickness_mm",
            label="Module thickness",
            unit="mm",
            pan_get=lambda pan: _to_mm(_as_float(_pan_get_module(pan, ["dimensions_m", "depth"]))),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["sizes", "thickness_mm"])),
            tol_abs=1.0,
        ),
        ChecklistItem(
            section="sizes_tech",
            key="cells_total",
            label="Total number of Cells",
            unit="-",
            pan_get=lambda pan: _pan_get_cells_total(pan),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["cells", "total"])),
            tol_abs=0.0,
        ),
        ChecklistItem(
            section="sizes_tech",
            key="vmax",
            label="Maximum Array Voltage",
            unit="V",
            pan_get=lambda pan: _pan_get_limit_vmax(pan),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["limits", "max_system_voltage_v"])),
            tol_abs=0.0,
        ),
        ChecklistItem(
            section="sizes_tech",
            key="bifaciality",
            label="Bifaciality",
            unit="-",
            pan_get=lambda pan: _pan_get_bifaciality_factor(pan),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["bifaciality_factor"])),
            tol_pct=2.0,
        ),

        # -----------------------------
        # Technical data (STC)
        # -----------------------------
        ChecklistItem(
            section="technical_stc",
            key="isc",
            label="Short circuit current - Isc",
            unit="A",
            pan_get=lambda pan: _pan_get_stc(pan, "isc_a"),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["stc", "isc_a"])),
            tol_pct=1.0,
        ),
        ChecklistItem(
            section="technical_stc",
            key="imp",
            label="Max power point current - Impp",
            unit="A",
            pan_get=lambda pan: _pan_get_stc(pan, "imp_a"),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["stc", "imp_a"])),
            tol_pct=1.0,
        ),
        ChecklistItem(
            section="technical_stc",
            key="voc",
            label="Open circuit Voltage - Voc",
            unit="V",
            pan_get=lambda pan: _pan_get_stc(pan, "voc_v"),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["stc", "voc_v"])),
            tol_pct=1.0,
        ),
        ChecklistItem(
            section="technical_stc",
            key="vmp",
            label="Max power point Voltage - Vmpp",
            unit="V",
            pan_get=lambda pan: _pan_get_stc(pan, "vmp_v"),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["stc", "vmp_v"])),
            tol_pct=1.0,
        ),

        # -----------------------------
        # Temperature characteristics (duplicated lines)
        # -----------------------------
        ChecklistItem(
            section="temp_char",
            key="alpha_isc_pct",
            label="Temperature coefficient of Isc - α",
            unit="%/°C",
            pan_get=lambda pan: pan_alpha_pct_out(pan),
            ds_get=lambda ds: ds_alpha_pct_out(ds),
            tol_abs=0.01,
        ),
        ChecklistItem(
            section="temp_char",
            key="mu_isc_ma",
            label="Temperature coefficient muIsc",
            unit="mA/°C",
            pan_get=lambda pan: pan_mu_isc_ma_out(pan),
            ds_get=lambda ds: ds_mu_isc_ma_out(ds),
            tol_pct=2.0,
        ),
        ChecklistItem(
            section="temp_char",
            key="gamma_pmax_pct",
            label="Temperature coefficient of Pmax - γ",
            unit="%/°C",
            pan_get=lambda pan: pan_gamma_pmax_pct(pan),
            ds_get=lambda ds: ds_gamma_pmax_pct(ds),
            tol_abs=0.02,
        ),
        ChecklistItem(
            section="temp_char",
            key="beta_voc_pct",
            label="Temperature coefficient of Voc - β",
            unit="%/°C",
            pan_get=lambda pan: pan_beta_pct_out(pan),
            ds_get=lambda ds: ds_beta_pct_out(ds),
            tol_abs=0.02,
        ),
        ChecklistItem(
            section="temp_char",
            key="mu_voc_mv",
            label="Temperature coefficient muVocSpec",
            unit="mV/°C",
            pan_get=lambda pan: pan_mu_voc_mv_out(pan),
            ds_get=lambda ds: ds_mu_voc_mv_out(ds),
            tol_pct=2.0,
        ),

        # -----------------------------
        # Additional
        # -----------------------------
        ChecklistItem(
            section="additional",
            key="rshunt",
            label="Shunt resistance (PVsyst default from STC)",
            unit="Ohm",
            pan_get=lambda pan: _pan_get_model_param(pan, "RShunt"),
            ds_get=lambda ds: _as_float(_safe_get(ds, ["model_params", "rshunt_default_ohm"])),
            tol_pct=25.0,
        ),
    ]


# -----------------------------------------------------------------------------
# Export (PDF + log)
# -----------------------------------------------------------------------------

def _write_log_txt(path: Path, result: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("PVInsight — Compare PAN vs Datasheet")
    lines.append("=" * 80)

    gen = result.get("generalities", {}) or {}
    lines.append("[GENERALITIES]")
    for k in (
        "analysis_datetime",
        "manufacturer_code",
        "pan_file",
        "datasheet_file",
        "pan_manufacturer",
        "pan_model",
        "pan_power_w_int",
        "datasheet_manufacturer",
        "datasheet_variant_id",
        "datasheet_power_w_int",
    ):
        if k in gen:
            lines.append(f"- {k}: {gen.get(k)}")

    proj = gen.get("project") or {}
    if isinstance(proj, dict) and proj:
        lines.append("\n[PROJECT]")
        for k in ("project_name", "project_no", "solar_engineer"):
            if proj.get(k):
                lines.append(f"- {k}: {proj.get(k)}")

    warns = result.get("warnings") or []
    if warns:
        lines.append("\n[WARNINGS]")
        for w in warns:
            lines.append(f"- {w}")

    comp = result.get("comparison", {}) or {}
    lines.append("\n[COMPARISON]")
    lines.append(f"- enabled: {comp.get('enabled')}")
    lines.append(f"- reason: {comp.get('reason')}")
    summ = comp.get("summary") or {}
    if isinstance(summ, dict):
        lines.append(f"- n_rows: {summ.get('n_rows')}")
        lines.append(f"- n_ok: {summ.get('n_ok')}")
        lines.append(f"- n_warn: {summ.get('n_warn')}")
        lines.append(f"- n_missing: {summ.get('n_missing')}")

    rows = comp.get("rows") or []
    if isinstance(rows, list) and rows:
        lines.append("\n[ROWS]")
        for r in rows:
            lines.append(
                f"- {r.get('section')}::{r.get('key')} | DS={r.get('datasheet')} | PAN={r.get('pan')} | "
                f"dAbs={r.get('deviation_abs')} | dPct={r.get('deviation_pct')} | status={r.get('status')}"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_pdf_report(path: Path, result: Dict[str, Any]) -> None:
    """
    PDF report — QC Inspection (PAN vs Datasheet)
    - Title: "Quality Control Inspection - Module PAN File"
    - Logo: assets/logo_company.png (top-right, small)
    - Generalities: Project info first + Date (dd/mm/yyyy) + Manufacturer + Module Type
    - Table: direct checklist rows (with units), header with background
    - IAM chart: Matplotlib PNG (bottom), with a title above
    """
    from datetime import datetime
    from pathlib import Path as _Path

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    # Matplotlib IAM renderer (you said you'll move it into iam_plot.py)
    # Expected function signature: iam_png_from_result(result: dict, title: str) -> Optional[bytes]
    from core.module.iam_plot import iam_png_from_result  # type: ignore

    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4

    # ----------------------------
    # Small helpers
    # ----------------------------
    def _fmt_date_ddmmyyyy(dt_str: Any) -> str:
        s = str(dt_str or "").strip()
        if not s:
            return "-"
        # common cases: "2026-02-12T10:22:33" or "2026-02-12 10:22:33"
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                d = datetime.strptime(s[: len(fmt)], fmt)
                return d.strftime("%d/%m/%Y")
            except Exception:
                pass
        # last resort: keep only date-like prefix if present
        if len(s) >= 10 and s[4] == "-" and s[7] == "-":
            return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
        return s

    def _center_section_title(txt: str, y: float) -> float:
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2.0, y, txt)
        return y - 6 * mm

    def _draw_kv_line(label: str, value: Any, y: float) -> float:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20 * mm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(55 * mm, y, str(value) if value not in (None, "") else "-")
        return y - 5 * mm

    def _hr(y: float) -> float:
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.6)
        c.line(20 * mm, y, w - 20 * mm, y)
        c.setStrokeColor(colors.black)
        return y - 4 * mm

    def _new_page_if_needed(y: float, min_y: float = 25 * mm) -> float:
        if y < min_y:
            c.showPage()
            return h - 20 * mm
        return y

    # ----------------------------
    # Header: title + logo (top-right)
    # ----------------------------
    header_height = 20 * mm
    y = h - 12 * mm

    # Ligne fine sous header
    def _header_line(ypos):
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.8)
        c.line(15 * mm, ypos, w - 15 * mm, ypos)
        c.setStrokeColor(colors.black)

    # Date (top-left)
    analysis_date = result.get("generalities", {}).get("analysis_datetime")
    formatted_date = _fmt_date_ddmmyyyy(analysis_date)

    c.setFont("Helvetica", 9)
    c.drawString(15 * mm, y, f"{formatted_date}")

    # Corporate title (center)
    c.setFont("Helvetica", 10)
    c.drawCentredString(
        w / 2,
        y,
        "Quality Assurance during Engineering of Solar PV Plants"
    )

    # Logo (top-right)
    logo_path = _Path("assets/logo_company.png")
    if logo_path.exists():
        try:
            logo_w = 25 * mm
            logo_h = 25 * mm
            c.drawImage(
                str(logo_path),
                w - 15 * mm - logo_w,
                y - 10 * mm,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    # Separation line
    _header_line(y - 8 * mm)

    # Move cursor below header
    y -= 16 * mm

    # -------------------------------------------------
    # REPORT TITLE
    # -------------------------------------------------
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(
        w / 2,
        y,
        "Quality Control Inspection - Module PAN File"
    )

    y -= 8 * mm
    y = _hr(y)

    # ----------------------------
    # Generalities (reduced, project first)
    # ----------------------------
    gen = result.get("generalities", {}) or {}
    proj = gen.get("project") or {}
    if not isinstance(proj, dict):
        proj = {}

    project_name = proj.get("project_name") or proj.get("project") or proj.get("name") or ""
    project_code = proj.get("project_code") or proj.get("project_no") or proj.get("code") or ""
    solar_engineer = proj.get("solar_engineer") or proj.get("engineer") or proj.get("user_name") or ""

    # Manufacturer: prefer PAN manufacturer if present
    manufacturer = (gen.get("datasheet_manufacturer") or gen.get("pan_manufacturer") or gen.get("manufacturer_code")) or "-"
    module_type = gen.get("pan_model") or "-"
    date_str = _fmt_date_ddmmyyyy(gen.get("analysis_datetime"))

    y = _center_section_title("GENERALITIES", y)
    y = _draw_kv_line("Project Name", project_name, y)
    y = _draw_kv_line("Project Code", project_code, y)
    y = _draw_kv_line("Solar Engineer", solar_engineer, y)
    y = _draw_kv_line("Date", date_str, y)
    y = _draw_kv_line("Manufacturer", manufacturer, y)
    y = _draw_kv_line("Module Type", module_type, y)
    y -= 1 * mm
    y = _hr(y)

    # ----------------------------
    # Table (Comparison rows)
    # ----------------------------
    y = _center_section_title("COMPARISON CHECKLIST", y)

    comp = result.get("comparison", {}) or {}
    enabled = bool(comp.get("enabled", False))
    rows = comp.get("rows") or []
    if not isinstance(rows, list):
        rows = []

    if not enabled:
        # Show reason and stop table
        reason = comp.get("reason") or "-"
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y, f"Comparison disabled: {reason}")
        y -= 6 * mm
    else:
        # Columns: Parameter | Unit | Datasheet | PAN | Delta (%) | Status
        headers = ["Parameter", "Unit", "Datasheet", "PAN", "Delta (%)", "Status"]

        # Table geometry
        x0 = 15 * mm
        table_w = w - 30 * mm
        col_w = [
            58 * mm,  # Parameter
            14 * mm,  # Unit
            34 * mm,  # Datasheet
            34 * mm,  # PAN
            18 * mm,  # Delta (%)
            15 * mm,  # Status
        ]
        # Normalize to available width if needed
        s = sum(col_w)
        if abs(s - table_w) > 1:
            scale = table_w / s
            col_w = [cw * scale for cw in col_w]

        row_h = 6.0 * mm
        header_h = 7.0 * mm

        def _draw_cell_text(x: float, y_top: float, w_: float, h_: float, txt: str, *, bold: bool = False) -> None:
            c.setFont("Helvetica-Bold" if bold else "Helvetica", 8.2 if bold else 8.0)
            # left padding
            c.drawString(x + 1.6 * mm, y_top - h_ + 2.1 * mm, (txt or "-")[:80])

        def _fmt_val(v: Any) -> str:
            if v is None or v == "":
                return "-"
            # numbers: keep readable
            if isinstance(v, (int, float)):
                # heuristic: big ints => no decimals; otherwise 3 decimals max
                if isinstance(v, int) or abs(v) >= 100:
                    return f"{v:,.0f}".replace(",", " ")
                return f"{v:.4f}".rstrip("0").rstrip(".")
            return str(v)

        def _fmt_pct(v: Any) -> str:
            if v is None or v == "":
                return "-"
            try:
                f = float(v)
                return f"{f:.2f}%"
            except Exception:
                return str(v)

        # Header background
        y = _new_page_if_needed(y, min_y=45 * mm)
        c.setFillColor(colors.HexColor("#E9EDF5"))
        c.rect(x0, y - header_h, table_w, header_h, fill=1, stroke=0)
        c.setFillColor(colors.black)

        # Header borders + texts
        c.setStrokeColor(colors.HexColor("#C7CEDB"))
        c.setLineWidth(0.6)
        x = x0
        for i, htxt in enumerate(headers):
            c.rect(x, y - header_h, col_w[i], header_h, fill=0, stroke=1)
            _draw_cell_text(x, y, col_w[i], header_h, htxt, bold=True)
            x += col_w[i]
        y -= header_h

        # Body rows
        c.setLineWidth(0.4)
        for r in rows:
            y = _new_page_if_needed(y, min_y=55 * mm)

            label = str(r.get("label") or r.get("key") or "-")
            unit = str(r.get("unit") or "-")
            ds_v = _fmt_val(r.get("datasheet"))
            pan_v = _fmt_val(r.get("pan"))
            dpct = _fmt_pct(r.get("deviation_pct"))
            status = str(r.get("status") or "-")

            # Row background (subtle zebra)
            if (rows.index(r) % 2) == 0:
                c.setFillColor(colors.whitesmoke)
                c.rect(x0, y - row_h, table_w, row_h, fill=1, stroke=0)
                c.setFillColor(colors.black)

            x = x0
            cells = [label, unit, ds_v, pan_v, dpct, status]
            for i, txt in enumerate(cells):
                c.setStrokeColor(colors.HexColor("#D7DCE7"))
                c.rect(x, y - row_h, col_w[i], row_h, fill=0, stroke=1)
                _draw_cell_text(x, y, col_w[i], row_h, txt, bold=False)
                x += col_w[i]

            y -= row_h

        y -= 2 * mm

    y = _hr(y)

    # ----------------------------
    # IAM chart (bottom) — larger, no section title
    # ----------------------------
    # Prefer profile name if available for chart title
    iam_title = "IAM"
    try:
        pan_only = result.get("pan_only") or {}
        std = (pan_only.get("standard") or {}) if isinstance(pan_only, dict) else {}
        iam = std.get("iam") or {}
        prof = iam.get("profile") or {}
        pname = prof.get("name") or ""
        if pname:
            iam_title = f"IAM {pname}"
    except Exception:
        pass

    # Render PNG via Matplotlib helper
    png = None
    try:
        png = iam_png_from_result(result, title=iam_title)
    except Exception:
        png = None

    if png:
        # If not enough room, move to a new page so the chart isn't cramped
        # We want a comfortable bottom margin with a larger chart.
        if y < 85 * mm:
            c.showPage()
            y = h - 20 * mm

        from io import BytesIO
        img = ImageReader(BytesIO(png))

        # Larger chart: wider + taller (but still compatible with header/table space)
        img_w = 150 * mm   # bigger width
        img_h = 70 * mm    # bigger height
        x0 = (w - img_w) / 2.0

        # Place it near bottom, leaving a clean bottom margin
        y0 = 18 * mm

        c.drawImage(
            img,
            x0,
            y0,
            width=img_w,
            height=img_h,
            preserveAspectRatio=True,
            mask="auto",
        )
    else:
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y, "IAM profile not available in PAN file.")
        y -= 6 * mm

    c.showPage()
    c.save()



def _generate_exports(run_dir: Path, result: Dict[str, Any]) -> Tuple[Path, Path]:
    pdf_path = run_dir / "compare_pan_vs_ds_report.pdf"
    log_path = run_dir / "compare_pan_vs_ds_log.txt"
    _write_pdf_report(pdf_path, result)
    _write_log_txt(log_path, result)
    return pdf_path, log_path


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def compare_pan_to_ds(
    pan: Union[BytesLike, Dict[str, Any]],
    ds: Union[BytesLike, Dict[str, Any]],
    *,
    manufacturer_code: str,
    outputs_dir: Union[str, Path],
    pan_source_name: str = "module.PAN",
    ds_source_name: str = "datasheet.pdf",
    cleanup_tmp_files: bool = False,
    project_info: Optional[Dict[str, str]] = None,  # {"project_name","project_no","solar_engineer"}
) -> Dict[str, Any]:
    """
    STRICT tool:
      - brand must match manufacturer_code (PAN + DS meta if available)
      - power must match exactly (integer W) between PAN and chosen DS variant
      - if DS power match is ambiguous -> require exact model match else skip comparison

    Always returns PAN-only package. If strict match fails, comparison is disabled.
    Also generates exports (PDF + log) in a dedicated run_dir under outputs_dir.
    """
    warnings: List[str] = []
    checklist = _build_checklist()

    mfr = (manufacturer_code or "").strip().lower()
    if mfr not in DS_READERS_BY_MFR:
        raise ValueError(f"Unknown manufacturer_code={manufacturer_code!r}. Expected one of: {sorted(DS_READERS_BY_MFR.keys())}")

    expected_token = EXPECTED_BRAND_TOKEN.get(mfr, "").strip().upper()

    run_dir = _make_run_dir(outputs_dir, tool_id="compare_pan_to_ds")

    # ---- Parse PAN
    if isinstance(pan, (bytes, bytearray)):
        pan_ds = read_pan_file(bytes(pan))
    else:
        pan_ds = pan

    pan_id = _extract_pan_identity(pan_ds)
    pan_manufacturer = pan_id.get("manufacturer")
    pan_model = pan_id.get("model")
    pan_power_w_int = pan_id.get("pmp_w_int")

    pan_mfr_norm = _norm_token(pan_manufacturer)
    brand_ok_pan = bool(expected_token) and (expected_token in pan_mfr_norm)
    if not brand_ok_pan:
        warnings.append(
            f"Brand mismatch (PAN): manufacturer={pan_manufacturer!r} inconsistent with manufacturer_code={manufacturer_code!r}."
        )

    # ---- Parse datasheet (bytes -> path -> dict)
    if isinstance(ds, (bytes, bytearray)):
        reader = DS_READERS_BY_MFR[mfr]
        ds_data = call_with_path(
            reader=reader,
            data=bytes(ds),
            source_name=ds_source_name,
            workdir=run_dir,
            default_suffix=".pdf",
            prefix="ds_",
            overwrite=False,
            cleanup=cleanup_tmp_files,
        )
    else:
        ds_data = ds

    # ---- Brand strict gate (DS meta manufacturer if available)
    ds_meta_mfr = _safe_get(ds_data, ["meta", "manufacturer"])
    ds_mfr_norm = _norm_token(ds_meta_mfr)
    brand_ok_ds = True
    if ds_meta_mfr and expected_token:
        brand_ok_ds = expected_token in ds_mfr_norm
        if not brand_ok_ds:
            warnings.append(
                f"Brand mismatch (Datasheet): manufacturer={ds_meta_mfr!r} inconsistent with manufacturer_code={manufacturer_code!r}."
            )

    ds_variants = ds_data.get("variants", []) or []
    ds_variant_ids = [v.get("variant_id") for v in ds_variants if isinstance(v, dict)]
    ds_power_classes = [_variant_power_int(v) for v in ds_variants if isinstance(v, dict)]
    ds_power_classes = [p for p in ds_power_classes if p is not None]

    # ---- Strict variant selection (power exact + resolve ambiguity only via model)
    best_variant, pick_dbg = _select_variant_strict(ds_data, pan_model=pan_model, pan_power_w_int=pan_power_w_int)

    comparison_enabled = True
    comparison_reason = "OK"

    if not brand_ok_pan:
        comparison_enabled = False
        comparison_reason = "PAN_BRAND_MISMATCH"
    if not brand_ok_ds:
        comparison_enabled = False
        comparison_reason = "DS_BRAND_MISMATCH"
    if best_variant is None:
        comparison_enabled = False
        comparison_reason = pick_dbg.get("mode") or "NO_MATCHING_VARIANT"
        warnings.append("No strict match in datasheet (brand/power/model). Comparison skipped (PAN-only).")

    # ---- Generalities (always)
    generalities = {
        "analysis_datetime": datetime.now().isoformat(timespec="seconds"),
        "manufacturer_code": manufacturer_code,
        "pan_file": pan_source_name,
        "datasheet_file": ds_source_name,
        "pan_manufacturer": pan_manufacturer,
        "pan_model": pan_model,
        "pan_power_w_int": pan_power_w_int,
        "project": project_info or {},
    }

    # ---- PAN-only package (always available)  ✅ FIXED
    pan_only = {"standard": pan_ds.get("standard", {}) or {}}

    # If comparison disabled, finalize result and export
    if not comparison_enabled:
        result = {
            "meta": {
                "tool": "compare_pan_to_ds",
                "version": "3.1",
                "run_dir": str(run_dir),
                "datasheet_schema": _safe_get(ds_data, ["meta", "schema"]),
                "datasheet_reader_id": _safe_get(ds_data, ["meta", "reader_id"]),
            },
            "warnings": warnings,
            "generalities": generalities,
            "comparison": {
                "enabled": False,
                "reason": comparison_reason,
                "variant_pick": pick_dbg,
                "available_variants": ds_variant_ids,
                "available_powers_w": ds_power_classes,
                "rows": [],
                "summary": {"n_rows": 0, "n_ok": 0, "n_warn": 0, "n_missing": 0},
            },
            "pan_only": pan_only,
            "graphs": {
                "iam": {
                    "available": bool(_safe_get(pan_only, ["standard", "iam", "profile", "points"])),  # ✅ FIXED
                    "source": "pan",
                },
            },
        }

        pdf_path, log_path = _generate_exports(run_dir, result)
        result["exports"] = {"pdf_path": str(pdf_path), "log_path": str(log_path)}
        return result

    # ---- Build DS context for checklist
    ds_ctx = _ds_ctx_from_variant(ds_data, best_variant)

    # Final strict power confirmation
    ds_power_w_int = ds_ctx.get("power_w_int")
    if pan_power_w_int is None or ds_power_w_int is None or pan_power_w_int != ds_power_w_int:
        warnings.append(f"Power mismatch after selection: PAN={pan_power_w_int} W vs DS={ds_power_w_int} W. Comparison skipped.")
        result = {
            "meta": {
                "tool": "compare_pan_to_ds",
                "version": "3.1",
                "run_dir": str(run_dir),
                "datasheet_schema": _safe_get(ds_data, ["meta", "schema"]),
                "datasheet_reader_id": _safe_get(ds_data, ["meta", "reader_id"]),
            },
            "warnings": warnings,
            "generalities": generalities,
            "comparison": {
                "enabled": False,
                "reason": "POWER_MISMATCH",
                "variant_pick": pick_dbg,
                "available_variants": ds_variant_ids,
                "available_powers_w": ds_power_classes,
                "rows": [],
                "summary": {"n_rows": 0, "n_ok": 0, "n_warn": 0, "n_missing": 0},
            },
            "pan_only": pan_only,
            "graphs": {
                "iam": {"available": bool(_safe_get(pan_only, ["standard", "iam", "profile", "points"])), "source": "pan"},
            },
        }
        pdf_path, log_path = _generate_exports(run_dir, result)
        result["exports"] = {"pdf_path": str(pdf_path), "log_path": str(log_path)}
        return result

    # enrich generalities with DS selection
    generalities.update(
        {
            "datasheet_manufacturer": _safe_get(ds_data, ["meta", "manufacturer"]),
            "datasheet_variant_id": ds_ctx.get("variant_id"),
            "datasheet_power_w_int": ds_power_w_int,
        }
    )

    # ---- Evaluate checklist rows
    rows: List[Dict[str, Any]] = []
    n_ok = 0
    n_warn = 0
    n_missing = 0

    for item in checklist:
        pan_raw = item.pan_get(pan_ds)
        ds_raw = item.ds_get(ds_ctx)

        pan_val = _as_float(pan_raw)
        ds_val = _as_float(ds_raw)

        d_abs, d_pct = _delta(pan_val, ds_val)

        status = "MISSING"
        if pan_val is None or ds_val is None:
            n_missing += 1
        else:
            status = "OK"
            if item.tol_abs is not None and d_abs is not None and abs(d_abs) > item.tol_abs:
                status = "WARN"
            if item.tol_pct is not None and d_pct is not None and abs(d_pct) > item.tol_pct:
                status = "WARN"

            if status == "OK":
                n_ok += 1
            else:
                n_warn += 1

        rows.append(
            {
                "section": item.section,
                "key": item.key,
                "label": item.label,
                "unit": item.unit,
                "datasheet": ds_raw,
                "pan": pan_raw,
                "deviation_abs": d_abs,
                "deviation_pct": d_pct,
                "status": status,
                "tol_abs": item.tol_abs,
                "tol_pct": item.tol_pct,
            }
        )

    result = {
        "meta": {
            "tool": "compare_pan_to_ds",
            "version": "3.1",
            "run_dir": str(run_dir),
            "datasheet_schema": _safe_get(ds_data, ["meta", "schema"]),
            "datasheet_reader_id": _safe_get(ds_data, ["meta", "reader_id"]),
        },
        "warnings": warnings,
        "generalities": generalities,
        "comparison": {
            "enabled": True,
            "reason": "OK",
            "variant_pick": pick_dbg,
            "available_variants": ds_variant_ids,
            "available_powers_w": ds_power_classes,
            "rows": rows,
            "summary": {"n_rows": len(rows), "n_ok": n_ok, "n_warn": n_warn, "n_missing": n_missing},
        },
        "pan_only": pan_only,
        "graphs": {
            "iam": {
                "available": bool(_safe_get(pan_only, ["standard", "iam", "profile", "points"])),  # ✅ FIXED
                "source": "pan",
            },
        },
    }

    pdf_path, log_path = _generate_exports(run_dir, result)
    result["exports"] = {"pdf_path": str(pdf_path), "log_path": str(log_path)}
    return result
