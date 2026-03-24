# core/market_analysis/standardization.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from utils.readers.hourly_results import read_hourly_from_bytes


# =============================================================================
# CENTRALIZED CONVENTIONS
# =============================================================================

SCHEMA_VERSION_MARKET = "market_prices_v2"
SCHEMA_VERSION_PV = "pv_hourly_v2"

BACKEND_PRICE_UNIT = "EUR/MWh"
BACKEND_ENERGY_UNIT = "MWh"
ANALYSIS_TIME_STEP_MINUTES = 60

SEASON_MAP = {
    12: "winter",
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "autumn",
    10: "autumn",
    11: "autumn",
}

CANONICAL_TIME_COLS = [
    "timestamp",
    "date",
    "year",
    "month",
    "day",
    "hour",
    "season",
]

CANONICAL_MARKET_COLS = CANONICAL_TIME_COLS + [
    "bzn",
    "price_eur_per_mwh",
    "is_negative_price",
    "source",
    "source_mode",
]

CANONICAL_PV_COLS = CANONICAL_TIME_COLS + [
    "e_grid_mwh",
    "is_positive_generation",
    "variant_label",
    "source",
]


# =============================================================================
# STANDARD RESULT CONTAINERS
# =============================================================================

@dataclass
class CanonicalMarketResult:
    data_original: pd.DataFrame
    data_analysis: pd.DataFrame
    meta: Dict[str, Any]
    warnings: List[str]


@dataclass
class CanonicalPVResult:
    data_original: pd.DataFrame
    data_analysis: pd.DataFrame
    meta: Dict[str, Any]
    warnings: List[str]


# =============================================================================
# SHARED HELPERS
# =============================================================================

def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return []


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_unit_text(value: Any) -> str:
    return _normalize_text(value).lower().replace(" ", "")


