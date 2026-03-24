# core/market_analysis/market_analysis_runner.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.market_analysis.bess_screening import (
    BESSScreeningResult,
    run_bess_screening,
)
from core.market_analysis.market_price_analysis import (
    MarketPVAnalysisResult,
    read_market_prices_from_api,
    run_market_pv_analysis,
)
from core.market_analysis.standardization import (
    CanonicalMarketResult,
    CanonicalPVResult,
    standardize_pvsyst_hourly_from_bytes,
)
from core.market_analysis.variant_comparison import (
    VariantComparisonResult,
    compare_market_pv_variants,
)
from utils.readers.reader_market_prices_csv import read_market_prices_csv


@dataclass
class RunnerResult:
    mode: str
    market_result: CanonicalMarketResult
    pv_result_a: CanonicalPVResult
    pv_result_b: Optional[CanonicalPVResult]
    analysis_result_a: MarketPVAnalysisResult
    analysis_result_b: Optional[MarketPVAnalysisResult]
    comparison_result: Optional[VariantComparisonResult]
    bess_result_a: Optional[BESSScreeningResult]
    bess_result_b: Optional[BESSScreeningResult]
    meta: Dict[str, Any]
    warnings: List[str]


# =============================================================================
# Helpers
# =============================================================================

def _validate_runner_inputs(
    *,
    market_source_mode: str,
    market_bzn: Optional[str],
    market_start: Optional[str],
    market_end: Optional[str],
    market_csv_source: Optional[bytes],
    pv_source_a: Optional[bytes],
) -> None:
    if market_source_mode not in {"api", "csv"}:
        raise ValueError("market_source_mode must be 'api' or 'csv'.")

    if market_source_mode == "api":
        if not market_bzn:
            raise ValueError("market_bzn is required when market_source_mode='api'.")
        if not market_start:
            raise ValueError("market_start is required when market_source_mode='api'.")
        if not market_end:
            raise ValueError("market_end is required when market_source_mode='api'.")

    if market_source_mode == "csv" and market_csv_source is None:
        raise ValueError("market_csv_source is required when market_source_mode='csv'.")

    if pv_source_a is None:
        raise ValueError("pv_source_a is required.")


