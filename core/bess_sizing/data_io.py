from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from core.market_analysis.market_price_analysis import read_market_prices_from_api
from core.market_analysis.standardization import infer_time_step_minutes
from utils.readers.hourly_results import read_hourly_from_bytes
from utils.readers.tmy_pvsyst import read_tmy_pvsyst
from utils.readers.tmy_solargis import read_tmy_solargis


ANALYSIS_STEP_MINUTES = 60


@dataclass
class ParsedInputTable:
    dataframe: pd.DataFrame
    source_format: str
    units_map: Dict[str, str]
    timestamp_candidates: List[str]
    value_candidates: List[str]
    default_timestamp_col: Optional[str]
    default_value_col: Optional[str]
    warnings: List[str]
    meta: Dict[str, Any]


def _decode_bytes(source: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return source.decode(enc)
        except Exception:
            continue
    return source.decode("latin-1", errors="ignore")


def _read_generic_table_from_bytes(source: bytes) -> pd.DataFrame:
    text = _decode_bytes(source)
    csv_buffer = StringIO(text)

    try:
        df = pd.read_csv(csv_buffer, sep=None, engine="python", comment="#")
        if not df.empty:
            return df
    except Exception:
        pass

    csv_buffer = StringIO(text)
    try:
        df = pd.read_csv(csv_buffer, sep=";", comment="#")
        if not df.empty:
            return df
    except Exception:
        pass

    csv_buffer = StringIO(text)
    return pd.read_csv(csv_buffer, sep=",", comment="#")


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().replace("\ufeff", "") for c in out.columns]
    return out.loc[:, [c for c in out.columns if c != ""]]


def _norm_col(value: Any) -> str:
    txt = str(value or "").strip().lower()
    for token in (" ", "_", "-", "/", "\\", "(", ")", "[", "]", ".", ":"):
        txt = txt.replace(token, "")
    return txt


