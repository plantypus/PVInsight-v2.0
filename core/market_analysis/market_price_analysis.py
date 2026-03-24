# core/market_analysis/market_price_analysis.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import numpy as np
import pandas as pd
import requests

from core.market_analysis.standardization import (
    BACKEND_ENERGY_UNIT,
    BACKEND_PRICE_UNIT,
    CanonicalMarketResult,
    CanonicalPVResult,
    standardize_energy_charts_price_payload,
)


# =============================================================================
# API CONFIG
# =============================================================================

ENERGY_CHARTS_BASE_URL = "https://api.energy-charts.info"
ENERGY_CHARTS_PRICE_ENDPOINT = "/price"
DEFAULT_LOCAL_TZ = "Europe/Paris"
DEFAULT_TIMEOUT = 30

SEASON_ORDER = ["winter", "spring", "summer", "autumn"]


# =============================================================================
# RESULT CONTAINERS
# =============================================================================

@dataclass
class MarketPVJoinResult:
    data: pd.DataFrame
    meta: Dict[str, Any]
    warnings: list[str]


@dataclass
class MarketPVAnalysisResult:
    merged_data: pd.DataFrame
    annual_indicators: Dict[str, Any]
    monthly_summary: pd.DataFrame
    seasonal_summary: pd.DataFrame
    market_profile_typical_daily: pd.DataFrame
    pv_profile_typical_daily: pd.DataFrame
    market_only_summary: Dict[str, Any]
    price_distribution_summary: Dict[str, Any]
    monthly_market_summary: pd.DataFrame
    seasonal_market_summary: pd.DataFrame
    meta: Dict[str, Any]
    warnings: list[str]


# =============================================================================
# API READ
# =============================================================================

def _default_request_get(
    url: str,
    *,
    params: Dict[str, Any],
    timeout: int = DEFAULT_TIMEOUT,
) -> requests.Response:
    return requests.get(url, params=params, timeout=timeout)


def _validate_input_params(
    *,
    bzn: str,
    start: str,
    end: str,
) -> None:
    if not str(bzn).strip():
        raise ValueError("Parameter 'bzn' is required.")
    if not str(start).strip():
        raise ValueError("Parameter 'start' is required.")
    if not str(end).strip():
        raise ValueError("Parameter 'end' is required.")


def _validate_api_payload_shape(payload: Dict[str, Any]) -> list[str]:
    warnings: list[str] = []

    for key in ("unix_seconds", "price"):
        if key not in payload:
            warnings.append(f"API payload missing expected key: '{key}'.")

    for key in ("unit", "license_info", "deprecated"):
        if key not in payload:
            warnings.append(f"API payload missing expected metadata key: '{key}'.")

    return warnings


def fetch_energy_charts_price_payload(
    *,
    bzn: str,
    start: str,
    end: str,
    timeout: int = DEFAULT_TIMEOUT,
    requester: Optional[Callable[..., Any]] = None,
) -> tuple[Dict[str, Any], Dict[str, Any], list[str]]:
    _validate_input_params(bzn=bzn, start=start, end=end)

    requester = requester or _default_request_get
    warnings: list[str] = []

    url = f"{ENERGY_CHARTS_BASE_URL}{ENERGY_CHARTS_PRICE_ENDPOINT}"
    params = {"bzn": bzn, "start": start, "end": end}

    request_meta = {
        "source": "energy_charts",
        "endpoint": ENERGY_CHARTS_PRICE_ENDPOINT,
        "request_url": url,
        "request_params": params,
    }

    try:
        response = requester(url, params=params, timeout=timeout)
    except Exception as exc:
        raise RuntimeError(f"Energy Charts API request failed: {exc}") from exc

    status_code = getattr(response, "status_code", None)
    if status_code != 200:
        response_text = getattr(response, "text", "")
        response_preview = response_text[:500] if isinstance(response_text, str) else ""
        raise RuntimeError(
            f"Energy Charts API returned HTTP {status_code}. "
            f"Response preview: {response_preview}"
        )

    try:
        payload = response.json()
    except Exception as exc:
        raise RuntimeError(f"Failed to decode JSON response from Energy Charts API: {exc}") from exc

    warnings.extend(_validate_api_payload_shape(payload))
    return payload, request_meta, warnings


