# core/production/hourly_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict
import pandas as pd


@dataclass
class AnalysisOptions:
    """
    threshold_value: threshold in the SAME UNIT as df_raw[threshold_column].
    threshold_column: column used by threshold & distribution studies (default: E_Grid).
    night_disconnection:
      - If True: negative values (import at night) are ignored for Threshold/Distribution
        by clamping the series to 0 (clip lower=0).
      - Night consumption is still computed from the raw series (negative values).
    """
    threshold_value: float
    threshold_column: str = "E_Grid"
    night_disconnection: bool = False


@dataclass
class AnalysisContext:
    input_file: Path
    general_info: Dict[str, str]
    units_map: Dict[str, str]
    df_raw: pd.DataFrame

    options: AnalysisOptions
    results: Dict[str, Any] = field(default_factory=dict)
