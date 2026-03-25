# app/pages/50_market_analysis.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.bootstrap import bootstrap
from app.ui.i18n import t
from core.market_analysis.market_analysis_runner import run_market_analysis_from_sources


# =============================================================================
# Bootstrap
# =============================================================================

bootstrap(render_sidebar_ui=True)

PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "chart_export",
        "height": 700,
        "width": 1200,
        "scale": 2,
    },
}

BZN_OPTIONS = {
    "France": "FR",
    "Germany / Luxembourg": "DE-LU",
    "Belgium": "BE",
    "Netherlands": "NL",
    "Spain": "ES",
    "Italy North": "IT-North",
    "Poland": "PL",
    "Switzerland": "CH",
    "Denmark 1": "DK1",
    "Denmark 2": "DK2",
}


# =============================================================================
# Helpers
# =============================================================================

def _label_map_market_analysis() -> Dict[str, str]:
    return {
        "month": t("MARKET_ANALYSIS_COL_MONTH"),
        "season": t("MARKET_ANALYSIS_COL_SEASON"),
        "price_mean_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_MEAN"),
        "price_median_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_MEDIAN"),
        "price_min_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_MIN"),
        "price_max_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_MAX"),
        "negative_hours": t("MARKET_ANALYSIS_COL_NEGATIVE_HOURS"),
        "negative_days": t("MARKET_ANALYSIS_COL_NEGATIVE_DAYS"),
        "negative_hour_share_pct": t("MARKET_ANALYSIS_COL_NEGATIVE_HOUR_SHARE"),
        "n_hours": t("MARKET_ANALYSIS_COL_N_HOURS"),
        "energy_theoretical_mwh": t("MARKET_ANALYSIS_COL_ENERGY_THEORETICAL"),
        "energy_injected_mwh": t("MARKET_ANALYSIS_COL_ENERGY_INJECTED"),
        "energy_curtailed_negative_mwh": t("MARKET_ANALYSIS_COL_ENERGY_CURTAILED"),
        "market_value_eur": t("MARKET_ANALYSIS_COL_MARKET_VALUE"),
        "market_value_raw_eur": t("MARKET_ANALYSIS_COL_MARKET_VALUE_RAW"),
        "negative_hours_market": t("MARKET_ANALYSIS_COL_NEGATIVE_HOURS_MARKET"),
        "negative_hours_with_generation": t("MARKET_ANALYSIS_COL_NEGATIVE_HOURS_WITH_GEN"),
        "days_in_month": t("MARKET_ANALYSIS_COL_DAYS_IN_PERIOD"),
        "negative_days_market": t("MARKET_ANALYSIS_COL_NEGATIVE_DAYS_MARKET"),
        "negative_days_with_generation": t("MARKET_ANALYSIS_COL_NEGATIVE_DAYS_WITH_GEN"),
        "energy_on_high_price_hours_mwh": t("MARKET_ANALYSIS_COL_ENERGY_HIGH_PRICE"),
        "capture_price_eur_per_mwh": t("MARKET_ANALYSIS_COL_CAPTURE_PRICE"),
        "capture_rate": t("MARKET_ANALYSIS_COL_CAPTURE_RATE"),
        "curtailed_share_pct": t("MARKET_ANALYSIS_COL_CURTAILED_SHARE"),
        "high_price_energy_share_pct": t("MARKET_ANALYSIS_COL_HIGH_PRICE_SHARE"),
        "avg_curtailed_per_day_mwh": t("MARKET_ANALYSIS_COL_AVG_CURTAILED_PER_DAY"),
        "avg_curtailed_per_impacted_day_mwh": t("MARKET_ANALYSIS_COL_AVG_CURTAILED_PER_IMPACTED_DAY"),
        "hour": t("MARKET_ANALYSIS_COL_HOUR"),
        "price_std_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_STD"),
        "price_p10_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_P10"),
        "price_p25_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_P25"),
        "price_p75_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_P75"),
        "price_p90_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE_P90"),
        "price_cv_pct": t("MARKET_ANALYSIS_COL_PRICE_CV"),
        "e_grid_mean_mwh": t("MARKET_ANALYSIS_COL_PV_MEAN"),
        "e_grid_median_mwh": t("MARKET_ANALYSIS_COL_PV_MEDIAN"),
        "e_grid_p25_mwh": t("MARKET_ANALYSIS_COL_PV_P25"),
        "e_grid_p75_mwh": t("MARKET_ANALYSIS_COL_PV_P75"),
        "e_grid_injected_mean_mwh": t("MARKET_ANALYSIS_COL_PV_INJECTED_MEAN"),
        "e_grid_injected_median_mwh": t("MARKET_ANALYSIS_COL_PV_INJECTED_MEDIAN"),
        "curtailed_negative_mean_mwh": t("MARKET_ANALYSIS_COL_PV_CURTAILED_MEAN"),
        "timestamp": t("MARKET_ANALYSIS_COL_TIMESTAMP"),
        "date": t("MARKET_ANALYSIS_COL_DATE"),
        "year": t("MARKET_ANALYSIS_COL_YEAR"),
        "day": t("MARKET_ANALYSIS_COL_DAY"),
        "bzn": t("MARKET_ANALYSIS_COL_BZN"),
        "price_eur_per_mwh": t("MARKET_ANALYSIS_COL_PRICE"),
        "is_negative_price": t("MARKET_ANALYSIS_COL_IS_NEGATIVE"),
        "e_grid_mwh": t("MARKET_ANALYSIS_COL_EGRID"),
        "e_grid_injected_mwh": t("MARKET_ANALYSIS_COL_EGRID_INJECTED"),
        "e_grid_curtailed_negative_mwh": t("MARKET_ANALYSIS_COL_EGRID_CURTAILED"),
        "is_positive_generation": t("MARKET_ANALYSIS_COL_IS_POSITIVE_GEN"),
        "has_negative_price_and_generation": t("MARKET_ANALYSIS_COL_HAS_NEG_AND_GEN"),
        "is_high_price_hour": t("MARKET_ANALYSIS_COL_IS_HIGH_PRICE"),
        "market_value_eur_raw": t("MARKET_ANALYSIS_COL_MARKET_VALUE_RAW"),
        "variant_label": t("MARKET_ANALYSIS_COL_VARIANT"),
        "source": t("MARKET_ANALYSIS_COL_SOURCE"),
        "source_mode": t("MARKET_ANALYSIS_COL_SOURCE_MODE"),
        "metric": t("MARKET_ANALYSIS_COL_METRIC"),
        "value": t("MARKET_ANALYSIS_COL_VALUE"),
        "energy_available_for_storage_mwh": t("MARKET_ANALYSIS_COL_BESS_ENERGY_AVAILABLE"),
        "energy_charged_from_source_mwh": t("MARKET_ANALYSIS_COL_BESS_CHARGED_SOURCE"),
        "energy_discharged_to_grid_mwh": t("MARKET_ANALYSIS_COL_BESS_DISCHARGED"),
        "total_losses_mwh": t("MARKET_ANALYSIS_COL_BESS_LOSSES"),
        "bess_added_value_eur": t("MARKET_ANALYSIS_COL_BESS_ADDED_VALUE"),
        "max_soc_mwh": t("MARKET_ANALYSIS_COL_BESS_MAX_SOC"),
        "charge_hours": t("MARKET_ANALYSIS_COL_BESS_CHARGE_HOURS"),
        "discharge_hours": t("MARKET_ANALYSIS_COL_BESS_DISCHARGE_HOURS"),
        "storage_recovery_ratio": t("MARKET_ANALYSIS_COL_BESS_RECOVERY_RATIO"),
        "bess_soc_before_mwh": t("MARKET_ANALYSIS_COL_BESS_SOC_BEFORE"),
        "bess_soc_after_mwh": t("MARKET_ANALYSIS_COL_BESS_SOC_AFTER"),
        "bess_charge_from_source_mwh": t("MARKET_ANALYSIS_COL_BESS_CHARGE_SOURCE"),
        "bess_charge_into_battery_mwh": t("MARKET_ANALYSIS_COL_BESS_CHARGE_BATTERY"),
        "bess_discharge_from_battery_mwh": t("MARKET_ANALYSIS_COL_BESS_DISCHARGE_BATTERY"),
        "bess_discharge_to_grid_mwh": t("MARKET_ANALYSIS_COL_BESS_DISCHARGE_GRID"),
        "bess_charge_losses_mwh": t("MARKET_ANALYSIS_COL_BESS_CHARGE_LOSSES"),
        "bess_discharge_losses_mwh": t("MARKET_ANALYSIS_COL_BESS_DISCHARGE_LOSSES"),
        "bess_total_losses_mwh": t("MARKET_ANALYSIS_COL_BESS_TOTAL_LOSSES"),
        "bess_market_value_eur": t("MARKET_ANALYSIS_COL_BESS_MARKET_VALUE"),
        "bess_is_charging": t("MARKET_ANALYSIS_COL_BESS_IS_CHARGING"),
        "bess_is_discharging": t("MARKET_ANALYSIS_COL_BESS_IS_DISCHARGING"),
        "market_value_with_bess_eur": t("MARKET_ANALYSIS_COL_MARKET_VALUE_WITH_BESS"),
    }