def read_market_prices_from_api(
    *,
    bzn: str,
    start: str,
    end: str,
    local_tz: str = DEFAULT_LOCAL_TZ,
    timeout: int = DEFAULT_TIMEOUT,
    requester: Optional[Callable[..., Any]] = None,
) -> CanonicalMarketResult:
    payload, request_meta, warnings = fetch_energy_charts_price_payload(
        bzn=bzn,
        start=start,
        end=end,
        timeout=timeout,
        requester=requester,
    )

    result = standardize_energy_charts_price_payload(
        payload=payload,
        bzn=bzn,
        start=start,
        end=end,
        local_tz=local_tz,
        source_mode="api",
    )

    result.meta["request_url"] = request_meta["request_url"]
    result.meta["request_params"] = request_meta["request_params"]
    result.warnings = warnings + result.warnings
    return result


# =============================================================================
# SHARED HELPERS
# =============================================================================

def _safe_div(numerator: float, denominator: float) -> Optional[float]:
    if denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _build_month_day_hour_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["merge_month"] = out["timestamp"].dt.month.astype("int64")
    out["merge_day"] = out["timestamp"].dt.day.astype("int64")
    out["merge_hour"] = out["timestamp"].dt.hour.astype("int64")
    return out


def _sort_season_df(df: pd.DataFrame) -> pd.DataFrame:
    if "season" in df.columns:
        df = df.copy()
        df["season"] = pd.Categorical(df["season"], categories=SEASON_ORDER, ordered=True)
        df = df.sort_values("season").reset_index(drop=True)
    return df


def _hourly_price_variability_stats(group: pd.Series) -> pd.Series:
    mean_val = float(group.mean())
    median_val = float(group.median())
    std_val = float(group.std(ddof=0)) if len(group) > 1 else 0.0
    p10 = float(group.quantile(0.10))
    p25 = float(group.quantile(0.25))
    p75 = float(group.quantile(0.75))
    p90 = float(group.quantile(0.90))
    cv_pct = None
    if abs(mean_val) >= 5.0:
        cv_pct = 100.0 * std_val / abs(mean_val)

    return pd.Series(
        {
            "price_mean_eur_per_mwh": mean_val,
            "price_median_eur_per_mwh": median_val,
            "price_std_eur_per_mwh": std_val,
            "price_p10_eur_per_mwh": p10,
            "price_p25_eur_per_mwh": p25,
            "price_p75_eur_per_mwh": p75,
            "price_p90_eur_per_mwh": p90,
            "price_cv_pct": cv_pct,
        }
    )


def _get_market_analysis_df(market_result: CanonicalMarketResult) -> pd.DataFrame:
    df = market_result.data_analysis.copy()
    if df.empty:
        raise ValueError("Market analysis DataFrame is empty.")
    return df


def _get_pv_analysis_df(pv_result: CanonicalPVResult) -> pd.DataFrame:
    df = pv_result.data_analysis.copy()
    if df.empty:
        raise ValueError("PV analysis DataFrame is empty.")
    return df


# =============================================================================
# JOIN MARKET + PV
# =============================================================================

