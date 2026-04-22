from __future__ import annotations

from typing import Dict, List

import pandas as pd

from core.bess_sizing.v2_models import AnalysisMode, BessRecommendation


def _find_row(summary_df: pd.DataFrame, config_id: str | None) -> pd.Series | None:
    if config_id is None or summary_df is None or summary_df.empty:
        return None
    rows = summary_df.loc[summary_df["config_id"] == config_id]
    if rows.empty:
        return None
    return rows.iloc[0]


def generate_auto_conclusions(
    *,
    summary_df: pd.DataFrame,
    mode: AnalysisMode,
    recommendations: Dict[str, BessRecommendation],
    sensitivity_warning: bool,
) -> List[str]:
    out: List[str] = []
    if summary_df is None or summary_df.empty:
        return out

    brute = recommendations.get("brut_max")
    techno = recommendations.get("techno")
    marginal = recommendations.get("marginal")

    brute_row = _find_row(summary_df, brute.config_id if brute else None)
    techno_row = _find_row(summary_df, techno.config_id if techno else None)
    marginal_row = _find_row(summary_df, marginal.config_id if marginal else None)

    if brute_row is not None and float(brute_row.get("is_upper_boundary", 0)) > 0.5:
        out.append(
            "La configuration maximisant le gain brut est en bord de domaine ; le domaine de recherche peut etre trop restreint."
        )

    if brute_row is not None and marginal_row is not None:
        if str(brute_row["config_id"]) != str(marginal_row["config_id"]):
            out.append(
                "La configuration maximisant le gain brut n'est pas celle recommandee par optimisation marginale."
            )
        out.append(
            f"La configuration marginale recommandee atteint {float(marginal_row.get('gain_share_of_max_pct', 0.0)):.1f} % du gain brut maximal."
        )

    if techno is not None and techno.config_id is None:
        out.append("Aucune configuration rentable dans le domaine teste sous les hypotheses economiques actuelles.")
        if techno.reason:
            out.append(techno.reason)
    elif techno_row is not None:
        if brute_row is not None and str(techno_row["config_id"]) != str(brute_row["config_id"]):
            out.append(
                "La configuration techno-economique recommandee differe de la configuration a gain brut maximal."
            )
        if techno is not None and techno.reason:
            out.append(techno.reason)
        share = techno_row.get("gain_share_of_max_pct")
        if pd.notna(share):
            out.append(
                f"La configuration techno-economique recommandee atteint {float(share):.1f} % du gain brut maximal."
            )
        net_margin = techno_row.get("annual_net_margin_eur")
        if pd.notna(net_margin):
            if float(net_margin) < 0:
                out.append(
                    "Avec les hypotheses CAPEX/OPEX retenues, la marge nette annualisee est negative pour la configuration recommandee."
                )
            else:
                out.append(
                    "La configuration technico-economique recommandee presente une marge nette annualisee positive."
                )

    if marginal_row is not None:
        power_sat = float(marginal_row.get("power_saturation_rate_pct", 0.0))
        energy_sat = float(marginal_row.get("energy_saturation_rate_pct", 0.0))
        underused = float(marginal_row.get("underutilized_capacity_share_pct", 0.0))
        if power_sat > energy_sat * 1.5 and power_sat >= 10:
            out.append(
                "Le systeme semble davantage limite par la puissance de conversion que par la capacite energetique."
            )
        elif energy_sat > power_sat * 1.5 and energy_sat >= 10:
            out.append(
                "Le systeme semble davantage limite par la capacite energetique que par la puissance."
            )
        if underused >= 35:
            out.append(
                "Une part significative de la capacite utile reste peu exploitee, ce qui suggere un possible surdimensionnement energetique."
            )

    max_marginal_mwh = float(summary_df.get("marginal_gain_per_mwh_eur", pd.Series(dtype=float)).max() or 0.0)
    min_marginal_mwh = float(summary_df.get("marginal_gain_per_mwh_eur", pd.Series(dtype=float)).min() or 0.0)
    if max_marginal_mwh > 0 and min_marginal_mwh <= 0.1 * max_marginal_mwh:
        out.append(
            "Le gain marginal decroit fortement sur les grandes tailles ; une zone de saturation de valeur est atteinte."
        )

    if mode == "mode_b_default_costs":
        out.append(
            "Les conclusions economiques reposent sur des hypotheses de cout simplifiees par defaut ; une analyse de sensibilite est recommandee."
        )

    if sensitivity_warning:
        out.append(
            "Les resultats apparaissent sensibles aux hypotheses CAPEX/OPEX (ecart faible entre les meilleures configurations)."
        )

    deduped: List[str] = []
    seen = set()
    for line in out:
        if line not in seen:
            deduped.append(line)
            seen.add(line)
    return deduped