def _format_season_value(value: Any) -> Any:
    if value == "winter":
        return t("MARKET_ANALYSIS_SEASON_WINTER")
    if value == "spring":
        return t("MARKET_ANALYSIS_SEASON_SPRING")
    if value == "summer":
        return t("MARKET_ANALYSIS_SEASON_SUMMER")
    if value == "autumn":
        return t("MARKET_ANALYSIS_SEASON_AUTUMN")
    return value


def _present_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    out = df.copy()

    if "season" in out.columns:
        out["season"] = out["season"].map(_format_season_value)

    label_map = _label_map_market_analysis()
    out = out.rename(columns={c: label_map.get(c, c) for c in out.columns})
    return out


def _styled_df(df: pd.DataFrame):
    presented = _present_df(df)

    if presented is None or presented.empty:
        return presented

    percent_keywords = ["%", "share", "ratio", "captation", "capture", "recovery"]
    eurmwh_keywords = ["EUR/MWh"]
    eur_keywords = ["EUR"]
    mwh_keywords = ["MWh"]
    mw_keywords = ["MW"]

    format_map: Dict[str, Any] = {}

    for col in presented.columns:
        col_l = str(col).lower()

        if "timestamp" in col_l or "date" in col_l:
            continue

        if any(k.lower() in col_l for k in eurmwh_keywords):
            format_map[col] = lambda x: _fmt_float(x, 1)
        elif any(k.lower() in col_l for k in percent_keywords):
            format_map[col] = lambda x: _fmt_float(x, 2)
        elif any(k.lower() in col_l for k in eur_keywords):
            format_map[col] = lambda x: _fmt_float(x, 0)
        elif any(k.lower() in col_l for k in mwh_keywords):
            format_map[col] = lambda x: _fmt_float(x, 1)
        elif any(k.lower() in col_l for k in mw_keywords):
            format_map[col] = lambda x: _fmt_float(x, 1)
        elif "hour" in col_l or "month" in col_l or "year" in col_l or "day" in col_l:
            format_map[col] = lambda x: _fmt_int(x)
        elif "value" in col_l:
            format_map[col] = lambda x: _fmt_float(x, 2)

    try:
        return presented.style.format(format_map)
    except Exception:
        return presented

def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")


def _series_dict_to_df(d: Dict[str, Any], key_name: str = "metric", value_name: str = "value") -> pd.DataFrame:
    return pd.DataFrame([{key_name: k, value_name: v} for k, v in d.items()])