def join_market_and_pv(
    market_result: CanonicalMarketResult,
    pv_result: CanonicalPVResult,
) -> MarketPVJoinResult:
    """
    Join market data with PV profile using month-day-hour only.

    Important:
    - market provides the true calendar/timestamp reference
    - PV provides the annual hourly profile
    - PV year is ignored
    - both sides must already be harmonized to the analysis time step
    """
    warnings: list[str] = []

    market_df = _get_market_analysis_df(market_result)
    pv_df = _get_pv_analysis_df(pv_result)

    market_step = market_result.meta.get("time_step_minutes_analysis")
    pv_step = pv_result.meta.get("time_step_minutes_analysis")
    if market_step != pv_step:
        raise ValueError(
            f"Market/PV analysis time steps differ: market={market_step} min, pv={pv_step} min."
        )

    market_df = _build_month_day_hour_key(market_df)
    pv_df = _build_month_day_hour_key(pv_df)

    pv_keep = [
        "merge_month",
        "merge_day",
        "merge_hour",
        "e_grid_mwh",
        "is_positive_generation",
        "variant_label",
    ]
    pv_join = pv_df[pv_keep].copy()

    dup_mask = pv_join.duplicated(
        subset=["merge_month", "merge_day", "merge_hour"],
        keep="first",
    )
    n_dup = int(dup_mask.sum())
    if n_dup > 0:
        warnings.append(
            f"{n_dup} duplicated PV month-day-hour key(s) detected in analysis data. Keeping first occurrence."
        )
        pv_join = pv_join.loc[~dup_mask].copy()

    merged = pd.merge(
        market_df,
        pv_join,
        on=["merge_month", "merge_day", "merge_hour"],
        how="left",
    )

    n_missing = int(merged["e_grid_mwh"].isna().sum())
    if n_missing > 0:
        warnings.append(
            f"{n_missing} market analysis row(s) could not be matched to PV profile on month-day-hour."
        )

    if merged["e_grid_mwh"].notna().sum() == 0:
        raise ValueError(
            "Market/PV merge produced no valid matched rows. Check month-day-hour alignment."
        )

    merged["e_grid_mwh"] = merged["e_grid_mwh"].fillna(0.0)
    merged["is_positive_generation"] = merged["is_positive_generation"].fillna(False)
    merged["variant_label"] = merged["variant_label"].fillna(
        pv_result.meta.get("variant_label", "")
    )

    # Raw value without negative-price curtailment rule
    merged["market_value_eur_raw"] = merged["e_grid_mwh"] * merged["price_eur_per_mwh"]

    # Negative-price curtailment rule
    merged["e_grid_curtailed_negative_mwh"] = np.where(
        merged["price_eur_per_mwh"] < 0.0,
        merged["e_grid_mwh"],
        0.0,
    )

    merged["e_grid_injected_mwh"] = np.where(
        merged["price_eur_per_mwh"] < 0.0,
        0.0,
        merged["e_grid_mwh"],
    )

    merged["market_value_eur"] = merged["e_grid_injected_mwh"] * merged["price_eur_per_mwh"]

    merged["has_negative_price_and_generation"] = (
        (merged["price_eur_per_mwh"] < 0.0) & (merged["e_grid_mwh"] > 0.0)
    )

    high_price_threshold = float(merged["price_eur_per_mwh"].quantile(0.75))
    merged["high_price_quartile_threshold"] = high_price_threshold
    merged["is_high_price_hour"] = merged["price_eur_per_mwh"] >= high_price_threshold
    merged["e_grid_on_high_price_hours_mwh"] = np.where(
        merged["is_high_price_hour"],
        merged["e_grid_mwh"],
        0.0,
    )

    merged = merged.sort_values("timestamp").reset_index(drop=True)

    meta = {
        "schema_version": "market_pv_join_v2",
        "join_key": "month-day-hour",
        "timestamp_reference": "market_analysis",
        "backend_energy_unit": BACKEND_ENERGY_UNIT,
        "backend_price_unit": BACKEND_PRICE_UNIT,
        "backend_value_unit": "EUR",
        "analysis_time_step_minutes": market_step,
        "market_rows_analysis": int(len(market_df)),
        "pv_rows_analysis": int(len(pv_df)),
        "joined_rows": int(len(merged)),
        "variant_label": pv_result.meta.get("variant_label", ""),
        "bzn": market_result.meta.get("bzn", ""),
        "time_start": merged["timestamp"].min().isoformat(),
        "time_end": merged["timestamp"].max().isoformat(),
        "market_resampled": bool(market_result.meta.get("resampled_to_analysis_step", False)),
        "pv_resampled": bool(pv_result.meta.get("resampled_to_analysis_step", False)),
    }

    warnings = market_result.warnings + pv_result.warnings + warnings

    ordered_cols = [
        "timestamp",
        "date",
        "year",
        "month",
        "day",
        "hour",
        "season",
        "bzn",
        "price_eur_per_mwh",
        "is_negative_price",
        "e_grid_mwh",
        "e_grid_injected_mwh",
        "e_grid_curtailed_negative_mwh",
        "is_positive_generation",
        "has_negative_price_and_generation",
        "is_high_price_hour",
        "e_grid_on_high_price_hours_mwh",
        "market_value_eur_raw",
        "market_value_eur",
        "variant_label",
        "source",
        "source_mode",
    ]
    merged = merged[[c for c in ordered_cols if c in merged.columns]]

    return MarketPVJoinResult(data=merged, meta=meta, warnings=warnings)


# =============================================================================
# CORE INDICATORS
# =============================================================================

