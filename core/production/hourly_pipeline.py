# core/production/hourly_pipeline.py
from __future__ import annotations

from pathlib import Path

from utils.readers.hourly_results import read_hourly_from_bytes
from .hourly_models import AnalysisContext, AnalysisOptions
from .hourly_analyzer import register_analyses, run_all_analyses


def analyze_hourly_source(
    *,
    source: bytes,
    source_name: str,
    threshold_value: float,
    threshold_column: str = "E_Grid",
    night_disconnection: bool = False,
    grid_capacity_kw: float | None = None,
) -> AnalysisContext:
    """
    In-memory analysis:
    - parse bytes -> df + meta
    - run all analyses
    - return AnalysisContext with results filled

    grid_capacity_kw is optional and used by grid-related analyses if provided.
    """
    general_info, df, units_map = read_hourly_from_bytes(source)

    # Normalize capacity (robust)
    cap = None
    try:
        if grid_capacity_kw is not None:
            cap = float(grid_capacity_kw)
            if cap <= 0:
                cap = None
    except Exception:
        cap = None

    # Try passing grid_capacity_kw to AnalysisOptions if supported.
    try:
        options = AnalysisOptions(
            threshold_value=float(threshold_value),
            threshold_column=str(threshold_column),
            night_disconnection=bool(night_disconnection),
            grid_capacity_kw=cap,  # may raise TypeError if not in dataclass
        )
    except TypeError:
        options = AnalysisOptions(
            threshold_value=float(threshold_value),
            threshold_column=str(threshold_column),
            night_disconnection=bool(night_disconnection),
        )
        # Backward-compatible injection (won't crash analyses using getattr)
        try:
            setattr(options, "grid_capacity_kw", cap)
        except Exception:
            pass

    context = AnalysisContext(
        input_file=Path(source_name),
        general_info=general_info,
        units_map=units_map,
        df_raw=df,
        options=options,
    )

    register_analyses()
    run_all_analyses(context)
    return context