def _clean_bess_params(
    *,
    capacity_mwh: Optional[float],
    charge_power_mw: Optional[float],
    discharge_power_mw: Optional[float],
    roundtrip_efficiency: Optional[float],
    charge_price_threshold_eur_per_mwh: Optional[float],
    discharge_price_threshold_eur_per_mwh: Optional[float],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if capacity_mwh is not None:
        params["capacity_mwh"] = capacity_mwh
    if charge_power_mw is not None:
        params["charge_power_mw"] = charge_power_mw
    if discharge_power_mw is not None:
        params["discharge_power_mw"] = discharge_power_mw
    if roundtrip_efficiency is not None:
        params["roundtrip_efficiency"] = roundtrip_efficiency
    if charge_price_threshold_eur_per_mwh is not None:
        params["charge_price_threshold_eur_per_mwh"] = charge_price_threshold_eur_per_mwh
    if discharge_price_threshold_eur_per_mwh is not None:
        params["discharge_price_threshold_eur_per_mwh"] = discharge_price_threshold_eur_per_mwh
    return params


def _fmt_step(meta: Dict[str, Any], key: str) -> str:
    val = meta.get(key)

    if val is None:
        return t("MARKET_ANALYSIS_NA")

    if isinstance(val, str) and val.strip() == "":
        return t("MARKET_ANALYSIS_NA")

    if pd.isna(val):
        return t("MARKET_ANALYSIS_NA")

    try:
        f = float(val)
        if f.is_integer():
            return f"{int(f)} min"
        return f"{f:.2f} min"
    except Exception:
        return str(val)


def _fmt_int(value: Any) -> str:
    if value is None or pd.isna(value):
        return t("MARKET_ANALYSIS_NA")
    try:
        return f"{int(round(float(value))):,}".replace(",", " ")
    except Exception:
        return str(value)


def _fmt_float(value: Any, decimals: int = 1, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return t("MARKET_ANALYSIS_NA")
    try:
        txt = f"{float(value):,.{decimals}f}".replace(",", " ").replace(".", ",")
        return f"{txt}{suffix}"
    except Exception:
        return str(value)


def _help_popover(title_key: str, body_key: str) -> None:
    with st.popover("❓"):
        st.markdown(f"**{t(title_key)}**")
        st.markdown(t(body_key))


def _single_variant_conclusions(result) -> list[str]:
    ann = result.analysis_result_a.annual_indicators
    out: list[str] = []

    curtailed_share = ann.get("curtailed_share_pct")
    curtailed_energy = ann.get("energy_curtailed_negative_mwh")
    if curtailed_share is not None:
        if curtailed_share < 1:
            out.append(
                t("MARKET_ANALYSIS_CONCLUSION_LOW_NEGATIVE").format(
                    value=float(curtailed_share)
                )
            )
        elif curtailed_share < 5:
            out.append(
                t("MARKET_ANALYSIS_CONCLUSION_MEDIUM_NEGATIVE").format(
                    value=float(curtailed_share)
                )
            )
        else:
            out.append(
                t("MARKET_ANALYSIS_CONCLUSION_HIGH_NEGATIVE").format(
                    value=float(curtailed_share)
                )
            )

    high_price_share = ann.get("high_price_energy_share_pct")
    if high_price_share is not None:
        if high_price_share >= 35:
            out.append(
                t("MARKET_ANALYSIS_CONCLUSION_HIGH_PRICE_SHARE_HIGH").format(
                    value=float(high_price_share)
                )
            )
        else:
            out.append(
                t("MARKET_ANALYSIS_CONCLUSION_HIGH_PRICE_SHARE_LOW").format(
                    value=float(high_price_share)
                )
            )

    capture_rate = ann.get("capture_rate")
    if capture_rate is not None:
        if capture_rate >= 1.0:
            out.append(
                t("MARKET_ANALYSIS_CONCLUSION_CAPTURE_RATE_GOOD").format(
                    value=float(capture_rate)
                )
            )
        else:
            out.append(
                t("MARKET_ANALYSIS_CONCLUSION_CAPTURE_RATE_LOW").format(
                    value=float(capture_rate)
                )
            )

    if result.market_result.meta.get("resampled_to_analysis_step"):
        out.append(t("MARKET_ANALYSIS_CONCLUSION_MARKET_RESAMPLED"))

    if result.pv_result_a.meta.get("resampled_to_analysis_step"):
        out.append(t("MARKET_ANALYSIS_CONCLUSION_PV_RESAMPLED"))

    return out


# =============================================================================
# Plot functions
# Graph titles remain in English by design
# =============================================================================

def plot_market_heatmap(market_df_analysis: pd.DataFrame) -> go.Figure:
    tmp = market_df_analysis.groupby(["month", "hour"], dropna=False)["price_eur_per_mwh"].mean().reset_index()
    pivot = tmp.pivot(index="month", columns="hour", values="price_eur_per_mwh").sort_index()

    fig = px.imshow(
        pivot,
        aspect="auto",
        labels={"x": "Hour", "y": "Month", "color": "EUR/MWh"},
        title="Market price heatmap (month × hour)",
        text_auto=".1f",
    )
    fig.update_layout(height=500)
    return fig


def plot_typical_price_profile(price_profile: pd.DataFrame) -> go.Figure:
    required = {
        "hour",
        "price_mean_eur_per_mwh",
        "price_p25_eur_per_mwh",
        "price_p75_eur_per_mwh",
    }
    missing = required - set(price_profile.columns)
    if missing:
        raise ValueError(f"Missing required columns for typical price profile: {sorted(missing)}")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=price_profile["hour"],
        y=price_profile["price_p75_eur_per_mwh"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=price_profile["hour"],
        y=price_profile["price_p25_eur_per_mwh"],
        mode="lines",
        fill="tonexty",
        name="P25-P75",
        line=dict(width=0),
    ))
    fig.add_trace(go.Scatter(
        x=price_profile["hour"],
        y=price_profile["price_mean_eur_per_mwh"],
        mode="lines+markers",
        name="Mean price",
    ))

    fig.update_layout(
        title="Typical daily price profile",
        xaxis_title="Hour",
        yaxis_title="EUR/MWh",
        height=450,
    )
    return fig


def plot_single_variant_price_pv_profile(price_profile: pd.DataFrame, pv_profile: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=price_profile["hour"],
        y=price_profile["price_mean_eur_per_mwh"],
        mode="lines+markers",
        name="Mean price (EUR/MWh)",
        yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=pv_profile["hour"],
        y=pv_profile["e_grid_mean_mwh"],
        mode="lines+markers",
        name="Mean production (MWh)",
        yaxis="y2",
    ))
    fig.add_trace(go.Scatter(
        x=pv_profile["hour"],
        y=pv_profile["e_grid_injected_mean_mwh"],
        mode="lines+markers",
        name="Mean injected energy (MWh)",
        yaxis="y2",
    ))

    fig.update_layout(
        title="Typical price + production profile",
        xaxis_title="Hour",
        yaxis=dict(title="EUR/MWh"),
        yaxis2=dict(title="MWh", overlaying="y", side="right"),
        height=500,
    )
    return fig


def plot_comparison_price_pv_profile(
    price_profile: pd.DataFrame,
    pv_profile_a: pd.DataFrame,
    pv_profile_b: pd.DataFrame,
    label_a: str,
    label_b: str,
) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=price_profile["hour"],
        y=price_profile["price_mean_eur_per_mwh"],
        mode="lines+markers",
        name="Mean price (EUR/MWh)",
        yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=pv_profile_a["hour"],
        y=pv_profile_a["e_grid_mean_mwh"],
        mode="lines+markers",
        name=f"{label_a} - mean production",
        yaxis="y2",
    ))
    fig.add_trace(go.Scatter(
        x=pv_profile_b["hour"],
        y=pv_profile_b["e_grid_mean_mwh"],
        mode="lines+markers",
        name=f"{label_b} - mean production",
        yaxis="y2",
    ))

    fig.update_layout(
        title="Typical price + production comparison",
        xaxis_title="Hour",
        yaxis=dict(title="EUR/MWh"),
        yaxis2=dict(title="MWh", overlaying="y", side="right"),
        height=500,
    )
    return fig


