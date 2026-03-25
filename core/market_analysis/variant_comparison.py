# core/market_analysis/variant_comparison.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from core.market_analysis.market_price_analysis import MarketPVAnalysisResult

SCHEMA_VERSION = "variant_comparison_v1"
SEASON_ORDER = ["winter", "spring", "summer", "autumn"]


@dataclass
class VariantComparisonResult:
    annual_comparison: Dict[str, Any]
    monthly_comparison: pd.DataFrame
    seasonal_comparison: pd.DataFrame
    conclusions: List[str]
    meta: Dict[str, Any]
    warnings: List[str]


# =============================================================================
# Helpers
# =============================================================================

def _safe_delta_pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or a == 0:
        return None
    return 100.0 * (b - a) / a


def _sort_season_df(df: pd.DataFrame) -> pd.DataFrame:
    if "season" in df.columns:
        out = df.copy()
        out["season"] = pd.Categorical(out["season"], categories=SEASON_ORDER, ordered=True)
        out = out.sort_values("season").reset_index(drop=True)
        return out
    return df


def _build_annual_metric_row(
    key: str,
    a_value: Any,
    b_value: Any,
) -> Dict[str, Any]:
    delta_abs = None
    delta_pct = None

    if isinstance(a_value, (int, float)) and isinstance(b_value, (int, float)):
        delta_abs = b_value - a_value
        delta_pct = _safe_delta_pct(float(a_value), float(b_value))

    return {
        "metric": key,
        "variant_a": a_value,
        "variant_b": b_value,
        "delta_b_minus_a": delta_abs,
        "delta_pct_b_vs_a": delta_pct,
    }


def _prefix_columns(df: pd.DataFrame, prefix: str, key_col: str) -> pd.DataFrame:
    rename_map = {c: f"{prefix}{c}" for c in df.columns if c != key_col}
    return df.rename(columns=rename_map)


def _compare_grouped_tables(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    *,
    key_col: str,
) -> pd.DataFrame:
    a = df_a.copy()
    b = df_b.copy()

    if key_col not in a.columns:
        raise ValueError(f"Missing key column '{key_col}' in variant A grouped table.")
    if key_col not in b.columns:
        raise ValueError(f"Missing key column '{key_col}' in variant B grouped table.")

    a = _prefix_columns(a, "a_", key_col)
    b = _prefix_columns(b, "b_", key_col)

    merged = pd.merge(a, b, on=key_col, how="outer")

    common_metric_roots = [
        "price_mean_eur_per_mwh",
        "energy_theoretical_mwh",
        "energy_injected_mwh",
        "energy_curtailed_negative_mwh",
        "market_value_eur",
        "market_value_raw_eur",
        "negative_hours_market",
        "negative_hours_with_generation",
        "negative_days_market",
        "negative_days_with_generation",
        "capture_price_eur_per_mwh",
        "capture_rate",
        "curtailed_share_pct",
        "energy_on_high_price_hours_mwh",
        "high_price_energy_share_pct",
        "avg_curtailed_per_day_mwh",
        "avg_curtailed_per_impacted_day_mwh",
    ]

    for root in common_metric_roots:
        col_a = f"a_{root}"
        col_b = f"b_{root}"
        if col_a in merged.columns and col_b in merged.columns:
            merged[f"delta_{root}_b_minus_a"] = merged[col_b] - merged[col_a]
            merged[f"delta_{root}_pct_b_vs_a"] = merged.apply(
                lambda r: _safe_delta_pct(r[col_a], r[col_b]),
                axis=1,
            )

    return merged


def _generate_conclusions(
    annual_a: Dict[str, Any],
    annual_b: Dict[str, Any],
    *,
    label_a: str,
    label_b: str,
) -> List[Dict[str, Any]]:
    conclusions: List[Dict[str, Any]] = []

    a_value = annual_a.get("market_value_eur")
    b_value = annual_b.get("market_value_eur")
    if a_value is not None and b_value is not None:
        if b_value > a_value:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_MARKET_VALUE",
                "params": {"better": label_b, "other": label_a},
            })
        elif b_value < a_value:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_MARKET_VALUE",
                "params": {"better": label_a, "other": label_b},
            })
        else:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_EQUAL_MARKET_VALUE",
                "params": {"label_a": label_a, "label_b": label_b},
            })

    a_cap = annual_a.get("capture_price_eur_per_mwh")
    b_cap = annual_b.get("capture_price_eur_per_mwh")
    if a_cap is not None and b_cap is not None:
        if b_cap > a_cap:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_CAPTURE_PRICE",
                "params": {"better": label_b, "other": label_a},
            })
        elif b_cap < a_cap:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_CAPTURE_PRICE",
                "params": {"better": label_a, "other": label_b},
            })

    a_neg = annual_a.get("energy_curtailed_negative_mwh")
    b_neg = annual_b.get("energy_curtailed_negative_mwh")
    if a_neg is not None and b_neg is not None:
        if b_neg < a_neg:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_NEGATIVE_EXPOSURE",
                "params": {"better": label_b, "other": label_a},
            })
        elif b_neg > a_neg:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_NEGATIVE_EXPOSURE",
                "params": {"better": label_a, "other": label_b},
            })

    a_hp = annual_a.get("high_price_energy_share_pct")
    b_hp = annual_b.get("high_price_energy_share_pct")
    if a_hp is not None and b_hp is not None:
        if b_hp > a_hp:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_HIGH_PRICE_ALIGNMENT",
                "params": {"better": label_b, "other": label_a},
            })
        elif b_hp < a_hp:
            conclusions.append({
                "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_HIGH_PRICE_ALIGNMENT",
                "params": {"better": label_a, "other": label_b},
            })

    a_energy = annual_a.get("energy_theoretical_mwh")
    b_energy = annual_b.get("energy_theoretical_mwh")
    if a_energy is not None and b_energy is not None and a_value is not None and b_value is not None:
        energy_delta_pct = _safe_delta_pct(a_energy, b_energy)
        value_delta_pct = _safe_delta_pct(a_value, b_value)
        if energy_delta_pct is not None and value_delta_pct is not None:
            if b_energy > a_energy and b_value > a_value:
                if value_delta_pct >= energy_delta_pct:
                    conclusions.append({
                        "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_ENERGY_TO_VALUE_FULL",
                        "params": {"better": label_b, "other": label_a},
                    })
                else:
                    conclusions.append({
                        "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_ENERGY_TO_VALUE_PARTIAL",
                        "params": {"better": label_b, "other": label_a},
                    })

    if not conclusions:
        conclusions.append({
            "key": "MARKET_ANALYSIS_COMPARE_CONCLUSION_NONE",
            "params": {},
        })

    return conclusions