def _enrich_time_columns(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    out = df.copy()
    out["date"] = out[timestamp_col].dt.date.astype(str)
    out["year"] = out[timestamp_col].dt.year.astype("int64")
    out["month"] = out[timestamp_col].dt.month.astype("int64")
    out["day"] = out[timestamp_col].dt.day.astype("int64")
    out["hour"] = out[timestamp_col].dt.hour.astype("int64")
    out["season"] = out["month"].map(SEASON_MAP)
    return out


def _drop_duplicate_timestamps(
    df: pd.DataFrame,
    *,
    warnings: List[str],
    label: str,
) -> pd.DataFrame:
    out = df.copy()
    dup_mask = out["timestamp"].duplicated(keep="first")
    n_dup = int(dup_mask.sum())
    if n_dup > 0:
        warnings.append(f"{n_dup} duplicated {label} timestamp(s) detected. Keeping first occurrence.")
        out = out.loc[~dup_mask].copy()
    return out


def _build_empty_market_result(meta: Dict[str, Any], warnings: List[str]) -> CanonicalMarketResult:
    empty = pd.DataFrame()
    return CanonicalMarketResult(
        data_original=empty,
        data_analysis=empty,
        meta=meta,
        warnings=warnings,
    )


def _build_empty_pv_result(meta: Dict[str, Any], warnings: List[str]) -> CanonicalPVResult:
    empty = pd.DataFrame()
    return CanonicalPVResult(
        data_original=empty,
        data_analysis=empty,
        meta=meta,
        warnings=warnings,
    )


# =============================================================================
# TIME STEP DETECTION
# =============================================================================

def infer_time_step_minutes(
    timestamp_series: pd.Series,
) -> Dict[str, Any]:
    """
    Infer time step from a datetime series.

    Returns a dict with:
    - time_step_minutes
    - time_step_hours
    - is_regular
    - n_unique_steps
    - detected_steps_minutes
    - method
    """
    s = pd.to_datetime(timestamp_series, errors="coerce")
    s = s.dropna().sort_values()

    if len(s) < 2:
        return {
            "time_step_minutes": None,
            "time_step_hours": None,
            "is_regular": False,
            "n_unique_steps": 0,
            "detected_steps_minutes": [],
            "method": "insufficient_data",
        }

    deltas = s.diff().dropna()
    delta_minutes = (deltas.dt.total_seconds() / 60.0).round(6)

    if delta_minutes.empty:
        return {
            "time_step_minutes": None,
            "time_step_hours": None,
            "is_regular": False,
            "n_unique_steps": 0,
            "detected_steps_minutes": [],
            "method": "insufficient_data",
        }

    counts = delta_minutes.value_counts()
    dominant_step = float(counts.index[0])
    unique_steps = sorted(float(x) for x in counts.index.tolist())

    return {
        "time_step_minutes": dominant_step,
        "time_step_hours": dominant_step / 60.0,
        "is_regular": len(unique_steps) == 1,
        "n_unique_steps": len(unique_steps),
        "detected_steps_minutes": unique_steps,
        "method": "mode_of_deltas",
    }


# =============================================================================
# ENERGY / POWER CONVERSION
# =============================================================================

def _get_energy_factor_to_mwh(unit_raw: str) -> Tuple[float, str]:
    unit_norm = _normalize_unit_text(unit_raw)

    if unit_norm == "wh":
        return 1e-6, "Wh"
    if unit_norm == "kwh":
        return 1e-3, "kWh"
    if unit_norm == "mwh":
        return 1.0, "MWh"

    raise ValueError(f"Unsupported energy unit for conversion to MWh: '{unit_raw}'.")


def _convert_power_to_mwh(series: pd.Series, unit_raw: str, dt_hours: float) -> Tuple[pd.Series, str]:
    unit_norm = _normalize_unit_text(unit_raw)

    if unit_norm == "kw":
        return pd.to_numeric(series, errors="coerce") * dt_hours / 1000.0, "kW"
    if unit_norm == "mw":
        return pd.to_numeric(series, errors="coerce") * dt_hours, "MW"

    raise ValueError(f"Unsupported power unit for conversion to MWh: '{unit_raw}'.")


def _convert_egrid_to_mwh(
    series: pd.Series,
    *,
    unit_raw: str,
    dt_hours: float,
) -> Tuple[pd.Series, str, str]:
    """
    Convert E_Grid to canonical MWh.

    Supports:
    - energy units: Wh, kWh, MWh
    - power units: kW, MW   -> converted using dt_hours
    """
    unit_norm = _normalize_unit_text(unit_raw)

    if unit_norm in {"wh", "kwh", "mwh"}:
        factor, detected = _get_energy_factor_to_mwh(unit_raw)
        return pd.to_numeric(series, errors="coerce") * factor, detected, "energy_unit_direct"

    if unit_norm in {"kw", "mw"}:
        converted, detected = _convert_power_to_mwh(series, unit_raw, dt_hours)
        return converted, detected, f"power_x_dt({dt_hours}h)"

    raise ValueError(f"Unsupported E_Grid unit for conversion to MWh: '{unit_raw}'.")


# =============================================================================
# MARKET HARMONIZATION
# =============================================================================

def harmonize_market_to_analysis_step(
    df_original: pd.DataFrame,
    *,
    analysis_step_minutes: int = ANALYSIS_TIME_STEP_MINUTES,
) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    warnings: List[str] = []

    if df_original.empty:
        return df_original.copy(), {
            "time_step_minutes_original": None,
            "time_step_minutes_analysis": analysis_step_minutes,
            "resampled_to_analysis_step": False,
            "resampling_method": None,
        }, warnings

    out = df_original.copy().sort_values("timestamp").reset_index(drop=True)

    ts_info = infer_time_step_minutes(out["timestamp"])
    original_step = ts_info["time_step_minutes"]

    if original_step is None:
        warnings.append("Could not infer market time step.")
        return out, {
            "time_step_minutes_original": None,
            "time_step_minutes_analysis": analysis_step_minutes,
            "resampled_to_analysis_step": False,
            "resampling_method": None,
        }, warnings

    if not ts_info["is_regular"]:
        warnings.append(
            f"Irregular market time steps detected: {ts_info['detected_steps_minutes']}. "
            f"Using dominant step {original_step} min."
        )

    if original_step == analysis_step_minutes:
        return out, {
            "time_step_minutes_original": original_step,
            "time_step_hours_original": original_step / 60.0,
            "time_step_minutes_analysis": analysis_step_minutes,
            "time_step_hours_analysis": analysis_step_minutes / 60.0,
            "resampled_to_analysis_step": False,
            "resampling_method": None,
        }, warnings

    # Market prices -> hourly mean
    tmp = out.copy()
    tmp = tmp.set_index("timestamp").sort_index()

    agg_map = {
        "price_eur_per_mwh": "mean",
        "bzn": "first",
        "source": "first",
        "source_mode": "first",
    }

    if "timestamp_local" in tmp.columns:
        agg_map["timestamp_local"] = "first"
    if "timestamp_utc" in tmp.columns:
        agg_map["timestamp_utc"] = "first"
    if "unix_seconds" in tmp.columns:
        agg_map["unix_seconds"] = "first"

    resampled = tmp.resample(f"{analysis_step_minutes}min").agg(agg_map).reset_index()

    resampled = _enrich_time_columns(resampled, "timestamp")
    resampled["is_negative_price"] = resampled["price_eur_per_mwh"] < 0.0
    resampled = resampled.sort_values("timestamp").reset_index(drop=True)

    warnings.append(
        f"Market data resampled from {original_step} min to {analysis_step_minutes} min using hourly mean price."
    )

    keep_cols = [c for c in CANONICAL_MARKET_COLS + ["timestamp_local", "timestamp_utc", "unix_seconds"] if c in resampled.columns]
    return resampled[keep_cols], {
        "time_step_minutes_original": original_step,
        "time_step_hours_original": original_step / 60.0,
        "time_step_minutes_analysis": analysis_step_minutes,
        "time_step_hours_analysis": analysis_step_minutes / 60.0,
        "resampled_to_analysis_step": True,
        "resampling_method": "mean_to_hourly",
    }, warnings


# =============================================================================
# PV HARMONIZATION
# =============================================================================

def harmonize_pv_to_analysis_step(
    df_original: pd.DataFrame,
    *,
    e_grid_unit_raw: str,
    analysis_step_minutes: int = ANALYSIS_TIME_STEP_MINUTES,
) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    warnings: List[str] = []

    if df_original.empty:
        return df_original.copy(), {
            "time_step_minutes_original": None,
            "time_step_minutes_analysis": analysis_step_minutes,
            "resampled_to_analysis_step": False,
            "resampling_method": None,
            "energy_conversion_basis": None,
        }, warnings

    out = df_original.copy().sort_values("timestamp").reset_index(drop=True)

    ts_info = infer_time_step_minutes(out["timestamp"])
    original_step = ts_info["time_step_minutes"]

    if original_step is None:
        raise ValueError("Could not infer PV time step.")

    if not ts_info["is_regular"]:
        warnings.append(
            f"Irregular PV time steps detected: {ts_info['detected_steps_minutes']}. "
            f"Using dominant step {original_step} min."
        )

    dt_hours = original_step / 60.0

    if "e_grid_raw" not in out.columns:
        raise ValueError("PV original data must contain 'e_grid_raw' for harmonization.")

    e_grid_mwh_step, egrid_unit_detected, conversion_basis = _convert_egrid_to_mwh(
        out["e_grid_raw"],
        unit_raw=e_grid_unit_raw,
        dt_hours=dt_hours,
    )

    work = pd.DataFrame({
        "timestamp": pd.to_datetime(out["timestamp"], errors="coerce"),
        "e_grid_mwh": e_grid_mwh_step,
        "variant_label": out["variant_label"] if "variant_label" in out.columns else "",
        "source": out["source"] if "source" in out.columns else "pvsyst_hourly_results",
    }).dropna(subset=["timestamp"])

    if original_step == analysis_step_minutes:
        work = _enrich_time_columns(work, "timestamp")
        work["is_positive_generation"] = work["e_grid_mwh"].fillna(0.0) > 0.0
        work = work.sort_values("timestamp").reset_index(drop=True)
        warnings.append("PV time step is already hourly; no resampling applied.")
        return work[CANONICAL_PV_COLS], {
            "time_step_minutes_original": original_step,
            "time_step_hours_original": dt_hours,
            "time_step_minutes_analysis": analysis_step_minutes,
            "time_step_hours_analysis": analysis_step_minutes / 60.0,
            "resampled_to_analysis_step": False,
            "resampling_method": None,
            "energy_conversion_basis": conversion_basis,
            "e_grid_unit_detected": egrid_unit_detected,
        }, warnings

    # PV energies -> sum to hourly
    resampled = (
        work.set_index("timestamp")
        .sort_index()
        .resample(f"{analysis_step_minutes}min")
        .agg({
            "e_grid_mwh": "sum",
            "variant_label": "first",
            "source": "first",
        })
        .reset_index()
    )

    resampled = _enrich_time_columns(resampled, "timestamp")
    resampled["is_positive_generation"] = resampled["e_grid_mwh"].fillna(0.0) > 0.0
    resampled = resampled.sort_values("timestamp").reset_index(drop=True)

    warnings.append(
        f"PV data resampled from {original_step} min to {analysis_step_minutes} min after converting {e_grid_unit_raw} to MWh using dt={dt_hours} h."
    )

    return resampled[CANONICAL_PV_COLS], {
        "time_step_minutes_original": original_step,
        "time_step_hours_original": dt_hours,
        "time_step_minutes_analysis": analysis_step_minutes,
        "time_step_hours_analysis": analysis_step_minutes / 60.0,
        "resampled_to_analysis_step": True,
        "resampling_method": "sum_energy_to_hourly",
        "energy_conversion_basis": conversion_basis,
        "e_grid_unit_detected": egrid_unit_detected,
    }, warnings


# =============================================================================
# MARKET STANDARDIZATION
# =============================================================================

def _build_market_meta(
    *,
    bzn: str,
    start: str,
    end: str,
    source_mode: str,
    raw_unit: str,
    license_info: str,
    deprecated: bool,
    local_tz: str,
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_MARKET,
        "source": "energy_charts",
        "source_mode": source_mode,
        "endpoint": "/price",
        "bzn": bzn,
        "start": start,
        "end": end,
        "backend_price_unit": BACKEND_PRICE_UNIT,
        "unit_raw": raw_unit,
        "license_info": license_info,
        "deprecated": deprecated,
        "local_timezone": local_tz,
        "analysis_time_step_minutes": ANALYSIS_TIME_STEP_MINUTES,
        "time_basis_note": (
            "Market timestamps are converted from unix_seconds (UTC) to local timezone, "
            "then stored as canonical local naive timestamps in 'timestamp'."
        ),
    }


def standardize_energy_charts_price_payload(
    payload: Dict[str, Any],
    *,
    bzn: str,
    start: str,
    end: str,
    local_tz: str = "Europe/Paris",
    source_mode: str = "api",
) -> CanonicalMarketResult:
    warnings: List[str] = []

    unix_seconds = _safe_list(payload.get("unix_seconds"))
    prices = _safe_list(payload.get("price"))
    raw_unit = _normalize_text(payload.get("unit"))
    license_info = _normalize_text(payload.get("license_info"))
    deprecated = bool(payload.get("deprecated", False))

    meta = _build_market_meta(
        bzn=bzn,
        start=start,
        end=end,
        source_mode=source_mode,
        raw_unit=raw_unit,
        license_info=license_info,
        deprecated=deprecated,
        local_tz=local_tz,
    )

    if deprecated:
        warnings.append("Energy Charts endpoint /price is flagged as deprecated.")

    if not unix_seconds:
        warnings.append("Payload contains no unix_seconds values.")
        return _build_empty_market_result(meta, warnings)

    if not prices:
        warnings.append("Payload contains no price values.")
        return _build_empty_market_result(meta, warnings)

    n = min(len(unix_seconds), len(prices))
    if len(unix_seconds) != len(prices):
        warnings.append(
            f"Length mismatch between unix_seconds ({len(unix_seconds)}) and price ({len(prices)}). Using shortest length."
        )

    df = pd.DataFrame({
        "unix_seconds": pd.to_numeric(pd.Series(unix_seconds[:n]), errors="coerce"),
        "price_eur_per_mwh": pd.to_numeric(pd.Series(prices[:n]), errors="coerce"),
    }).dropna(subset=["unix_seconds", "price_eur_per_mwh"])

    if df.empty:
        warnings.append("No valid market rows remain after numeric conversion.")
        return _build_empty_market_result(meta, warnings)

    ts_utc = pd.to_datetime(df["unix_seconds"], unit="s", utc=True)
    ts_local = ts_utc.dt.tz_convert(local_tz)

    df["timestamp_utc"] = ts_utc
    df["timestamp_local"] = ts_local
    df["timestamp"] = df["timestamp_local"].dt.tz_localize(None)

    df = _enrich_time_columns(df, "timestamp")
    df["bzn"] = bzn
    df["is_negative_price"] = df["price_eur_per_mwh"] < 0.0
    df["source"] = "energy_charts"
    df["source_mode"] = source_mode

    df = df.sort_values("timestamp").reset_index(drop=True)
    df = _drop_duplicate_timestamps(df, warnings=warnings, label="market")

    keep_cols = [c for c in CANONICAL_MARKET_COLS + ["timestamp_local", "timestamp_utc", "unix_seconds"] if c in df.columns]
    data_original = df[keep_cols].copy()

    data_analysis, harmon_meta, harmon_warnings = harmonize_market_to_analysis_step(data_original)
    warnings.extend(harmon_warnings)

    meta.update(harmon_meta)
    meta["n_rows_original"] = int(len(data_original))
    meta["n_rows_analysis"] = int(len(data_analysis))
    if not data_original.empty:
        meta["time_start_original"] = data_original["timestamp"].min().isoformat()
        meta["time_end_original"] = data_original["timestamp"].max().isoformat()
    if not data_analysis.empty:
        meta["time_start_analysis"] = data_analysis["timestamp"].min().isoformat()
        meta["time_end_analysis"] = data_analysis["timestamp"].max().isoformat()
        meta["negative_hours_analysis"] = int(data_analysis["is_negative_price"].sum())

    unit_norm = _normalize_unit_text(raw_unit)
    if raw_unit and unit_norm not in {"eur/mwh", "eur/mwh."}:
        warnings.append(f"Unexpected market price unit returned by API: '{raw_unit}'.")

    return CanonicalMarketResult(
        data_original=data_original,
        data_analysis=data_analysis,
        meta=meta,
        warnings=warnings,
    )


# =============================================================================
# PVSYST STANDARDIZATION
# =============================================================================

def _build_pv_meta(
    *,
    variant_label: Optional[str],
    source_name: str,
    general_info: Dict[str, Any],
    units_map: Dict[str, Any],
    e_grid_unit_raw: str,
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_PV,
        "source": "pvsyst_hourly_results",
        "source_mode": source_name,
        "variant_label": variant_label or general_info.get("Variant_name", ""),
        "pvsyst_version": general_info.get("PVSyst_version", ""),
        "simulation_date": general_info.get("Simulation_date", ""),
        "project_file": general_info.get("Project_file", ""),
        "project_code": general_info.get("Project_code", ""),
        "site_name": general_info.get("Site_name", ""),
        "meteo_name": general_info.get("Meteo_name", ""),
        "variant_name": general_info.get("Variant_name", ""),
        "units_map": units_map,
        "backend_energy_unit": BACKEND_ENERGY_UNIT,
        "e_grid_unit_raw": e_grid_unit_raw,
        "analysis_time_step_minutes": ANALYSIS_TIME_STEP_MINUTES,
        "time_basis_note": (
            "PVSyst timestamps are parsed as local naive timestamps. "
            "The year may be technical (e.g. 1990) and is not used for market join."
        ),
    }


def standardize_pvsyst_hourly_from_bytes(
    source: bytes,
    *,
    variant_label: Optional[str] = None,
    source_name: str = "bytes",
) -> CanonicalPVResult:
    warnings: List[str] = []

    general_info, df_raw, units_map = read_hourly_from_bytes(source)

    e_grid_unit_raw = _normalize_text(units_map.get("E_Grid"))
    meta = _build_pv_meta(
        variant_label=variant_label,
        source_name=source_name,
        general_info=general_info,
        units_map=units_map,
        e_grid_unit_raw=e_grid_unit_raw,
    )

    if df_raw.empty:
        warnings.append("PVSyst hourly DataFrame is empty after parsing.")
        return _build_empty_pv_result(meta, warnings)

    if "E_Grid" not in df_raw.columns:
        raise ValueError("Missing mandatory PVSyst column 'E_Grid'.")

    if not isinstance(df_raw.index, pd.DatetimeIndex):
        raise ValueError("PVSyst DataFrame index is not a DatetimeIndex.")

    if not e_grid_unit_raw:
        raise ValueError("Missing unit for E_Grid. Cannot standardize PV data.")

    tmp = pd.DataFrame(index=df_raw.index.copy())
    tmp["e_grid_raw"] = pd.to_numeric(df_raw["E_Grid"], errors="coerce")
    tmp = tmp.reset_index()

    first_col = tmp.columns[0]
    tmp = tmp.rename(columns={first_col: "timestamp"})
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
    tmp = tmp.dropna(subset=["timestamp"]).copy()

    tmp["variant_label"] = variant_label or general_info.get("Variant_name", "")
    tmp["source"] = "pvsyst_hourly_results"

    if tmp.empty:
        warnings.append("No valid PV rows remain after timestamp normalization.")
        return _build_empty_pv_result(meta, warnings)

    tmp = tmp.sort_values("timestamp").reset_index(drop=True)
    tmp = _drop_duplicate_timestamps(tmp, warnings=warnings, label="pv")

    data_original = tmp.copy()

    data_analysis, harmon_meta, harmon_warnings = harmonize_pv_to_analysis_step(
        data_original,
        e_grid_unit_raw=e_grid_unit_raw,
    )
    warnings.extend(harmon_warnings)

    meta.update(harmon_meta)
    meta["n_rows_original"] = int(len(data_original))
    meta["n_rows_analysis"] = int(len(data_analysis))
    if not data_original.empty:
        meta["time_start_original"] = data_original["timestamp"].min().isoformat()
        meta["time_end_original"] = data_original["timestamp"].max().isoformat()
    if not data_analysis.empty:
        meta["time_start_analysis"] = data_analysis["timestamp"].min().isoformat()
        meta["time_end_analysis"] = data_analysis["timestamp"].max().isoformat()
        meta["positive_generation_hours_analysis"] = int(data_analysis["is_positive_generation"].sum())
        meta["e_grid_sum_mwh_analysis"] = float(data_analysis["e_grid_mwh"].sum(skipna=True))

    return CanonicalPVResult(
        data_original=data_original,
        data_analysis=data_analysis,
        meta=meta,
        warnings=warnings,
    )