def plot_single_variant_monthly_summary(monthly_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_df["month"],
        y=monthly_df["energy_curtailed_negative_mwh"],
        name="Curtailed energy (MWh)",
    ))
    fig.add_trace(go.Scatter(
        x=monthly_df["month"],
        y=monthly_df["market_value_eur"],
        mode="lines+markers",
        name="Market value (EUR)",
        yaxis="y2",
    ))

    fig.update_layout(
        title="Monthly curtailed energy and market value",
        xaxis_title="Month",
        yaxis=dict(title="MWh"),
        yaxis2=dict(title="EUR", overlaying="y", side="right"),
        height=500,
    )
    return fig


def plot_comparison_monthly_delta(monthly_comp: pd.DataFrame) -> go.Figure:
    col = "delta_market_value_eur_b_minus_a"
    if col not in monthly_comp.columns:
        return go.Figure()

    fig = px.bar(
        monthly_comp,
        x="month",
        y=col,
        title="Monthly market value delta (B - A)",
        labels={"month": "Month", col: "EUR"},
        text_auto=".0f",
    )
    fig.update_layout(height=450)
    return fig


def plot_bess_monthly_summary(bess_monthly: pd.DataFrame, title_suffix: str = "") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bess_monthly["month"],
        y=bess_monthly["energy_discharged_to_grid_mwh"],
        name="Discharged energy (MWh)",
    ))
    fig.add_trace(go.Scatter(
        x=bess_monthly["month"],
        y=bess_monthly["bess_added_value_eur"],
        mode="lines+markers",
        name="Added BESS value (EUR)",
        yaxis="y2",
    ))

    fig.update_layout(
        title=f"Monthly BESS summary{title_suffix}",
        xaxis_title="Month",
        yaxis=dict(title="MWh"),
        yaxis2=dict(title="EUR", overlaying="y", side="right"),
        height=450,
    )
    return fig


# =============================================================================
# Header
# =============================================================================

st.title(t("MARKET_ANALYSIS_TITLE"))
st.caption(t("MARKET_ANALYSIS_DESC"))

with st.container(border=True):
    top1, top2 = st.columns([0.9, 0.1])
    with top1:
        st.subheader(t("MARKET_ANALYSIS_CONFIG_TITLE"))
    with top2:
        _help_popover("MARKET_ANALYSIS_HELP_CONFIG_TITLE", "MARKET_ANALYSIS_HELP_CONFIG_BODY")

    c1, c2, c3 = st.columns([1.2, 1.2, 1.2])

    with c1:
        market_source_mode = st.radio(
            t("MARKET_ANALYSIS_MARKET_SOURCE"),
            options=["api", "csv"],
            format_func=lambda x: t("MARKET_ANALYSIS_MARKET_SOURCE_API") if x == "api" else t("MARKET_ANALYSIS_MARKET_SOURCE_CSV"),
            horizontal=True,
        )

    with c2:
        analysis_mode = st.radio(
            t("MARKET_ANALYSIS_ANALYSIS_MODE"),
            options=["single_variant", "comparison"],
            format_func=lambda x: t("MARKET_ANALYSIS_MODE_SINGLE") if x == "single_variant" else t("MARKET_ANALYSIS_MODE_COMPARISON"),
            horizontal=True,
        )

    with c3:
        enable_bess = st.checkbox(t("MARKET_ANALYSIS_ENABLE_BESS"), value=False)

    market_csv_bytes = None
    market_bzn = None
    market_start = None
    market_end = None

    if market_source_mode == "api":
        c_api_1, c_api_2 = st.columns([1.2, 1])
        with c_api_1:
            selected_country = st.selectbox(
                t("MARKET_ANALYSIS_MARKET_ZONE"),
                list(BZN_OPTIONS.keys()),
                index=0,
            )
            market_bzn = BZN_OPTIONS[selected_country]
        with c_api_2:
            current_year = datetime.now().year
            year_options = list(range(current_year, current_year - 8, -1))
            default_idx = 1 if len(year_options) > 1 else 0
            selected_year = st.selectbox(t("MARKET_ANALYSIS_YEAR"), year_options, index=default_idx)
            market_start = f"{selected_year}-01-01"
            market_end = f"{selected_year}-12-31"
    else:
        market_csv_file = st.file_uploader(
            t("MARKET_ANALYSIS_MARKET_CSV_UPLOAD"),
            type=["csv"],
            key="market_csv_file",
        )
        if market_csv_file is not None:
            market_csv_bytes = market_csv_file.getvalue()

    st.markdown(f"### {t('MARKET_ANALYSIS_PVSYST_SOURCES_TITLE')}")
    pv_a_col1, pv_a_col2 = st.columns([2, 1])

    with pv_a_col1:
        pv_file_a = st.file_uploader(
            t("MARKET_ANALYSIS_PV_FILE_A"),
            type=["csv", "txt"],
            key="pv_file_a",
        )
    with pv_a_col2:
        pv_label_a = st.text_input(t("MARKET_ANALYSIS_PV_LABEL_A"), value="Fixed")

    pv_file_b = None
    pv_label_b = "Variant B"

    if analysis_mode == "comparison":
        pv_b_col1, pv_b_col2 = st.columns([2, 1])
        with pv_b_col1:
            pv_file_b = st.file_uploader(
                t("MARKET_ANALYSIS_PV_FILE_B"),
                type=["csv", "txt"],
                key="pv_file_b",
            )
        with pv_b_col2:
            pv_label_b = st.text_input(t("MARKET_ANALYSIS_PV_LABEL_B"), value="Tracker")

    bess_params: Dict[str, Any] = {}
    if enable_bess:
        with st.expander(t("MARKET_ANALYSIS_BESS_PARAMS_TITLE"), expanded=False):
            b1, b2, b3 = st.columns(3)
            with b1:
                capacity_mwh = st.number_input(t("MARKET_ANALYSIS_BESS_PARAM_CAPACITY"), min_value=0.0, value=0.0, step=1.0)
                charge_power_mw = st.number_input(t("MARKET_ANALYSIS_BESS_PARAM_CHARGE_POWER"), min_value=0.0, value=0.0, step=1.0)
            with b2:
                discharge_power_mw = st.number_input(t("MARKET_ANALYSIS_BESS_PARAM_DISCHARGE_POWER"), min_value=0.0, value=0.0, step=1.0)
                roundtrip_efficiency = st.number_input(t("MARKET_ANALYSIS_BESS_PARAM_EFFICIENCY"), min_value=0.0, max_value=1.0, value=0.0, step=0.01)
            with b3:
                charge_threshold = st.number_input(t("MARKET_ANALYSIS_BESS_PARAM_CHARGE_THRESHOLD"), value=0.0, step=1.0)
                discharge_threshold = st.number_input(t("MARKET_ANALYSIS_BESS_PARAM_DISCHARGE_THRESHOLD"), value=0.0, step=1.0)

            bess_params = _clean_bess_params(
                capacity_mwh=capacity_mwh if capacity_mwh > 0 else None,
                charge_power_mw=charge_power_mw if charge_power_mw > 0 else None,
                discharge_power_mw=discharge_power_mw if discharge_power_mw > 0 else None,
                roundtrip_efficiency=roundtrip_efficiency if roundtrip_efficiency > 0 else None,
                charge_price_threshold_eur_per_mwh=charge_threshold,
                discharge_price_threshold_eur_per_mwh=discharge_threshold if discharge_threshold > 0 else None,
            )

    run_btn = st.button(t("MARKET_ANALYSIS_RUN_BUTTON"), type="primary")