# =============================================================================
# Main comparison
# =============================================================================

def compare_market_pv_variants(
    analysis_result_a: MarketPVAnalysisResult,
    analysis_result_b: MarketPVAnalysisResult,
    *,
    variant_label_a: Optional[str] = None,
    variant_label_b: Optional[str] = None,
) -> VariantComparisonResult:
    warnings: List[str] = []

    annual_a = analysis_result_a.annual_indicators
    annual_b = analysis_result_b.annual_indicators

    label_a = (
        variant_label_a
        or analysis_result_a.meta.get("variant_label")
        or analysis_result_a.merged_data["variant_label"].dropna().iloc[0]
        if not analysis_result_a.merged_data.empty and "variant_label" in analysis_result_a.merged_data.columns
        else "Variant A"
    )
    label_b = (
        variant_label_b
        or analysis_result_b.meta.get("variant_label")
        or analysis_result_b.merged_data["variant_label"].dropna().iloc[0]
        if not analysis_result_b.merged_data.empty and "variant_label" in analysis_result_b.merged_data.columns
        else "Variant B"
    )

    bzn_a = analysis_result_a.meta.get("bzn")
    bzn_b = analysis_result_b.meta.get("bzn")
    if bzn_a != bzn_b:
        warnings.append(f"Bidding zones differ between variants: A={bzn_a}, B={bzn_b}.")

    annual_metrics_keys = [
        "energy_theoretical_mwh",
        "energy_injected_mwh",
        "energy_curtailed_negative_mwh",
        "market_value_eur",
        "market_value_raw_eur",
        "avg_market_price_eur_per_mwh",
        "capture_price_eur_per_mwh",
        "capture_rate",
        "negative_hours_market",
        "negative_days_market",
        "negative_hours_with_generation",
        "negative_days_with_generation",
        "curtailed_share_pct",
        "energy_on_high_price_hours_mwh",
        "high_price_energy_share_pct",
    ]

    annual_rows = []
    for key in annual_metrics_keys:
        annual_rows.append(_build_annual_metric_row(key, annual_a.get(key), annual_b.get(key)))

    annual_comparison = {
        "variant_label_a": label_a,
        "variant_label_b": label_b,
        "metrics_table": annual_rows,
        "summary": {
            "better_for_market_value": (
                label_b if annual_b.get("market_value_eur", 0) > annual_a.get("market_value_eur", 0)
                else label_a
            ),
            "better_for_capture_price": (
                label_b if (annual_b.get("capture_price_eur_per_mwh") or float("-inf"))
                > (annual_a.get("capture_price_eur_per_mwh") or float("-inf"))
                else label_a
            ),
            "better_for_negative_price_exposure": (
                label_b if (annual_b.get("energy_curtailed_negative_mwh") or float("inf"))
                < (annual_a.get("energy_curtailed_negative_mwh") or float("inf"))
                else label_a
            ),
            "better_for_high_price_alignment": (
                label_b if (annual_b.get("high_price_energy_share_pct") or float("-inf"))
                > (annual_a.get("high_price_energy_share_pct") or float("-inf"))
                else label_a
            ),
            "energy_gain_pct_b_vs_a": _safe_delta_pct(
                annual_a.get("energy_theoretical_mwh"),
                annual_b.get("energy_theoretical_mwh"),
            ),
            "market_value_gain_pct_b_vs_a": _safe_delta_pct(
                annual_a.get("market_value_eur"),
                annual_b.get("market_value_eur"),
            ),
        },
    }

    monthly_comparison = _compare_grouped_tables(
        analysis_result_a.monthly_summary,
        analysis_result_b.monthly_summary,
        key_col="month",
    ).sort_values("month").reset_index(drop=True)

    seasonal_comparison = _sort_season_df(
        _compare_grouped_tables(
            analysis_result_a.seasonal_summary,
            analysis_result_b.seasonal_summary,
            key_col="season",
        )
    )

    conclusions = _generate_conclusions(
        annual_a,
        annual_b,
        label_a=label_a,
        label_b=label_b,
    )

    meta = {
        "schema_version": SCHEMA_VERSION,
        "variant_label_a": label_a,
        "variant_label_b": label_b,
        "comparison_reference": "B minus A",
        "backend_energy_unit": "MWh",
        "backend_price_unit": "EUR/MWh",
        "backend_value_unit": "EUR",
        "bzn": bzn_a,
    }

    warnings = analysis_result_a.warnings + analysis_result_b.warnings + warnings

    return VariantComparisonResult(
        annual_comparison=annual_comparison,
        monthly_comparison=monthly_comparison,
        seasonal_comparison=seasonal_comparison,
        conclusions=conclusions,
        meta=meta,
        warnings=warnings,
    )