def _numeric_ratio(series: pd.Series, n: int = 500) -> float:
    sample = series.head(n)
    coerced = pd.to_numeric(
        sample.astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    return float(coerced.notna().mean()) if len(sample) > 0 else 0.0


def _datetime_ratio(series: pd.Series, n: int = 500) -> float:
    sample = series.head(n)
    parsed = pd.to_datetime(sample, errors="coerce", dayfirst=True)
    return float(parsed.notna().mean()) if len(sample) > 0 else 0.0


def _detect_timestamp_candidates(df: pd.DataFrame) -> List[str]:
    tokens = ("date", "time", "hour", "timestamp", "datetime")
    scored: List[tuple[str, float]] = []

    for col in df.columns:
        col_norm = _norm_col(col)
        token_bonus = 0.2 if any(tok in col_norm for tok in tokens) else 0.0
        ratio = _datetime_ratio(df[col])
        score = ratio + token_bonus
        if ratio >= 0.30 or score >= 0.40:
            scored.append((str(col), score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored]


def _column_token_score(col_name: str, kind: str) -> float:
    n = _norm_col(col_name)

    if kind == "pv":
        if n == "egrid":
            return 5.0
        if "egrid" in n:
            return 4.0
        if "energy" in n and "grid" in n:
            return 3.0
        if "pv" in n and ("energy" in n or "prod" in n):
            return 2.0
        if "power" in n and "pv" in n:
            return 1.5
    elif kind == "tmy":
        if n in {"ghi", "gti", "gpoa"}:
            return 5.0
        if "ghi" in n:
            return 4.0
        if "dni" in n or "dhi" in n:
            return 3.0
        if "temp" in n:
            return 2.0
    elif kind == "market":
        if n == "priceeurpermwh":
            return 5.0
        if "price" in n:
            return 4.0
        if "eurpermwh" in n:
            return 4.0
        if "dayahead" in n:
            return 2.0

    return 0.0


def _detect_value_candidates(df: pd.DataFrame, kind: str) -> List[str]:
    scored: List[tuple[str, float]] = []
    timestamp_like = set(_detect_timestamp_candidates(df))

    for col in df.columns:
        if col in timestamp_like:
            continue
        ratio = _numeric_ratio(df[col])
        if ratio < 0.50:
            continue
        score = _column_token_score(str(col), kind) + ratio
        scored.append((str(col), score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored]


def _default_value_col_from_candidates(kind: str, value_candidates: List[str]) -> Optional[str]:
    if not value_candidates:
        return None
    if kind == "pv":
        for col in value_candidates:
            n = _norm_col(col)
            if n == "egrid" or "egrid" in n:
                return col
    return value_candidates[0]


def _build_parsed_input(
    *,
    df: pd.DataFrame,
    source_format: str,
    units_map: Dict[str, str],
    kind: str,
    warnings: Optional[Sequence[str]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> ParsedInputTable:
    cleaned = _clean_columns(df)
    ts_candidates = _detect_timestamp_candidates(cleaned)
    val_candidates = _detect_value_candidates(cleaned, kind)

    return ParsedInputTable(
        dataframe=cleaned,
        source_format=source_format,
        units_map={str(k): str(v) for k, v in (units_map or {}).items()},
        timestamp_candidates=ts_candidates,
        value_candidates=val_candidates,
        default_timestamp_col=ts_candidates[0] if ts_candidates else None,
        default_value_col=_default_value_col_from_candidates(kind, val_candidates),
        warnings=list(warnings or []),
        meta=dict(meta or {}),
    )


def load_pv_input_table(source: bytes) -> ParsedInputTable:
    warnings: List[str] = []
    units_map: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    try:
        general_info, df_pvsyst, units_map = read_hourly_from_bytes(source)
        df = df_pvsyst.reset_index()
        if not df.empty:
            first_col = df.columns[0]
            df = df.rename(columns={first_col: "timestamp"})
        meta.update(general_info)
        return _build_parsed_input(
            df=df,
            source_format="pvsyst_hourly_results",
            units_map=units_map,
            kind="pv",
            warnings=warnings,
            meta=meta,
        )
    except Exception as exc:
        warnings.append(f"PV parser fallback to generic CSV reader: {exc}")

    df = _read_generic_table_from_bytes(source)
    return _build_parsed_input(
        df=df,
        source_format="generic_delimited",
        units_map=units_map,
        kind="pv",
        warnings=warnings,
        meta=meta,
    )


def load_tmy_input_table(source: bytes) -> ParsedInputTable:
    warnings: List[str] = []
    units_map: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    try:
        ds = read_tmy_pvsyst(
            source,
            source_name="uploaded_tmy.csv",
            target_irradiance_unit="W/m2",
            resample_hourly_if_subhourly=False,
        )
        df = ds.df.copy().rename(columns={"datetime": "timestamp"})
        units_map = ds.units_by_col
        warnings.extend(ds.warnings)
        meta = {
            "reader": "tmy_pvsyst",
            "time_step_minutes": ds.time_step_minutes,
        }
        return _build_parsed_input(
            df=df,
            source_format="tmy_pvsyst",
            units_map=units_map,
            kind="tmy",
            warnings=warnings,
            meta=meta,
        )
    except Exception:
        pass

    try:
        ds2 = read_tmy_solargis(
            source,
            source_name="uploaded_tmy.csv",
            target_irradiance_unit="W/m2",
            resample_hourly_if_subhourly=False,
        )
        df = ds2.df.copy().rename(columns={"datetime": "timestamp"})
        units_map = ds2.units_by_col
        warnings.extend(ds2.warnings)
        meta = {
            "reader": "tmy_solargis",
            "time_step_minutes": ds2.time_step_minutes,
        }
        return _build_parsed_input(
            df=df,
            source_format="tmy_solargis",
            units_map=units_map,
            kind="tmy",
            warnings=warnings,
            meta=meta,
        )
    except Exception as exc:
        warnings.append(f"TMY parser fallback to generic CSV reader: {exc}")

    df = _read_generic_table_from_bytes(source)
    return _build_parsed_input(
        df=df,
        source_format="generic_delimited",
        units_map=units_map,
        kind="tmy",
        warnings=warnings,
        meta=meta,
    )


def load_market_input_table(source: bytes) -> ParsedInputTable:
    df = _read_generic_table_from_bytes(source)
    return _build_parsed_input(
        df=df,
        source_format="generic_delimited",
        units_map={},
        kind="market",
        warnings=[],
        meta={},
    )


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def _check_timestamp_duplicates(
    df: pd.DataFrame,
    *,
    value_col: str,
    agg: str,
    warnings: List[str],
    label: str,
) -> pd.DataFrame:
    out = df.copy()
    n_dup = int(out["timestamp"].duplicated(keep=False).sum())
    if n_dup <= 0:
        return out

    warnings.append(
        f"{label}: {n_dup} duplicated timestamps detected. Aggregation='{agg}' applied."
    )

    grouped = out.groupby("timestamp", as_index=False)[value_col].agg(agg)
    return grouped


def _normalize_unit(value: Optional[str]) -> str:
    return str(value or "").strip().lower().replace(" ", "")


def detect_pv_unit_from_metadata(
    selected_value_col: str,
    units_map: Optional[Dict[str, str]] = None,
) -> str:
    units_map = units_map or {}
    raw = units_map.get(selected_value_col) or units_map.get(selected_value_col.strip())
    if raw:
        return str(raw)

    n = _norm_col(selected_value_col)
    if "mwh" in n:
        return "MWh"
    if "kwh" in n:
        return "kWh"
    if n.endswith("mw") or "power" in n:
        return "MW"
    if n.endswith("kw"):
        return "kW"
    return "kWh"


def detect_price_unit_from_metadata(selected_value_col: str) -> str:
    n = _norm_col(selected_value_col)
    if "eurpermwh" in n:
        return "EUR/MWh"
    if "eurperkwh" in n:
        return "EUR/kWh"
    if "ceurperkwh" in n or ("cent" in n and "kwh" in n):
        return "cEUR/kWh"
    return "EUR/MWh"


def _convert_pv_to_mwh_step(
    values: pd.Series,
    *,
    unit: str,
    step_minutes: float,
) -> pd.Series:
    unit_n = _normalize_unit(unit)
    step_h = float(step_minutes) / 60.0
    v = _to_numeric(values)

    if unit_n == "wh":
        return v * 1e-6
    if unit_n == "kwh":
        return v * 1e-3
    if unit_n == "mwh":
        return v

    if unit_n == "w":
        return v * step_h * 1e-6
    if unit_n == "kw":
        return v * step_h * 1e-3
    if unit_n == "mw":
        return v * step_h

    raise ValueError(
        f"Unsupported PV unit '{unit}'. Use one of: Wh, kWh, MWh, W, kW, MW."
    )


def _convert_price_to_eur_per_mwh(values: pd.Series, *, unit: str) -> pd.Series:
    unit_n = _normalize_unit(unit)
    v = _to_numeric(values)

    if unit_n in {"eur/mwh", "eurpermwh"}:
        return v
    if unit_n in {"eur/kwh", "eurperkwh"}:
        return v * 1000.0
    if unit_n in {"ceur/kwh", "ceurperkwh", "centeurperkwh"}:
        return v * 10.0

    raise ValueError(
        f"Unsupported price unit '{unit}'. Use one of: EUR/MWh, EUR/kWh, cEUR/kWh."
    )


def _infer_step_minutes_or_raise(
    timestamp_series: pd.Series,
    *,
    label: str,
    warnings: List[str],
) -> float:
    info = infer_time_step_minutes(timestamp_series)
    step = info.get("time_step_minutes")
    if step is None:
        raise ValueError(f"{label}: cannot infer input time step.")

    if not info.get("is_regular", False):
        warnings.append(
            f"{label}: irregular time-step detected {info.get('detected_steps_minutes')}; "
            f"dominant step {step} min is used."
        )

    return float(step)


def _reindex_hourly(
    df: pd.DataFrame,
    *,
    timestamp_col: str,
    value_col: str,
    fill_mode: str,
    warnings: List[str],
    label: str,
) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.set_index(timestamp_col).sort_index()
    hourly_index = pd.date_range(
        start=out.index.min(),
        end=out.index.max(),
        freq="1h",
    )
    out = out.reindex(hourly_index)
    missing = int(out[value_col].isna().sum())

    if missing > 0:
        warnings.append(f"{label}: {missing} missing hourly rows after reindex.")
        if fill_mode == "zero":
            out[value_col] = out[value_col].fillna(0.0)
        elif fill_mode == "interpolate":
            out[value_col] = (
                out[value_col]
                .interpolate(method="time", limit=6, limit_direction="both")
                .ffill()
                .bfill()
            )
            still_missing = int(out[value_col].isna().sum())
            if still_missing > 0:
                raise ValueError(
                    f"{label}: {still_missing} missing hourly values remain after interpolation."
                )
        else:
            raise ValueError(f"Unknown fill_mode '{fill_mode}'.")

    out = out.reset_index().rename(columns={"index": timestamp_col})
    return out


def prepare_pv_hourly_series(
    *,
    dataframe: pd.DataFrame,
    timestamp_col: str,
    value_col: str,
    value_unit: str,
) -> tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    warnings: List[str] = []

    if timestamp_col not in dataframe.columns:
        raise ValueError(f"PV: timestamp column '{timestamp_col}' not found.")
    if value_col not in dataframe.columns:
        raise ValueError(f"PV: value column '{value_col}' not found.")

    work = dataframe[[timestamp_col, value_col]].copy()
    work = work.rename(columns={timestamp_col: "timestamp", value_col: "pv_raw"})
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce", dayfirst=True)
    work["pv_raw"] = _to_numeric(work["pv_raw"])

    n_before = len(work)
    work = work.dropna(subset=["timestamp", "pv_raw"]).copy()
    dropped = n_before - len(work)
    if dropped > 0:
        warnings.append(f"PV: {dropped} row(s) dropped due to invalid timestamp/value.")

    if work.empty:
        raise ValueError("PV: no valid rows available after parsing.")

    step_minutes = _infer_step_minutes_or_raise(
        work["timestamp"],
        label="PV",
        warnings=warnings,
    )

    if step_minutes > ANALYSIS_STEP_MINUTES:
        raise ValueError(
            f"PV: unsupported time step {step_minutes} min. "
            "Only hourly or sub-hourly data are supported."
        )

    work["pv_mwh_step"] = _convert_pv_to_mwh_step(
        work["pv_raw"],
        unit=value_unit,
        step_minutes=step_minutes,
    )

    n_negative = int((work["pv_mwh_step"] < 0.0).sum())
    if n_negative > 0:
        warnings.append(
            f"PV: {n_negative} negative energy rows detected and clipped to 0."
        )
        work["pv_mwh_step"] = work["pv_mwh_step"].clip(lower=0.0)

    if step_minutes < ANALYSIS_STEP_MINUTES:
        work["timestamp"] = work["timestamp"].dt.floor("1h")
        work = work.groupby("timestamp", as_index=False)["pv_mwh_step"].sum()
        resampling_method = "sum_to_hourly"
    else:
        work["timestamp"] = work["timestamp"].dt.floor("1h")
        work = _check_timestamp_duplicates(
            work[["timestamp", "pv_mwh_step"]],
            value_col="pv_mwh_step",
            agg="sum",
            warnings=warnings,
            label="PV",
        )
        resampling_method = "native_hourly"

    work = _reindex_hourly(
        work,
        timestamp_col="timestamp",
        value_col="pv_mwh_step",
        fill_mode="zero",
        warnings=warnings,
        label="PV",
    )

    out = work.rename(columns={"pv_mwh_step": "pv_mwh"})
    out = out.sort_values("timestamp").reset_index(drop=True)
    out["month"] = out["timestamp"].dt.month.astype("int64")
    out["day"] = out["timestamp"].dt.day.astype("int64")
    out["hour"] = out["timestamp"].dt.hour.astype("int64")

    meta = {
        "n_rows_hourly": int(len(out)),
        "time_step_minutes_original": step_minutes,
        "time_step_minutes_analysis": ANALYSIS_STEP_MINUTES,
        "resampling_method": resampling_method,
        "value_unit_input": value_unit,
        "value_unit_analysis": "MWh",
        "energy_total_mwh": float(out["pv_mwh"].sum()),
        "time_start": out["timestamp"].min().isoformat(),
        "time_end": out["timestamp"].max().isoformat(),
    }
    return out, meta, warnings


def prepare_market_hourly_series(
    *,
    dataframe: pd.DataFrame,
    timestamp_col: str,
    value_col: str,
    value_unit: str,
) -> tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    warnings: List[str] = []

    if timestamp_col not in dataframe.columns:
        raise ValueError(f"Market: timestamp column '{timestamp_col}' not found.")
    if value_col not in dataframe.columns:
        raise ValueError(f"Market: value column '{value_col}' not found.")

    work = dataframe[[timestamp_col, value_col]].copy()
    work = work.rename(columns={timestamp_col: "timestamp", value_col: "price_raw"})
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce", dayfirst=True)
    work["price_raw"] = _to_numeric(work["price_raw"])

    n_before = len(work)
    work = work.dropna(subset=["timestamp", "price_raw"]).copy()
    dropped = n_before - len(work)
    if dropped > 0:
        warnings.append(f"Market: {dropped} row(s) dropped due to invalid timestamp/value.")

    if work.empty:
        raise ValueError("Market: no valid rows available after parsing.")

    step_minutes = _infer_step_minutes_or_raise(
        work["timestamp"],
        label="Market",
        warnings=warnings,
    )
    if step_minutes > ANALYSIS_STEP_MINUTES:
        raise ValueError(
            f"Market: unsupported time step {step_minutes} min. "
            "Only hourly or sub-hourly data are supported."
        )

    work["price_eur_per_mwh"] = _convert_price_to_eur_per_mwh(
        work["price_raw"],
        unit=value_unit,
    )

    if step_minutes < ANALYSIS_STEP_MINUTES:
        work["timestamp"] = work["timestamp"].dt.floor("1h")
        work = work.groupby("timestamp", as_index=False)["price_eur_per_mwh"].mean()
        resampling_method = "mean_to_hourly"
    else:
        work["timestamp"] = work["timestamp"].dt.floor("1h")
        work = _check_timestamp_duplicates(
            work[["timestamp", "price_eur_per_mwh"]],
            value_col="price_eur_per_mwh",
            agg="mean",
            warnings=warnings,
            label="Market",
        )
        resampling_method = "native_hourly"

    work = _reindex_hourly(
        work,
        timestamp_col="timestamp",
        value_col="price_eur_per_mwh",
        fill_mode="interpolate",
        warnings=warnings,
        label="Market",
    )

    out = work.sort_values("timestamp").reset_index(drop=True)
    out["month"] = out["timestamp"].dt.month.astype("int64")
    out["day"] = out["timestamp"].dt.day.astype("int64")
    out["hour"] = out["timestamp"].dt.hour.astype("int64")

    meta = {
        "n_rows_hourly": int(len(out)),
        "time_step_minutes_original": step_minutes,
        "time_step_minutes_analysis": ANALYSIS_STEP_MINUTES,
        "resampling_method": resampling_method,
        "value_unit_input": value_unit,
        "value_unit_analysis": "EUR/MWh",
        "price_mean_eur_per_mwh": float(out["price_eur_per_mwh"].mean()),
        "time_start": out["timestamp"].min().isoformat(),
        "time_end": out["timestamp"].max().isoformat(),
    }
    return out, meta, warnings


def fetch_market_prices_hourly_from_api(
    *,
    bzn: str,
    year: int,
    local_tz: str = "Europe/Paris",
) -> tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    start = f"{int(year)}-01-01"
    end = f"{int(year)}-12-31"

    result = read_market_prices_from_api(
        bzn=bzn,
        start=start,
        end=end,
        local_tz=local_tz,
    )

    df = result.data_analysis.copy()
    if df.empty:
        raise ValueError("Market API returned an empty hourly dataset.")

    out = df[["timestamp", "price_eur_per_mwh"]].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out = out.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    out["month"] = out["timestamp"].dt.month.astype("int64")
    out["day"] = out["timestamp"].dt.day.astype("int64")
    out["hour"] = out["timestamp"].dt.hour.astype("int64")

    meta = {
        "source": "api_energy_charts",
        "bzn": bzn,
        "year": int(year),
        "n_rows_hourly": int(len(out)),
        "time_step_minutes_analysis": ANALYSIS_STEP_MINUTES,
        "time_start": out["timestamp"].min().isoformat(),
        "time_end": out["timestamp"].max().isoformat(),
    }

    return out, meta, list(result.warnings)


def align_market_prices_to_pv_profile(
    *,
    pv_hourly: pd.DataFrame,
    market_hourly: pd.DataFrame,
) -> tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    warnings: List[str] = []

    if pv_hourly.empty:
        raise ValueError("PV hourly dataset is empty.")
    if market_hourly.empty:
        raise ValueError("Market hourly dataset is empty.")

    pv = pv_hourly.copy()
    mk = market_hourly.copy()

    for col in ("month", "day", "hour"):
        if col not in pv.columns:
            if col == "month":
                pv[col] = pv["timestamp"].dt.month
            elif col == "day":
                pv[col] = pv["timestamp"].dt.day
            else:
                pv[col] = pv["timestamp"].dt.hour
        if col not in mk.columns:
            if col == "month":
                mk[col] = mk["timestamp"].dt.month
            elif col == "day":
                mk[col] = mk["timestamp"].dt.day
            else:
                mk[col] = mk["timestamp"].dt.hour

    market_key = (
        mk.groupby(["month", "day", "hour"], as_index=False)["price_eur_per_mwh"]
        .mean()
    )

    aligned = pv.merge(
        market_key,
        on=["month", "day", "hour"],
        how="left",
        validate="many_to_one",
    )

    missing_initial = int(aligned["price_eur_per_mwh"].isna().sum())
    if missing_initial > 0:
        warnings.append(
            f"Price alignment month-day-hour: {missing_initial} PV row(s) unmatched; fallback month-hour profile used."
        )

        month_hour = mk.groupby(["month", "hour"])["price_eur_per_mwh"].mean().to_dict()
        aligned["price_eur_per_mwh"] = aligned.apply(
            lambda r: (
                month_hour.get((int(r["month"]), int(r["hour"])))
                if pd.isna(r["price_eur_per_mwh"])
                else r["price_eur_per_mwh"]
            ),
            axis=1,
        )

    missing_after_fallback = int(aligned["price_eur_per_mwh"].isna().sum())
    if missing_after_fallback > 0:
        global_mean = float(mk["price_eur_per_mwh"].mean())
        warnings.append(
            f"{missing_after_fallback} row(s) still unmatched after fallback; global mean price applied."
        )
        aligned["price_eur_per_mwh"] = aligned["price_eur_per_mwh"].fillna(global_mean)

    aligned = aligned.sort_values("timestamp").reset_index(drop=True)
    aligned = aligned[["timestamp", "pv_mwh", "price_eur_per_mwh", "month", "day", "hour"]]

    meta = {
        "alignment_mode": "month_day_hour",
        "n_rows": int(len(aligned)),
        "missing_price_before_fallback": missing_initial,
        "missing_price_after_fallback": missing_after_fallback,
    }
    return aligned, meta, warnings


def prepare_tmy_hourly_series(
    *,
    dataframe: pd.DataFrame,
    timestamp_col: str,
    value_col: str,
) -> tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    warnings: List[str] = []

    if timestamp_col not in dataframe.columns:
        raise ValueError(f"TMY: timestamp column '{timestamp_col}' not found.")
    if value_col not in dataframe.columns:
        raise ValueError(f"TMY: value column '{value_col}' not found.")

    work = dataframe[[timestamp_col, value_col]].copy()
    work = work.rename(columns={timestamp_col: "timestamp", value_col: "tmy_signal"})
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce", dayfirst=True)
    work["tmy_signal"] = _to_numeric(work["tmy_signal"])

    n_before = len(work)
    work = work.dropna(subset=["timestamp", "tmy_signal"]).copy()
    dropped = n_before - len(work)
    if dropped > 0:
        warnings.append(f"TMY: {dropped} row(s) dropped due to invalid timestamp/value.")

    if work.empty:
        raise ValueError("TMY: no valid rows available after parsing.")

    step_minutes = _infer_step_minutes_or_raise(
        work["timestamp"],
        label="TMY",
        warnings=warnings,
    )
    if step_minutes > ANALYSIS_STEP_MINUTES:
        raise ValueError(
            f"TMY: unsupported time step {step_minutes} min. "
            "Only hourly or sub-hourly data are supported."
        )

    if step_minutes < ANALYSIS_STEP_MINUTES:
        work["timestamp"] = work["timestamp"].dt.floor("1h")
        work = work.groupby("timestamp", as_index=False)["tmy_signal"].mean()
        resampling_method = "mean_to_hourly"
    else:
        work["timestamp"] = work["timestamp"].dt.floor("1h")
        work = _check_timestamp_duplicates(
            work[["timestamp", "tmy_signal"]],
            value_col="tmy_signal",
            agg="mean",
            warnings=warnings,
            label="TMY",
        )
        resampling_method = "native_hourly"

    out = work.sort_values("timestamp").reset_index(drop=True)
    out["month"] = out["timestamp"].dt.month.astype("int64")
    out["day"] = out["timestamp"].dt.day.astype("int64")
    out["hour"] = out["timestamp"].dt.hour.astype("int64")

    meta = {
        "n_rows_hourly": int(len(out)),
        "time_step_minutes_original": step_minutes,
        "time_step_minutes_analysis": ANALYSIS_STEP_MINUTES,
        "resampling_method": resampling_method,
        "time_start": out["timestamp"].min().isoformat(),
        "time_end": out["timestamp"].max().isoformat(),
    }
    return out, meta, warnings


def compute_tmy_coherence(
    *,
    pv_hourly: pd.DataFrame,
    tmy_hourly: Optional[pd.DataFrame],
) -> Dict[str, Any]:
    if tmy_hourly is None or tmy_hourly.empty:
        return {
            "available": False,
            "message": "No TMY dataset provided.",
        }

    pv = pv_hourly.copy()
    tmy = tmy_hourly.copy()

    tmy_key = tmy.groupby(["month", "day", "hour"], as_index=False)["tmy_signal"].mean()
    merged = pv.merge(
        tmy_key,
        on=["month", "day", "hour"],
        how="left",
        validate="many_to_one",
    )

    matched = int(merged["tmy_signal"].notna().sum())
    total = int(len(merged))
    coverage_pct = 100.0 * matched / total if total > 0 else 0.0

    correlation = None
    valid = merged.dropna(subset=["pv_mwh", "tmy_signal"])
    if len(valid) > 10:
        corr = valid["pv_mwh"].corr(valid["tmy_signal"])
        if not pd.isna(corr):
            correlation = float(corr)

    return {
        "available": True,
        "matched_hours": matched,
        "total_hours": total,
        "coverage_pct": coverage_pct,
        "pv_tmy_signal_correlation": correlation,
    }