if run_btn:
    try:
        if market_source_mode == "csv" and market_csv_bytes is None:
            st.error(t("MARKET_ANALYSIS_ERROR_NEED_MARKET_CSV"))
        elif pv_file_a is None:
            st.error(t("MARKET_ANALYSIS_ERROR_NEED_PV_A"))
        elif analysis_mode == "comparison" and pv_file_b is None:
            st.error(t("MARKET_ANALYSIS_ERROR_NEED_PV_B"))
        else:
            with st.spinner(t("MARKET_ANALYSIS_RUNNING")):
                result = run_market_analysis_from_sources(
                    market_source_mode=market_source_mode,
                    market_bzn=market_bzn,
                    market_start=market_start,
                    market_end=market_end,
                    market_csv_source=market_csv_bytes,
                    pv_source_a=pv_file_a.getvalue(),
                    pv_variant_label_a=pv_label_a or "Variant A",
                    pv_source_b=pv_file_b.getvalue() if pv_file_b is not None else None,
                    pv_variant_label_b=pv_label_b or "Variant B",
                    enable_bess=enable_bess,
                    bess_params=bess_params,
                )
            st.session_state["market_analysis_result"] = result
    except Exception as exc:
        st.exception(exc)

result = st.session_state.get("market_analysis_result")

if result is None:
    st.info(t("MARKET_ANALYSIS_INFO_WAITING"))
    st.stop()

if result.warnings:
    with st.expander(f"{t('MARKET_ANALYSIS_WARNINGS_TITLE')} ({len(result.warnings)})", expanded=False):
        for w in result.warnings:
            st.write(f"- {w}")

st.subheader(t("MARKET_ANALYSIS_TIME_SECTION_TITLE"))
st.caption(t("MARKET_ANALYSIS_TIME_SECTION_DESC"))

with st.expander(t("MARKET_ANALYSIS_TIME_EXPANDER"), expanded=False):
    t1, t2, t3 = st.columns(3)
    with t1:
        st.metric(
            t("MARKET_ANALYSIS_TIME_MARKET_ORIGINAL"),
            _fmt_step(result.market_result.meta, "time_step_minutes_original"),
        )
        st.metric(
            t("MARKET_ANALYSIS_TIME_MARKET_ANALYSIS"),
            _fmt_step(result.market_result.meta, "time_step_minutes_analysis"),
        )

    with t2:
        st.metric(
            t("MARKET_ANALYSIS_TIME_PV_A_ORIGINAL"),
            _fmt_step(result.pv_result_a.meta, "time_step_minutes_original"),
        )
        st.metric(
            t("MARKET_ANALYSIS_TIME_PV_A_ANALYSIS"),
            _fmt_step(result.pv_result_a.meta, "time_step_minutes_analysis"),
        )

    with t3:
        if result.pv_result_b is not None:
            st.metric(
                t("MARKET_ANALYSIS_TIME_PV_B_ORIGINAL"),
                _fmt_step(result.pv_result_b.meta, "time_step_minutes_original"),
            )
            st.metric(
                t("MARKET_ANALYSIS_TIME_PV_B_ANALYSIS"),
                _fmt_step(result.pv_result_b.meta, "time_step_minutes_analysis"),
            )
        else:
            st.metric(
                t("MARKET_ANALYSIS_TIME_ANALYSIS_STEP"),
                _fmt_step(result.analysis_result_a.meta, "analysis_time_step_minutes"),
            )
            st.caption(t("MARKET_ANALYSIS_TIME_ANALYSIS_NOTE"))

    h1, h2 = st.columns(2)
    with h1:
        st.write(f"**{t('MARKET_ANALYSIS_TIME_MARKET_BLOCK')}**")
        st.write(f"{t('MARKET_ANALYSIS_TIME_ORIGINAL_ROWS')}: {_fmt_int(result.market_result.meta.get('n_rows_original'))}")
        st.write(f"{t('MARKET_ANALYSIS_TIME_ANALYSIS_ROWS')}: {_fmt_int(result.market_result.meta.get('n_rows_analysis'))}")
        st.write(f"{t('MARKET_ANALYSIS_TIME_RESAMPLED')}: {result.market_result.meta.get('resampled_to_analysis_step', False)}")
        if result.market_result.meta.get("resampling_method"):
            st.write(f"{t('MARKET_ANALYSIS_TIME_METHOD')}: {result.market_result.meta.get('resampling_method')}")

    with h2:
        st.write(f"**{t('MARKET_ANALYSIS_TIME_PV_BLOCK')}**")
        st.write(f"{t('MARKET_ANALYSIS_TIME_ORIGINAL_ROWS')}: {_fmt_int(result.pv_result_a.meta.get('n_rows_original'))}")
        st.write(f"{t('MARKET_ANALYSIS_TIME_ANALYSIS_ROWS')}: {_fmt_int(result.pv_result_a.meta.get('n_rows_analysis'))}")
        st.write(f"{t('MARKET_ANALYSIS_TIME_RESAMPLED')}: {result.pv_result_a.meta.get('resampled_to_analysis_step', False)}")
        if result.pv_result_a.meta.get("resampling_method"):
            st.write(f"{t('MARKET_ANALYSIS_TIME_METHOD')}: {result.pv_result_a.meta.get('resampling_method')}")
        if result.pv_result_a.meta.get("energy_conversion_basis"):
            st.write(f"{t('MARKET_ANALYSIS_TIME_ENERGY_CONVERSION')}: {result.pv_result_a.meta.get('energy_conversion_basis')}")