def compute_basic_market_pv_indicators(join_result: MarketPVJoinResult) -> Dict[str, Any]:
    df = join_result.data

    if df.empty:
        raise ValueError("Joined market/PV DataFrame is empty.")

    energy_theoretical_mwh = float(df["e_grid_mwh"].sum())
    energy_injected_mwh = float(df["e_grid_injected_mwh"].sum())
    energy_curtailed_negative_mwh = float(df["e_grid_curtailed_negative_mwh"].sum())

    market_value_eur = float(df["market_value_eur"].sum())
    market_value_raw_eur = float(df["market_value_eur_raw"].sum())

    avg_market_price_eur_per_mwh = float(df["price_eur_per_mwh"].mean())
    capture_price_eur_per_mwh = _safe_div(market_value_eur, energy_injected_mwh)
    capture_rate = (
        _safe_div(capture_price_eur_per_mwh, avg_market_price_eur_per_mwh)
        if capture_price_eur_per_mwh is not None
        else None
    )

    negative_hours_market = int((df["price_eur_per_mwh"] < 0.0).sum())
    negative_days_market = int(df.loc[df["price_eur_per_mwh"] < 0.0, "date"].nunique())
    negative_hours_with_generation = int(df["has_negative_price_and_generation"].sum())
    negative_days_with_generation = int(
        df.loc[df["has_negative_price_and_generation"], "date"].nunique()
    )

    curtailed_share_pct = (
        100.0 * energy_curtailed_negative_mwh / energy_theoretical_mwh
        if energy_theoretical_mwh > 0
        else None
    )

    energy_on_high_price_hours_mwh = float(df["e_grid_on_high_price_hours_mwh"].sum())
    high_price_energy_share_pct = (
        100.0 * energy_on_high_price_hours_mwh / energy_theoretical_mwh
        if energy_theoretical_mwh > 0
        else None
    )

    return {
        "energy_theoretical_mwh": energy_theoretical_mwh,
        "energy_injected_mwh": energy_injected_mwh,
        "energy_curtailed_negative_mwh": energy_curtailed_negative_mwh,
        "market_value_eur": market_value_eur,
        "market_value_raw_eur": market_value_raw_eur,
        "avg_market_price_eur_per_mwh": avg_market_price_eur_per_mwh,
        "capture_price_eur_per_mwh": capture_price_eur_per_mwh,
        "capture_rate": capture_rate,
        "negative_hours_market": negative_hours_market,
        "negative_days_market": negative_days_market,
        "negative_hours_with_generation": negative_hours_with_generation,
        "negative_days_with_generation": negative_days_with_generation,
        "curtailed_share_pct": curtailed_share_pct,
        "energy_on_high_price_hours_mwh": energy_on_high_price_hours_mwh,
        "high_price_energy_share_pct": high_price_energy_share_pct,
    }


# =============================================================================
# MARKET-ONLY ANALYSIS
# =============================================================================

def compute_market_only_summary(market_result: CanonicalMarketResult) -> Dict[str, Any]:
    df = _get_market_analysis_df(market_result)

    return {
        "n_rows": int(len(df)),
        "price_mean_eur_per_mwh": float(df["price_eur_per_mwh"].mean()),
        "price_median_eur_per_mwh": float(df["price_eur_per_mwh"].median()),
        "price_min_eur_per_mwh": float(df["price_eur_per_mwh"].min()),
        "price_max_eur_per_mwh": float(df["price_eur_per_mwh"].max()),
        "price_p10_eur_per_mwh": float(df["price_eur_per_mwh"].quantile(0.10)),
        "price_p90_eur_per_mwh": float(df["price_eur_per_mwh"].quantile(0.90)),
        "negative_hours": int((df["price_eur_per_mwh"] < 0.0).sum()),
        "negative_days": int(df.loc[df["price_eur_per_mwh"] < 0.0, "date"].nunique()),
        "time_step_minutes_analysis": market_result.meta.get("time_step_minutes_analysis"),
    }


def compute_price_distribution_summary(market_result: CanonicalMarketResult) -> Dict[str, Any]:
    df = _get_market_analysis_df(market_result)
    price = df["price_eur_per_mwh"]

    return {
        "hours_below_0": int((price < 0).sum()),
        "hours_0_to_25": int(((price >= 0) & (price < 25)).sum()),
        "hours_25_to_50": int(((price >= 25) & (price < 50)).sum()),
        "hours_50_to_100": int(((price >= 50) & (price < 100)).sum()),
        "hours_above_100": int((price >= 100).sum()),
    }