def _dedupe_keep_order(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for v in values:
        if not v:
            continue
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _build_global_meta(
    *,
    mode: str,
    market_source_mode: str,
    market_result: CanonicalMarketResult,
    analysis_result_a: MarketPVAnalysisResult,
    analysis_result_b: Optional[MarketPVAnalysisResult],
    variant_label_a: str,
    variant_label_b: Optional[str],
    has_variant_b: bool,
    bess_enabled: bool,
    bess_result_a: Optional[BESSScreeningResult],
    bess_result_b: Optional[BESSScreeningResult],
) -> Dict[str, Any]:
    meta = {
        "analysis_mode": mode,
        "market_source_mode": market_source_mode,
        "bzn": market_result.meta.get("bzn"),
        "time_start": market_result.meta.get("time_start") or analysis_result_a.meta.get("time_start"),
        "time_end": market_result.meta.get("time_end") or analysis_result_a.meta.get("time_end"),
        "variant_label_a": variant_label_a,
        "variant_label_b": variant_label_b if has_variant_b else None,
        "has_variant_b": has_variant_b,
        "bess_enabled": bess_enabled,
        "comparison_available": analysis_result_b is not None,
        "bess_available_a": bess_result_a is not None,
        "bess_available_b": bess_result_b is not None,
    }
    return meta


# =============================================================================
# Main runner
# =============================================================================

def run_market_analysis_from_sources(
    *,
    market_source_mode: str,
    market_bzn: str | None = None,
    market_start: str | None = None,
    market_end: str | None = None,
    market_csv_source: bytes | None = None,
    pv_source_a: bytes,
    pv_variant_label_a: str = "Variant A",
    pv_source_b: bytes | None = None,
    pv_variant_label_b: str = "Variant B",
    enable_bess: bool = False,
    bess_params: dict | None = None,
    local_tz: str = "Europe/Paris",
) -> RunnerResult:
    """
    Unified backend entry point for Streamlit.

    Scope:
    - market API or market CSV
    - single variant or two-variant comparison
    - optional indicative BESS screening
    """
    _validate_runner_inputs(
        market_source_mode=market_source_mode,
        market_bzn=market_bzn,
        market_start=market_start,
        market_end=market_end,
        market_csv_source=market_csv_source,
        pv_source_a=pv_source_a,
    )

    warnings: List[str] = []
    has_variant_b = pv_source_b is not None
    mode = "comparison" if has_variant_b else "single_variant"

    # -------------------------------------------------------------------------
    # Read market
    # -------------------------------------------------------------------------
    if market_source_mode == "api":
        market_result = read_market_prices_from_api(
            bzn=str(market_bzn),
            start=str(market_start),
            end=str(market_end),
            local_tz=local_tz,
        )
    else:
        market_result = read_market_prices_csv(market_csv_source)

    # -------------------------------------------------------------------------
    # Read PV A
    # -------------------------------------------------------------------------
    pv_result_a = standardize_pvsyst_hourly_from_bytes(
        pv_source_a,
        variant_label=pv_variant_label_a,
        source_name="bytes",
    )

    analysis_result_a = run_market_pv_analysis(
        market_result=market_result,
        pv_result=pv_result_a,
    )

    # -------------------------------------------------------------------------
    # Read PV B / comparison
    # -------------------------------------------------------------------------
    pv_result_b: Optional[CanonicalPVResult] = None
    analysis_result_b: Optional[MarketPVAnalysisResult] = None
    comparison_result: Optional[VariantComparisonResult] = None

    if has_variant_b:
        pv_result_b = standardize_pvsyst_hourly_from_bytes(
            pv_source_b,
            variant_label=pv_variant_label_b,
            source_name="bytes",
        )

        analysis_result_b = run_market_pv_analysis(
            market_result=market_result,
            pv_result=pv_result_b,
        )

        comparison_result = compare_market_pv_variants(
            analysis_result_a=analysis_result_a,
            analysis_result_b=analysis_result_b,
            variant_label_a=pv_variant_label_a,
            variant_label_b=pv_variant_label_b,
        )

    # -------------------------------------------------------------------------
    # BESS
    # -------------------------------------------------------------------------
    bess_result_a: Optional[BESSScreeningResult] = None
    bess_result_b: Optional[BESSScreeningResult] = None

    if enable_bess:
        bess_params = bess_params or {}

        bess_params_a = dict(bess_params)
        bess_params_a["variant_label"] = pv_variant_label_a
        bess_result_a = run_bess_screening(
            analysis_result=analysis_result_a,
            bess_params=bess_params_a,
        )

        if analysis_result_b is not None:
            bess_params_b = dict(bess_params)
            bess_params_b["variant_label"] = pv_variant_label_b
            bess_result_b = run_bess_screening(
                analysis_result=analysis_result_b,
                bess_params=bess_params_b,
            )

    # -------------------------------------------------------------------------
    # Consolidated meta / warnings
    # -------------------------------------------------------------------------
    meta = _build_global_meta(
        mode=mode,
        market_source_mode=market_source_mode,
        market_result=market_result,
        analysis_result_a=analysis_result_a,
        analysis_result_b=analysis_result_b,
        variant_label_a=pv_variant_label_a,
        variant_label_b=pv_variant_label_b if has_variant_b else None,
        has_variant_b=has_variant_b,
        bess_enabled=enable_bess,
        bess_result_a=bess_result_a,
        bess_result_b=bess_result_b,
    )

    warnings.extend(market_result.warnings)
    warnings.extend(pv_result_a.warnings)
    warnings.extend(analysis_result_a.warnings)

    if pv_result_b is not None:
        warnings.extend(pv_result_b.warnings)
    if analysis_result_b is not None:
        warnings.extend(analysis_result_b.warnings)
    if comparison_result is not None:
        warnings.extend(comparison_result.warnings)
    if bess_result_a is not None:
        warnings.extend(bess_result_a.warnings)
    if bess_result_b is not None:
        warnings.extend(bess_result_b.warnings)

    warnings = _dedupe_keep_order(warnings)

    return RunnerResult(
        mode=mode,
        market_result=market_result,
        pv_result_a=pv_result_a,
        pv_result_b=pv_result_b,
        analysis_result_a=analysis_result_a,
        analysis_result_b=analysis_result_b,
        comparison_result=comparison_result,
        bess_result_a=bess_result_a,
        bess_result_b=bess_result_b,
        meta=meta,
        warnings=warnings,
    )