tab_main, tab_detail = st.tabs([t("MARKET_ANALYSIS_TAB_MAIN"), t("MARKET_ANALYSIS_TAB_DETAILED")])

with tab_main:
    head1, head2 = st.columns([0.9, 0.1])
    with head1:
        st.subheader(t("MARKET_ANALYSIS_EXEC_SUMMARY_TITLE"))
    with head2:
        _help_popover("MARKET_ANALYSIS_HELP_GENERAL_RESULTS_TITLE", "MARKET_ANALYSIS_HELP_GENERAL_RESULTS_BODY")

    if result.mode == "single_variant":
        ann = result.analysis_result_a.annual_indicators
        market_only = result.analysis_result_a.market_only_summary

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("MARKET_ANALYSIS_KPI_PRICE_MEAN"), _fmt_float(market_only["price_mean_eur_per_mwh"], 1, " EUR/MWh"))
        c2.metric(t("MARKET_ANALYSIS_KPI_NEGATIVE_HOURS"), _fmt_int(market_only["negative_hours"]))
        c3.metric(t("MARKET_ANALYSIS_KPI_ENERGY_INJECTED"), _fmt_float(ann["energy_injected_mwh"], 1, " MWh"))
        c4.metric(t("MARKET_ANALYSIS_KPI_MARKET_VALUE"), _fmt_float(ann["market_value_eur"], 0, " EUR"))

        c5, c6, c7, c8 = st.columns(4)
        c5.metric(t("MARKET_ANALYSIS_KPI_CURTAILED_ENERGY"), _fmt_float(ann["energy_curtailed_negative_mwh"], 1, " MWh"))
        c6.metric(t("MARKET_ANALYSIS_KPI_CAPTURE_PRICE"), _fmt_float(ann["capture_price_eur_per_mwh"], 1, " EUR/MWh"))
        c7.metric(t("MARKET_ANALYSIS_KPI_CAPTURE_RATE"), _fmt_float(ann["capture_rate"], 2))
        c8.metric(t("MARKET_ANALYSIS_KPI_CURTAILED_SHARE"), _fmt_float(ann["curtailed_share_pct"], 2, " %"))

        concl1, concl2 = st.columns([0.9, 0.1])
        with concl1:
            st.markdown(f"### {t('MARKET_ANALYSIS_CONCLUSIONS_TITLE')}")
        with concl2:
            _help_popover("MARKET_ANALYSIS_HELP_TITLE", "MARKET_ANALYSIS_HELP_CAPTURE_RATE")

        for txt in _single_variant_conclusions(result):
            st.markdown(f"- {txt}")

        charts1, charts2 = st.columns([0.9, 0.1])
        with charts1:
            st.markdown(f"### {t('MARKET_ANALYSIS_MAIN_CHARTS_TITLE')}")
        with charts2:
            _help_popover("MARKET_ANALYSIS_HELP_PROFILES_TITLE", "MARKET_ANALYSIS_HELP_PROFILES_BODY")

        fig1 = plot_market_heatmap(result.market_result.data_analysis)
        st.plotly_chart(fig1, width="stretch", config=PLOT_CONFIG)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig2 = plot_typical_price_profile(result.analysis_result_a.market_profile_typical_daily)
            st.plotly_chart(fig2, width="stretch", config=PLOT_CONFIG)
        with col_g2:
            fig3 = plot_single_variant_price_pv_profile(
                result.analysis_result_a.market_profile_typical_daily,
                result.analysis_result_a.pv_profile_typical_daily,
            )
            st.plotly_chart(fig3, width="stretch", config=PLOT_CONFIG)

        fig4 = plot_single_variant_monthly_summary(result.analysis_result_a.monthly_summary)
        st.plotly_chart(fig4, width="stretch", config=PLOT_CONFIG)

        if result.bess_result_a is not None:
            st.markdown(f"### {t('MARKET_ANALYSIS_BESS_TITLE')}")
            b_ann = result.bess_result_a.annual_indicators
            bc1, bc2, bc3, bc4 = st.columns(4)
            bc1.metric(t("MARKET_ANALYSIS_BESS_KPI_AVAILABLE"), _fmt_float(b_ann["energy_available_for_storage_mwh"], 1, " MWh"))
            bc2.metric(t("MARKET_ANALYSIS_BESS_KPI_DISCHARGED"), _fmt_float(b_ann["energy_discharged_to_grid_mwh"], 1, " MWh"))
            bc3.metric(t("MARKET_ANALYSIS_BESS_KPI_ADDED_VALUE"), _fmt_float(b_ann["bess_added_value_eur"], 0, " EUR"))
            bc4.metric(t("MARKET_ANALYSIS_BESS_KPI_EQ_CYCLES"), _fmt_float(b_ann["equivalent_cycles"], 1))

            fig_bess = plot_bess_monthly_summary(
                result.bess_result_a.monthly_summary,
                title_suffix=f" - {result.meta['variant_label_a']}",
            )
            st.plotly_chart(fig_bess, width="stretch", config=PLOT_CONFIG)

    else:
        comp = result.comparison_result
        ann_a = result.analysis_result_a.annual_indicators
        ann_b = result.analysis_result_b.annual_indicators

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            t("MARKET_ANALYSIS_KPI_VARIANT_ENERGY").format(label=result.meta["variant_label_a"]),
            _fmt_float(ann_a["energy_theoretical_mwh"], 1, " MWh"),
        )
        c2.metric(
            t("MARKET_ANALYSIS_KPI_VARIANT_ENERGY").format(label=result.meta["variant_label_b"]),
            _fmt_float(ann_b["energy_theoretical_mwh"], 1, " MWh"),
            delta=_fmt_float(ann_b["energy_theoretical_mwh"] - ann_a["energy_theoretical_mwh"], 1, " MWh"),
        )
        c3.metric(
            t("MARKET_ANALYSIS_KPI_VARIANT_VALUE").format(label=result.meta["variant_label_a"]),
            _fmt_float(ann_a["market_value_eur"], 0, " EUR"),
        )
        c4.metric(
            t("MARKET_ANALYSIS_KPI_VARIANT_VALUE").format(label=result.meta["variant_label_b"]),
            _fmt_float(ann_b["market_value_eur"], 0, " EUR"),
            delta=_fmt_float(ann_b["market_value_eur"] - ann_a["market_value_eur"], 0, " EUR"),
        )

        c5, c6, c7, c8 = st.columns(4)
        c5.metric(
            t("MARKET_ANALYSIS_KPI_VARIANT_CAPTURE_PRICE").format(label=result.meta["variant_label_a"]),
            _fmt_float(ann_a["capture_price_eur_per_mwh"], 1, " EUR/MWh"),
        )
        c6.metric(
            t("MARKET_ANALYSIS_KPI_VARIANT_CAPTURE_PRICE").format(label=result.meta["variant_label_b"]),
            _fmt_float(ann_b["capture_price_eur_per_mwh"], 1, " EUR/MWh"),
        )
        c7.metric(
            t("MARKET_ANALYSIS_KPI_VARIANT_CURTAILED").format(label=result.meta["variant_label_a"]),
            _fmt_float(ann_a["energy_curtailed_negative_mwh"], 1, " MWh"),
        )
        c8.metric(
            t("MARKET_ANALYSIS_KPI_VARIANT_CURTAILED").format(label=result.meta["variant_label_b"]),
            _fmt_float(ann_b["energy_curtailed_negative_mwh"], 1, " MWh"),
        )

        concl1, concl2 = st.columns([0.9, 0.1])
        with concl1:
            st.markdown(f"### {t('MARKET_ANALYSIS_CONCLUSIONS_TITLE')}")
        with concl2:
            _help_popover("MARKET_ANALYSIS_HELP_TITLE", "MARKET_ANALYSIS_HELP_CAPTURE_RATE")

        for item in comp.conclusions:
            st.markdown(f"- {t(item['key']).format(**item['params'])}")

        st.markdown(f"### {t('MARKET_ANALYSIS_MAIN_CHARTS_TITLE')}")
        fig1 = plot_market_heatmap(result.market_result.data_analysis)
        st.plotly_chart(fig1, width="stretch", config=PLOT_CONFIG)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig2 = plot_typical_price_profile(result.analysis_result_a.market_profile_typical_daily)
            st.plotly_chart(fig2, width="stretch", config=PLOT_CONFIG)
        with col_g2:
            fig3 = plot_comparison_price_pv_profile(
                result.analysis_result_a.market_profile_typical_daily,
                result.analysis_result_a.pv_profile_typical_daily,
                result.analysis_result_b.pv_profile_typical_daily,
                result.meta["variant_label_a"],
                result.meta["variant_label_b"],
            )
            st.plotly_chart(fig3, width="stretch", config=PLOT_CONFIG)

        fig4 = plot_comparison_monthly_delta(comp.monthly_comparison)
        st.plotly_chart(fig4, width="stretch", config=PLOT_CONFIG)

        if result.bess_result_a is not None:
            st.markdown(f"### {t('MARKET_ANALYSIS_BESS_TITLE')}")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                fig_bess_a = plot_bess_monthly_summary(
                    result.bess_result_a.monthly_summary,
                    title_suffix=f" - {result.meta['variant_label_a']}",
                )
                st.plotly_chart(fig_bess_a, width="stretch", config=PLOT_CONFIG)
            with col_b2:
                if result.bess_result_b is not None:
                    fig_bess_b = plot_bess_monthly_summary(
                        result.bess_result_b.monthly_summary,
                        title_suffix=f" - {result.meta['variant_label_b']}",
                    )
                    st.plotly_chart(fig_bess_b, width="stretch", config=PLOT_CONFIG)