def compute_monthly_market_summary(market_result: CanonicalMarketResult) -> pd.DataFrame:
    df = _get_market_analysis_df(market_result)

    grouped = df.groupby("month", dropna=False).agg(
        price_mean_eur_per_mwh=("price_eur_per_mwh", "mean"),
        price_median_eur_per_mwh=("price_eur_per_mwh", "median"),
        price_min_eur_per_mwh=("price_eur_per_mwh", "min"),
        price_max_eur_per_mwh=("price_eur_per_mwh", "max"),
        negative_hours=("is_negative_price", "sum"),
        negative_days=("date", lambda s: s[df.loc[s.index, "is_negative_price"]].nunique()),
        n_hours=("price_eur_per_mwh", "size"),
    ).reset_index()

    grouped["negative_hour_share_pct"] = 100.0 * grouped["negative_hours"] / grouped["n_hours"]
    return grouped.sort_values("month").reset_index(drop=True)


def compute_seasonal_market_summary(market_result: CanonicalMarketResult) -> pd.DataFrame:
    df = _get_market_analysis_df(market_result)

    grouped = df.groupby("season", dropna=False).agg(
        price_mean_eur_per_mwh=("price_eur_per_mwh", "mean"),
        price_median_eur_per_mwh=("price_eur_per_mwh", "median"),
        price_min_eur_per_mwh=("price_eur_per_mwh", "min"),
        price_max_eur_per_mwh=("price_eur_per_mwh", "max"),
        negative_hours=("is_negative_price", "sum"),
        negative_days=("date", lambda s: s[df.loc[s.index, "is_negative_price"]].nunique()),
        n_hours=("price_eur_per_mwh", "size"),
    ).reset_index()

    grouped["negative_hour_share_pct"] = 100.0 * grouped["negative_hours"] / grouped["n_hours"]
    return _sort_season_df(grouped)


# =============================================================================
# MONTHLY / SEASONAL CROSS ANALYSIS
# =============================================================================

def compute_monthly_summary(join_result: MarketPVJoinResult) -> pd.DataFrame:
    df = join_result.data.copy()

    grouped = df.groupby("month", dropna=False).agg(
        price_mean_eur_per_mwh=("price_eur_per_mwh", "mean"),
        energy_theoretical_mwh=("e_grid_mwh", "sum"),
        energy_injected_mwh=("e_grid_injected_mwh", "sum"),
        energy_curtailed_negative_mwh=("e_grid_curtailed_negative_mwh", "sum"),
        market_value_eur=("market_value_eur", "sum"),
        market_value_raw_eur=("market_value_eur_raw", "sum"),
        negative_hours_market=("is_negative_price", "sum"),
        negative_hours_with_generation=("has_negative_price_and_generation", "sum"),
        days_in_month=("date", "nunique"),
        negative_days_market=("date", lambda s: s[df.loc[s.index, "is_negative_price"]].nunique()),
        negative_days_with_generation=("date", lambda s: s[df.loc[s.index, "has_negative_price_and_generation"]].nunique()),
        energy_on_high_price_hours_mwh=("e_grid_on_high_price_hours_mwh", "sum"),
    ).reset_index()

    grouped["capture_price_eur_per_mwh"] = grouped.apply(
        lambda r: _safe_div(r["market_value_eur"], r["energy_injected_mwh"]),
        axis=1,
    )
    grouped["capture_rate"] = grouped.apply(
        lambda r: _safe_div(r["capture_price_eur_per_mwh"], r["price_mean_eur_per_mwh"]),
        axis=1,
    )
    grouped["curtailed_share_pct"] = grouped.apply(
        lambda r: 100.0 * r["energy_curtailed_negative_mwh"] / r["energy_theoretical_mwh"]
        if r["energy_theoretical_mwh"] > 0
        else None,
        axis=1,
    )
    grouped["high_price_energy_share_pct"] = grouped.apply(
        lambda r: 100.0 * r["energy_on_high_price_hours_mwh"] / r["energy_theoretical_mwh"]
        if r["energy_theoretical_mwh"] > 0
        else None,
        axis=1,
    )
    grouped["avg_curtailed_per_day_mwh"] = grouped.apply(
        lambda r: _safe_div(r["energy_curtailed_negative_mwh"], r["days_in_month"]),
        axis=1,
    )
    grouped["avg_curtailed_per_impacted_day_mwh"] = grouped.apply(
        lambda r: _safe_div(r["energy_curtailed_negative_mwh"], r["negative_days_with_generation"]),
        axis=1,
    )

    return grouped.sort_values("month").reset_index(drop=True)


