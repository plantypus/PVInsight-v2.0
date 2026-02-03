# utils/__init__.py
"""
Utils = briques transverses (I/O, unités, séries temporelles, validation, readers).
"""
from __future__ import annotations

from .io import read_text_lines, split_pvsyst_hash_header, detect_separator, read_delimited_from_lines
from .units import normalize_unit, convert_irradiance_units, UnitConversionResult
from .time_series import parse_time_step_from_header, detect_time_step_from_datetime, resample_to_hourly, TimeStepInfo
from .validation import basic_quality_check, DataQuality
from .energy import annual_irradiation, EnergySummary
from .columns import check_required_columns, suggest_similar_columns
from .formatting import format_number, format_with_unit


__all__ = [
    # io
    "read_text_lines",
    "split_pvsyst_hash_header",
    "detect_separator",
    "read_delimited_from_lines",
    # units
    "normalize_unit",
    "convert_irradiance_units",
    "UnitConversionResult",
    # time_series
    "parse_time_step_from_header",
    "detect_time_step_from_datetime",
    "resample_to_hourly",
    "TimeStepInfo",
    # validation
    "basic_quality_check",
    "DataQuality",
    # energy
    "annual_irradiation",
    "EnergySummary",
    # columns
    "check_required_columns",
    "suggest_similar_columns",
    # formatting
    "format_number",
    "format_with_unit",
]