with tab_detail:
    topd1, topd2 = st.columns([0.9, 0.1])
    with topd1:
        st.subheader(t("MARKET_ANALYSIS_DETAIL_TITLE"))
    with topd2:
        _help_popover("MARKET_ANALYSIS_HELP_TITLE", "MARKET_ANALYSIS_HELP_BESS")

    col_meta_1, col_meta_2 = st.columns(2)
    with col_meta_1:
        st.write(f"**{t('MARKET_ANALYSIS_META_GLOBAL')}**")
        st.json(result.meta)
    with col_meta_2:
        st.write(f"**{t('MARKET_ANALYSIS_META_MARKET')}**")
        st.json(result.market_result.meta)

    col_meta_3, col_meta_4 = st.columns(2)
    with col_meta_3:
        st.write(f"**{t('MARKET_ANALYSIS_META_PV_A')}**")
        st.json(result.pv_result_a.meta)
    with col_meta_4:
        if result.pv_result_b is not None:
            st.write(f"**{t('MARKET_ANALYSIS_META_PV_B')}**")
            st.json(result.pv_result_b.meta)

    if result.bess_result_a is not None:
        with st.expander(t("MARKET_ANALYSIS_BESS_ASSUMPTIONS_TITLE"), expanded=False):
            st.json(result.bess_result_a.assumptions_used)

    st.markdown(f"### {t('MARKET_ANALYSIS_EXPORTS_TITLE')}")

    exp1, exp2, exp3 = st.columns(3)
    with exp1:
        st.download_button(
            t("MARKET_ANALYSIS_EXPORT_MARKET_ORIGINAL"),
            data=_df_to_csv_bytes(result.market_result.data_original),
            file_name="market_data_original.csv",
            mime="text/csv",
        )
    with exp2:
        st.download_button(
            t("MARKET_ANALYSIS_EXPORT_MERGED").format(label=result.meta["variant_label_a"]),
            data=_df_to_csv_bytes(result.analysis_result_a.merged_data),
            file_name=f"merged_{result.meta['variant_label_a']}.csv",
            mime="text/csv",
        )
    with exp3:
        if result.analysis_result_b is not None:
            st.download_button(
                t("MARKET_ANALYSIS_EXPORT_MERGED").format(label=result.meta["variant_label_b"]),
                data=_df_to_csv_bytes(result.analysis_result_b.merged_data),
                file_name=f"merged_{result.meta['variant_label_b']}.csv",
                mime="text/csv",
            )

    st.markdown(f"### {t('MARKET_ANALYSIS_TABLES_TITLE')}")

    with st.expander(t("MARKET_ANALYSIS_TABLE_ANNUAL_A"), expanded=True):
        st.dataframe(_styled_df(_series_dict_to_df(result.analysis_result_a.annual_indicators)), width="stretch")
        st.download_button(
            t("MARKET_ANALYSIS_EXPORT_ANNUAL_A"),
            data=_df_to_csv_bytes(_series_dict_to_df(result.analysis_result_a.annual_indicators)),
            file_name="annual_summary_a.csv",
            mime="text/csv",
            key="dl_annual_a",
        )

    with st.expander(t("MARKET_ANALYSIS_TABLE_MONTHLY_A"), expanded=False):
        st.dataframe(_styled_df(result.analysis_result_a.monthly_summary), width="stretch")
        st.download_button(
            t("MARKET_ANALYSIS_EXPORT_MONTHLY_A"),
            data=_df_to_csv_bytes(result.analysis_result_a.monthly_summary),
            file_name="monthly_summary_a.csv",
            mime="text/csv",
            key="dl_monthly_a",
        )

    with st.expander(t("MARKET_ANALYSIS_TABLE_SEASONAL_A"), expanded=False):
        st.dataframe(_styled_df(result.analysis_result_a.seasonal_summary), width="stretch")
        st.download_button(
            t("MARKET_ANALYSIS_EXPORT_SEASONAL_A"),
            data=_df_to_csv_bytes(result.analysis_result_a.seasonal_summary),
            file_name="seasonal_summary_a.csv",
            mime="text/csv",
            key="dl_seasonal_a",
        )

    with st.expander(t("MARKET_ANALYSIS_TABLE_MARKET_ONLY"), expanded=False):
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_MARKET_INDICATORS')}**")
        st.dataframe(_styled_df(_series_dict_to_df(result.analysis_result_a.market_only_summary)), width="stretch")
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_PRICE_DISTRIBUTION')}**")
        st.dataframe(_styled_df(_series_dict_to_df(result.analysis_result_a.price_distribution_summary)), width="stretch")
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_MONTHLY_MARKET')}**")
        st.dataframe(_styled_df(result.analysis_result_a.monthly_market_summary), width="stretch")
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_SEASONAL_MARKET')}**")
        st.dataframe(_styled_df(result.analysis_result_a.seasonal_market_summary), width="stretch")

    with st.expander(t("MARKET_ANALYSIS_TABLE_TYPICAL_PROFILES"), expanded=False):
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_TYPICAL_PRICE')}**")
        st.dataframe(_styled_df(result.analysis_result_a.market_profile_typical_daily), width="stretch")
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_TYPICAL_PV_A')}**")
        st.dataframe(_styled_df(result.analysis_result_a.pv_profile_typical_daily), width="stretch")
        if result.analysis_result_b is not None:
            st.write(f"**{t('MARKET_ANALYSIS_TABLE_TYPICAL_PV_B')}**")
            st.dataframe(_styled_df(result.analysis_result_b.pv_profile_typical_daily), width="stretch")

    with st.expander(t("MARKET_ANALYSIS_TABLE_ORIGINAL_VS_ANALYSIS"), expanded=False):
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_MARKET_ORIGINAL')}**")
        st.dataframe(result.market_result.data_original.head(200), width="stretch")
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_MARKET_ANALYSIS')}**")
        st.dataframe(result.market_result.data_analysis.head(200), width="stretch")

        st.write(f"**{t('MARKET_ANALYSIS_TABLE_PV_A_ORIGINAL')}**")
        st.dataframe(result.pv_result_a.data_original.head(200), width="stretch")
        st.write(f"**{t('MARKET_ANALYSIS_TABLE_PV_A_ANALYSIS')}**")
        st.dataframe(result.pv_result_a.data_analysis.head(200), width="stretch")

        if result.pv_result_b is not None:
            st.write(f"**{t('MARKET_ANALYSIS_TABLE_PV_B_ORIGINAL')}**")
            st.dataframe(result.pv_result_b.data_original.head(200), width="stretch")
            st.write(f"**{t('MARKET_ANALYSIS_TABLE_PV_B_ANALYSIS')}**")
            st.dataframe(result.pv_result_b.data_analysis.head(200), width="stretch")

    if result.analysis_result_b is not None and result.comparison_result is not None:
        with st.expander(t("MARKET_ANALYSIS_COMPARE_TITLE"), expanded=True):
            st.write(f"**{t('MARKET_ANALYSIS_COMPARE_ANNUAL')}**")
            annual_comp_df = pd.DataFrame(result.comparison_result.annual_comparison["metrics_table"])
            st.dataframe(_styled_df(annual_comp_df), width="stretch")

            st.write(f"**{t('MARKET_ANALYSIS_COMPARE_MONTHLY')}**")
            st.dataframe(_styled_df(result.comparison_result.monthly_comparison), width="stretch")

            st.write(f"**{t('MARKET_ANALYSIS_COMPARE_SEASONAL')}**")
            st.dataframe(_styled_df(result.comparison_result.seasonal_comparison), width="stretch")

            st.write(f"**{t('MARKET_ANALYSIS_COMPARE_CONCLUSIONS')}**")
            for item in result.comparison_result.conclusions:
                st.write(f"- {t(item['key']).format(**item['params'])}")

    if result.bess_result_a is not None:
        with st.expander(t("MARKET_ANALYSIS_BESS_VARIANT_TITLE").format(label=result.meta["variant_label_a"]), expanded=False):
            st.write(f"**{t('MARKET_ANALYSIS_BESS_ANNUAL')}**")
            st.dataframe(_styled_df(_series_dict_to_df(result.bess_result_a.annual_indicators)), width="stretch")
            st.write(f"**{t('MARKET_ANALYSIS_BESS_MONTHLY')}**")
            st.dataframe(_styled_df(result.bess_result_a.monthly_summary), width="stretch")
            st.write(f"**{t('MARKET_ANALYSIS_BESS_SEASONAL')}**")
            st.dataframe(_styled_df(result.bess_result_a.seasonal_summary), width="stretch")
            st.write(f"**{t('MARKET_ANALYSIS_BESS_HOURLY_HEAD')}**")
            st.dataframe(_styled_df(result.bess_result_a.hourly_data.head(200)), width="stretch")

    if result.bess_result_b is not None:
        with st.expander(t("MARKET_ANALYSIS_BESS_VARIANT_TITLE").format(label=result.meta["variant_label_b"]), expanded=False):
            st.write(f"**{t('MARKET_ANALYSIS_BESS_ANNUAL')}**")
            st.dataframe(_styled_df(_series_dict_to_df(result.bess_result_b.annual_indicators)), width="stretch")
            st.write(f"**{t('MARKET_ANALYSIS_BESS_MONTHLY')}**")
            st.dataframe(_styled_df(result.bess_result_b.monthly_summary), width="stretch")
            st.write(f"**{t('MARKET_ANALYSIS_BESS_SEASONAL')}**")
            st.dataframe(_styled_df(result.bess_result_b.seasonal_summary), width="stretch")
            st.write(f"**{t('MARKET_ANALYSIS_BESS_HOURLY_HEAD')}**")
            st.dataframe(_styled_df(result.bess_result_b.hourly_data.head(200)), width="stretch")