def compute_seasonal_summary(join_result: MarketPVJoinResult) -> pd.DataFrame:
    df = join_result.data.copy()

    grouped = df.groupby("season", dropna=False).agg(
        price_mean_eur_per_mwh=("price_eur_per_mwh", "mean"),
        energy_theoretical_mwh=("e_grid_mwh", "sum"),
        energy_injected_mwh=("e_grid_injected_mwh", "sum"),
        energy_curtailed_negative_mwh=("e_grid_curtailed_negative_mwh", "sum"),
        market_value_eur=("market_value_eur", "sum"),
        market_value_raw_eur=("market_value_eur_raw", "sum"),
        negative_hours_market=("is_negative_price", "sum"),
        negative_hours_with_generation=("has_negative_price_and_generation", "sum"),
        negative_days_market=("date", lambda s: s[df.loc[s.index, "is_negative_price"]].nunique()),
        negative_days_with_generation=("date", lambda s: s[df.loc[s.index, "has_negative_price_and_generation"]].nunique()),
        energy_on_high_price_hours_mwh=("e_grid_on_high_price_hours_mwh", "sum"),
    ).reset_index()

    grouped["capture_price_eur_per_mwh"] = grouped.apply(
        lambda r: _safe_div(r["market_value_eur"], r["energy_injected_mwh"]),
        axis=1,
    )
    grouped["capture_rate"] = grouped.apply(
        lambda r: _safe_div(r["capture_price_eur_per_mwh"], r["price_mean_eur_per_mwh"]),
        axis=1,
    )
    grouped["curtailed_share_pct"] = grouped.apply(
        lambda r: 100.0 * r["energy_curtailed_negative_mwh"] / r["energy_theoretical_mwh"]
        if r["energy_theoretical_mwh"] > 0
        else None,
        axis=1,
    )
    grouped["high_price_energy_share_pct"] = grouped.apply(
        lambda r: 100.0 * r["energy_on_high_price_hours_mwh"] / r["energy_theoretical_mwh"]
        if r["energy_theoretical_mwh"] > 0
        else None,
        axis=1,
    )

    return _sort_season_df(grouped)


# =============================================================================
# TYPICAL DAILY PROFILES
# =============================================================================

def compute_market_typical_daily_profile(join_result: MarketPVJoinResult) -> pd.DataFrame:
    df = join_result.data.copy()

    out = (
        df.groupby("hour", dropna=False)["price_eur_per_mwh"]
        .apply(_hourly_price_variability_stats)
        .unstack()
        .reset_index()
        .sort_values("hour")
        .reset_index(drop=True)
    )

    return out


def compute_pv_typical_daily_profile(join_result: MarketPVJoinResult) -> pd.DataFrame:
    df = join_result.data.copy()

    grouped = df.groupby("hour", dropna=False).agg(
        e_grid_mean_mwh=("e_grid_mwh", "mean"),
        e_grid_median_mwh=("e_grid_mwh", "median"),
        e_grid_p25_mwh=("e_grid_mwh", lambda s: float(s.quantile(0.25))),
        e_grid_p75_mwh=("e_grid_mwh", lambda s: float(s.quantile(0.75))),
        e_grid_injected_mean_mwh=("e_grid_injected_mwh", "mean"),
        e_grid_injected_median_mwh=("e_grid_injected_mwh", "median"),
        curtailed_negative_mean_mwh=("e_grid_curtailed_negative_mwh", "mean"),
        price_mean_eur_per_mwh=("price_eur_per_mwh", "mean"),
    ).reset_index()

    return grouped.sort_values("hour").reset_index(drop=True)


# =============================================================================
# COMPARISON-READY INSIGHTS FOR ONE VARIANT
# =============================================================================

def compute_variant_positioning_indicators(join_result: MarketPVJoinResult) -> Dict[str, Any]:
    df = join_result.data.copy()

    energy_total_mwh = float(df["e_grid_mwh"].sum())
    energy_high_price_mwh = float(df["e_grid_on_high_price_hours_mwh"].sum())
    energy_negative_price_mwh = float(df["e_grid_curtailed_negative_mwh"].sum())

    return {
        "energy_total_mwh": energy_total_mwh,
        "energy_high_price_mwh": energy_high_price_mwh,
        "energy_high_price_share_pct": (
            100.0 * energy_high_price_mwh / energy_total_mwh if energy_total_mwh > 0 else None
        ),
        "energy_negative_price_mwh": energy_negative_price_mwh,
        "energy_negative_price_share_pct": (
            100.0 * energy_negative_price_mwh / energy_total_mwh if energy_total_mwh > 0 else None
        ),
    }


# =============================================================================
# HIGH-LEVEL ORCHESTRATION
# =============================================================================

def run_market_pv_analysis(
    market_result: CanonicalMarketResult,
    pv_result: CanonicalPVResult,
) -> MarketPVAnalysisResult:
    join_result = join_market_and_pv(market_result, pv_result)

    annual_indicators = compute_basic_market_pv_indicators(join_result)
    monthly_summary = compute_monthly_summary(join_result)
    seasonal_summary = compute_seasonal_summary(join_result)

    market_profile_typical_daily = compute_market_typical_daily_profile(join_result)
    pv_profile_typical_daily = compute_pv_typical_daily_profile(join_result)

    market_only_summary = compute_market_only_summary(market_result)
    price_distribution_summary = compute_price_distribution_summary(market_result)
    monthly_market_summary = compute_monthly_market_summary(market_result)
    seasonal_market_summary = compute_seasonal_market_summary(market_result)
    positioning = compute_variant_positioning_indicators(join_result)

    meta = dict(join_result.meta)
    meta["analysis_scope"] = "market_pv_single_variant_v2"
    meta["variant_label"] = pv_result.meta.get("variant_label", "")
    meta["positioning_indicators"] = positioning
    meta["market_original_rows"] = market_result.meta.get("n_rows_original")
    meta["market_analysis_rows"] = market_result.meta.get("n_rows_analysis")
    meta["pv_original_rows"] = pv_result.meta.get("n_rows_original")
    meta["pv_analysis_rows"] = pv_result.meta.get("n_rows_analysis")
    meta["market_time_step_minutes_original"] = market_result.meta.get("time_step_minutes_original")
    meta["pv_time_step_minutes_original"] = pv_result.meta.get("time_step_minutes_original")
    meta["analysis_time_step_minutes"] = market_result.meta.get("time_step_minutes_analysis")

    warnings = join_result.warnings

    return MarketPVAnalysisResult(
        merged_data=join_result.data,
        annual_indicators=annual_indicators,
        monthly_summary=monthly_summary,
        seasonal_summary=seasonal_summary,
        market_profile_typical_daily=market_profile_typical_daily,
        pv_profile_typical_daily=pv_profile_typical_daily,
        market_only_summary=market_only_summary,
        price_distribution_summary=price_distribution_summary,
        monthly_market_summary=monthly_market_summary,
        seasonal_market_summary=seasonal_market_summary,
        meta=meta,
        warnings=warnings,
    )


# =============================================================================
# DEBUG HELPERS
# =============================================================================

def debug_print_join_result(result: MarketPVJoinResult, n: int = 5) -> None:
    print("=" * 80)
    print("META")
    for k, v in result.meta.items():
        print(f"- {k}: {v}")

    print("=" * 80)
    print("WARNINGS")
    if result.warnings:
        for w in result.warnings:
            print(f"- {w}")
    else:
        print("- none")

    print("=" * 80)
    print("DATA HEAD")
    print(result.data.head(n))


def debug_print_analysis_result(result: MarketPVAnalysisResult, n: int = 5) -> None:
    print("=" * 80)
    print("META")
    for k, v in result.meta.items():
        print(f"- {k}: {v}")

    print("=" * 80)
    print("WARNINGS")
    if result.warnings:
        for w in result.warnings:
            print(f"- {w}")
    else:
        print("- none")

    print("=" * 80)
    print("ANNUAL INDICATORS")
    for k, v in result.annual_indicators.items():
        print(f"- {k}: {v}")

    print("=" * 80)
    print("MERGED DATA HEAD")
    print(result.merged_data.head(n))

    print("=" * 80)
    print("MONTHLY SUMMARY")
    print(result.monthly_summary.head(12))

    print("=" * 80)
    print("SEASONAL SUMMARY")
    print(result.seasonal_summary)

    print("=" * 80)
    print("MARKET TYPICAL DAILY PROFILE")
    print(result.market_profile_typical_daily.head(24))

    print("=" * 80)
    print("PV TYPICAL DAILY PROFILE")
    print(result.pv_profile_typical_daily.head(24))