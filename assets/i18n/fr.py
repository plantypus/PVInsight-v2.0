# assets/i18n/fr.py

TEXTS = {
    # =========================================================================
    # App (global)
    # =========================================================================
    "APP_PAGE_TITLE": "PVInsight",
    "APP_TITLE": "PVInsight — Analyse PVSyst",
    "APP_VERSION_LABEL": "Version",
    "APP_DESCRIPTION": (
        "Outil Streamlit (vide pour l’instant) destiné à accueillir des briques "
        "d’analyse des exports PVSyst (hourly results, bilans mensuels, PR, pertes, etc.)."
    ),

    # =========================================================================
    # Navigation / Pages
    # =========================================================================
    "PAGE_HOME_TITLE": "Accueil",
    "PAGE_SETTINGS_TITLE": "Réglages",
    "PAGE_EXIT_TITLE": "Quitter",

    # Sidebar / common buttons
    "BTN_GO_HOME": "🏠 Accueil",
    "BTN_EXIT": "⛔ Quitter",

    # =========================================================================
    # Language
    # =========================================================================
    "LANG_LABEL": "Langue",
    "LANG_FR": "Français",
    "LANG_EN": "Anglais",

    # =========================================================================
    # Home page
    # =========================================================================
    "HOME_WELCOME": "Bienvenue",
    "HOME_TOOLS_TITLE": "Outils",
    "HOME_TOOLS_EMPTY": "Aucun outil métier pour l’instant (site vide).",
    "HOME_SETTINGS_SHORTCUT": "⚙️ Ouvrir les réglages",

    # =========================================================================
    # Settings page
    # =========================================================================
    "SETTINGS_TITLE": "Réglages",
    "SETTINGS_SUBTITLE": "Paramètres utilisateur et paramètres par défaut.",
    "SETTINGS_SECTION_UI": "Interface",
    "SETTINGS_RESET": "Réinitialiser les paramètres par défaut",
    "SETTINGS_RESET_DONE": "Paramètres réinitialisés.",

    # =========================================================================
    # Exit page
    # =========================================================================
    "EXIT_TITLE": "Au revoir",
    "EXIT_TEXT": (
        "Vous pouvez fermer cet onglet.\n\n"
        "Note : Streamlit ne peut pas fermer automatiquement l’onglet du navigateur."
    ),
    "EXIT_CLOSE_TAB": "Vous pouvez fermer cet onglet.",
    "EXIT_CLOUD_NOTE": "Sur Streamlit Cloud, l’application continue de tourner côté serveur.",


    # =========================================================================
    # Tool placeholders (future)
    # =========================================================================
    "TOOL_PLACEHOLDER_TITLE": "Outil (placeholder)",
    "TOOL_PLACEHOLDER_DESC": "Page métier vide, à compléter plus tard.",

    "NAV_TOOLS_GROUP": "Outils",

    "TOOL_TEMPLATE_TITLE": "Outil template",
    "TOOL_TEMPLATE_DESC": "Page exemple standardisée (Inputs → Run → Results → Export) pour valider l’architecture.",

    "SECTION_INPUTS": "Entrées",
    "SECTION_RUN": "Exécution",
    "SECTION_RESULTS": "Résultats",
    "SECTION_EXPORT": "Export",

    # --- TMY analysis tool ---
    "TOOL_TMY_ANALYSIS_TITLE": "Analyse de fichier TMY",
    "TOOL_TMY_ANALYSIS_DESC": (
        "Analyse et génération d’un rapport à partir d’un fichier météo TMY "
        "(format PVSyst). Statistiques, qualité des données et irradiation annuelle."
    ),

    "TMY_UPLOAD_LABEL": "Fichier TMY (format PVSyst)",
    "TMY_TARGET_IRR_UNIT": "Unité cible d’irradiance",
    "TMY_ENERGY_UNIT": "Unité d’énergie",
    "TMY_RESAMPLE_1H": "Re-échantillonner les données infra-horaires en 1h",

    "TMY_RUN_ANALYSIS": "Lancer l’analyse",
    "TMY_RUNNING": "Analyse en cours…",
    "TMY_DONE": "Analyse terminée.",

    "TMY_SUMMARY": "Résumé",
    "TMY_ENERGY": "Irradiation annuelle",
    "TMY_STATS": "Statistiques de base",
    "TMY_WARNINGS": "Avertissements",
    "TMY_OUTPUTS": "Fichiers générés",

    "TMY_DOWNLOAD_PDF": "Télécharger le rapport PDF",
    "TMY_DOWNLOAD_LOG": "Télécharger le journal (log)",
    "TMY_NO_ENERGY": "Impossible de calculer l’irradiation annuelle.",
    
    "TMY_TIMESTAMP_OUTPUTS": "Ajouter un horodatage aux fichiers générés",
    "TMY_NO_OUTPUTS_YET": "Aucun fichier généré pour le moment.",

    "TMY_TIMESTAMP_OUTPUTS": "Ajouter un horodatage aux fichiers générés",
    "TMY_NO_OUTPUTS_YET": "Aucun résultat : clique sur Lancer l’analyse.",

    "TMY_CURVES_TITLE": "Courbes annuelles (interactives)",
    "TMY_DISTRIBUTIONS_TITLE": "Distributions (interactives)",

    "TMY_DATE": "Date",
    "TMY_COUNT": "Occurrences",
    "TMY_VAR": "Variable",
    "TMY_VALUE": "Valeur",
    "TMY_UNIT": "Unité",

    "TMY_TEMP_LABEL": "Température",
    "TMY_GHI_NOT_AVAILABLE": "GHI non disponible.",
    "TMY_TEMP_NOT_AVAILABLE": "Température non disponible.",

    "TMY_GHI_DISTRIB_LABEL": "GHI – histogramme (valeurs > 0, classes de 200)",
    "TMY_TEMP_DISTRIB_LABEL": "Température – histogramme",
    "TMY_GHI_DISTRIB_EMPTY": "Distribution GHI indisponible (pas de valeurs > 0).",
    "TMY_TEMP_DISTRIB_EMPTY": "Distribution température indisponible.",

    # Hourly results
  "TOOL_HOURLY_RESULTS_TITLE": "Analyse Hourly Results (PVSyst)",
  "TOOL_HOURLY_RESULTS_DESC": "Analyse un export horaire PVSyst et produit des synthèses + rapports (Excel/PDF).",

  "HOURLY_UPLOAD_LABEL": "Fichier PVSyst (Hourly results) — CSV/TXT",
  "HOURLY_TIMESTAMP_OUTPUTS": "Ajouter un timestamp aux exports (évite d’écraser les fichiers)",
  "HOURLY_THRESHOLD_COLUMN_LABEL": "Colonne analysée pour le seuil & la distribution",
  "HOURLY_THRESHOLD_COLUMN_HELP": "Par défaut: E_Grid. La valeur de seuil doit être dans la même unité que cette colonne.",
  "HOURLY_THRESHOLD_VALUE_LABEL": "Seuil (même unité que la colonne)",
  "HOURLY_THRESHOLD_VALUE_HELP": "Utilisé par l’étude « Seuil » et par « Distribution ».",

  "HOURLY_INPUTS_GUIDE_TITLE": "À quoi servent les paramètres ?",
  "HOURLY_INPUTS_GUIDE_THRESHOLD": "Seuil : calcule les heures et la somme au-dessus du seuil (mensuel/saisonnier + % mensuel).",
  "HOURLY_INPUTS_GUIDE_DISTRIBUTION": "Distribution : classe les heures de production par ratio (vs maximum annuel) sur la colonne analysée.",
  "HOURLY_INPUTS_GUIDE_CLIPPING": "Clipping onduleur : nécessite EOutInv et IL_Pmax (sinon l’étude est marquée indisponible).",

  "HOURLY_RUN": "Run",
  "HOURLY_RUNNING": "Analyse en cours…",
  "HOURLY_DONE": "Analyse terminée.",
  "HOURLY_FAILED": "Échec de l’analyse.",
  "HOURLY_NO_OUTPUTS_YET": "Aucun résultat pour le moment. Lance un run.",

  "HOURLY_SUMMARY": "Résumé",
  "HOURLY_SUMMARY_FILE": "Fichier",
  "HOURLY_SUMMARY_PVSYST_VERSION": "Version PVSyst",
  "HOURLY_SUMMARY_SIM_DATE": "Date de simulation",
  "HOURLY_SUMMARY_PERIOD": "Période couverte",
  "HOURLY_SUMMARY_ROWS": "Nombre de lignes",
  "HOURLY_SUMMARY_COLUMNS": "Colonnes disponibles",
  "HOURLY_SUMMARY_THRESHOLD": "Seuil",

  "HOURLY_TAB_GRAPHS": "Graphiques",
  "HOURLY_TAB_DISTRIBUTION": "Distribution & tableaux",

  "HOURLY_RESULTS_THRESHOLD": "Étude : Seuil",
  "HOURLY_RESULTS_DISTRIBUTION": "Étude : Distribution",
  "HOURLY_RESULTS_CLIPPING": "Étude : Clipping onduleur",

  "HOURLY_THRESHOLD_NOT_AVAILABLE": "L’étude Seuil est indisponible (colonne manquante).",
  "HOURLY_DISTRIBUTION_NOT_AVAILABLE": "L’étude Distribution est indisponible (colonne manquante).",
  "HOURLY_CLIPPING_NOT_AVAILABLE": "L’étude Clipping est indisponible (colonnes manquantes).",
  "HOURLY_CLIPPING_NOT_RUN": "Aucune donnée de clipping.",

  "HOURLY_EMPTY": "Pas de données exploitables.",
  "HOURLY_MISSING_COLUMNS": "Colonnes manquantes",
  "HOURLY_SUGGESTED_COLUMNS": "Colonnes proches (suggestions)",

  "HOURLY_THR_OPERATING_HOURS": "Heures de fonctionnement (>0)",
  "HOURLY_THR_HOURS_ABOVE": "Heures > seuil",
  "HOURLY_THR_SHARE_ABOVE": "% du temps de fonctionnement > seuil",
  "HOURLY_THR_SUM_ABOVE": "Somme > seuil",

  "HOURLY_CLIP_HOURS": "Heures de clipping",
  "HOURLY_CLIP_PCT": "% clipping (sur potentiel)",
  "HOURLY_CLIP_ENERGY": "Énergie clippée",

  "HOURLY_TABLE_THRESHOLD_MONTHLY": "Seuil — Mensuel",
  "HOURLY_TABLE_THRESHOLD_SEASONAL": "Seuil — Saisonnier",
  "HOURLY_COL_MONTH": "Mois",
  "HOURLY_COL_SEASON": "Saison",
  "HOURLY_COL_HOURS_ABOVE": "Heures > seuil",
  "HOURLY_COL_SUM_ABOVE": "Somme > seuil",
  "HOURLY_COL_CLASS": "Classe",
  "HOURLY_COL_PCT_TIME": "% du temps",
  "HOURLY_COL_SUM": "Somme",

  "HOURLY_CHART_MONTHLY_HOURS": "Heures > seuil — mensuel",
  "HOURLY_CHART_MONTHLY_SHARE": "% du temps > seuil — mensuel",
  "HOURLY_CHART_CLIPPING_MONTHLY": "% clipping — mensuel",
  "HOURLY_Y_HOURS": "Heures",
  "HOURLY_Y_PERCENT": "%",

  "HOURLY_GENERATE_EXCEL": "Générer Excel",
  "HOURLY_GENERATE_PDF": "Générer PDF",
  "HOURLY_GENERATE_LOG": "Générer log",
  "HOURLY_EXCEL_READY": "Excel prêt.",
  "HOURLY_PDF_READY": "PDF prêt.",
  "HOURLY_LOG_READY": "Log prêt.",
  "HOURLY_NO_EXPORTS_YET": "Aucun export généré pour le moment.",

  "HOURLY_DOWNLOAD_EXCEL": "Télécharger Excel",
  "HOURLY_DOWNLOAD_PDF": "Télécharger PDF",
  "HOURLY_DOWNLOAD_LOG": "Télécharger log",

  "HOURLY_Y_HOURS": "Heures",
  "HOURLY_Y_PERCENT": "%",

  "HOURLY_INPUTS_GUIDE_NIGHT": "Déconnexion nocturne : ignore les valeurs négatives (soutirage) dans Seuil/Distribution, tout en calculant le soutirage nocturne.",
  "HOURLY_NIGHT_DISCONNECT_LABEL": "Déconnexion nocturne (ignorer le soutirage négatif pour les études Seuil/Distribution)",
  "HOURLY_NIGHT_DISCONNECT_HELP": "Si activé, les valeurs négatives de la colonne analysée sont ramenées à 0 pour le calcul du temps de fonctionnement, du seuil et de la distribution. Le soutirage nocturne est calculé séparément à partir des valeurs négatives brutes.",
  "HOURLY_SUMMARY_NIGHT_OPTION": "Option nocturne",
  "HOURLY_NIGHT_DISCONNECT_ON": "Déconnexion nocturne activée",
  "HOURLY_NIGHT_DISCONNECT_OFF": "Déconnexion nocturne désactivée",

  "HOURLY_RESULTS_NIGHT": "Soutirage nocturne",
  "HOURLY_NIGHT_CONSUMPTION": "Soutirage nocturne",
  "HOURLY_NIGHT_HOURS": "Heures de soutirage",

  "HOURLY_CHART_NIGHT_IMPORT": "Soutirage nocturne — mensuel",

  "HOURLY_GLOBAL_PRODUCTION_TITLE": "Production globale",
  "HOURLY_GLOBAL_PROJECT": "Projet",
  "HOURLY_GLOBAL_PROJECT_FILE": "Fichier projet",
  "HOURLY_GLOBAL_VARIANT": "Variante",
  "HOURLY_GLOBAL_TIMESTEP": "Pas de temps détecté",
  "HOURLY_GLOBAL_OPERATING_HOURS": "Heures de fonctionnement",
  "HOURLY_GLOBAL_NET_PRODUCTION": "Production nette (avec soutirage)",
  "HOURLY_GLOBAL_PRODUCTION_NO_IMPORT": "Production sans soutirage (valeurs négatives à 0)",
  "HOURLY_GLOBAL_NIGHT_CONSUMPTION": "Soutirage nocturne (auxiliaires)",
  "HOURLY_GLOBAL_IMPORT_HOURS": "Heures de soutirage",

  "HOURLY_GLOBAL_PRODUCTION_TITLE": "Production globale",
  "HOURLY_GLOBAL_NOT_AVAILABLE": "Synthèse globale indisponible (colonne manquante).",
  "HOURLY_GLOBAL_TIMESTEP_QUALITY": "Qualité du pas de temps",

  "HOURLY_GLOBAL_NET_PRODUCTION": "Production nette (avec soutirage)",
  "HOURLY_GLOBAL_PRODUCTION_NO_IMPORT": "Production sans soutirage (valeurs négatives à 0)",
  "HOURLY_GLOBAL_NIGHT_CONSUMPTION": "Soutirage nocturne (auxiliaires)",
  "HOURLY_GLOBAL_IMPORT_HOURS": "Heures de soutirage",

  "HOURLY_CHART_MONTHLY_ENERGY_ABOVE": "Énergie > seuil — mensuel",
  "HOURLY_Y_ENERGY_KWH": "Énergie (kWh)",

  "HOURLY_COL_ENERGY_ABOVE_KWH": "Énergie > seuil (kWh)",
  "HOURLY_COL_HOURS": "Heures",
  "HOURLY_COL_ENERGY_KWH": "Énergie (kWh)",

  "HOURLY_THR_ENERGY_ABOVE": "Énergie > seuil",

  "HOURLY_INPUTS_GUIDE_GRID_CAPACITY": "Capacité réseau (optionnel) : permet de calculer un facteur de charge annuel/mensuel lorsque disponible.",

  "HOURLY_GRID_CAPACITY_LABEL": "Capacité réseau (kW) — optionnel",
  "HOURLY_GRID_CAPACITY_HELP": "Puissance de raccordement / capacité d’injection (kW). Laisse vide si inconnue.",
  "HOURLY_GRID_CAPACITY_PLACEHOLDER": "ex: 3000",

  "HOURLY_GLOBAL_GRID_CAPACITY": "Capacité réseau",
  "HOURLY_GLOBAL_GRID_CAPACITY_NONE": "Non renseignée",
  "HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR": "Facteur de charge annuel (réseau)",
  "HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR_NONE": "Non calculé (capacité non renseignée)",

  "HOURLY_RESULTS_GRID_LIMIT": "Étude : Limitation réseau",
  "HOURLY_GRID_LIMIT_NOT_AVAILABLE": "Étude Limitation réseau indisponible (colonnes manquantes).",
  "HOURLY_CHART_GRID_LIMIT_LOST_KWH": "Limitation réseau — énergie perdue (mensuel)",
  "HOURLY_CHART_GRID_LIMIT_LOST_PCT": "Limitation réseau — % de perte (mensuel)",
  "HOURLY_GRID_LOST_ENERGY": "Énergie perdue",
  "HOURLY_GRID_LOST_PCT": "% de perte",
  "HOURLY_GRID_HOURS_LIMITED": "Heures limitées",
  "HOURLY_GRID_INJECTED": "Énergie injectée",
  "HOURLY_GRID_ANNUAL_LF": "Facteur de charge annuel",
  "HOURLY_GRID_ANNUAL_LF_NONE": "Non calculé (capacité non renseignée)",
  "HOURLY_TABLE_GRID_LIMIT_MONTHLY": "Limitation réseau — mensuel",

  "HOURLY_RESULTS_LOAD_FACTOR": "Étude : Charge & qualité réseau",
  "HOURLY_LOAD_FACTOR_NOT_AVAILABLE": "Étude Charge & qualité réseau indisponible (colonnes manquantes).",
  "HOURLY_CHART_COSPHI_MONTHLY": "cos(phi) — mensuel",
  "HOURLY_CHART_SATURATION_DIST": "Saturation apparente — distribution",
  "HOURLY_Y_COSPHI": "cos(phi)",

  "HOURLY_LF_COSPHI": "cos(phi) (annuel)",
  "HOURLY_LF_Q_SHARE": "Part réactive (annuel)",
  "HOURLY_LF_ANNUAL_LF": "Facteur de charge annuel",
  "HOURLY_LF_ANNUAL_LF_NONE": "Non calculé (capacité non renseignée)",
  "HOURLY_LF_NOT_AVAILABLE": "N/A",

  "HOURLY_TABLE_LOAD_FACTOR_MONTHLY": "Charge & qualité réseau — mensuel",
  "HOURLY_TABLE_SATURATION_DIST": "Saturation apparente — distribution",

  "HOURLY_LF_S_APPARENT": "Apparente (équiv. kWh)",
  "HOURLY_LF_Q_REACTIVE": "Réactive (équiv. kWh)",
  "HOURLY_LF_P_ACTIVE": "Active (kWh)",

  "HOURLY_HELP_BUTTON": "❓ Aide",
  "HOURLY_HELP_LOAD_FACTOR_MD": (
    "**Charge & qualité réseau**\n\n"
    "- **cos(φ) (annuel)** ≈ *P / S* : énergie active injectée (kWh) divisée par l’énergie apparente (kVAh équivalent).\n"
    "- **Part réactive (annuel)** ≈ *Q / S* : énergie réactive (kvarh équivalent) rapportée à l’apparente.\n"
    "- **Facteur de charge annuel** (si capacité renseignée) : *P / (Capacité × Heures totales)*.\n\n"
    "⚠️ Les calculs sont des indicateurs énergétiques (agrégés sur l’année / par mois) et dépendent des paramètres exportés par PVSyst."
  ),
  "HOURLY_HELP_GRID_LIMIT_MD": (
    "**Limitation réseau**\n\n"
    "- **Énergie perdue** : intégrale de **EGrdLim** (kWh).\n"
    "- **% de perte** : Énergie perdue / (Énergie injectée + Énergie perdue).\n"
    "- **Heures limitées** : nombre de pas où **EGrdLim > 0** (converti en heures avec le pas de temps).\n"
    "- Si une **capacité réseau** est renseignée, un **facteur de charge** peut être calculé."
  ),
  "HOURLY_HELP_THRESHOLD_MD": (
    "**Seuil**\n\n"
    "- Calcule le temps et l’énergie **au-dessus d’un seuil** sur la colonne choisie (ex: E_Grid).\n"
    "- Résultats : heures > seuil, énergie > seuil, % du temps de fonctionnement, et répartition mensuelle/saisonnière.\n"
    "- **Déconnexion nocturne** (si activée) : les valeurs négatives sont ignorées pour le fonctionnement et le seuil."
  ),

  "HOURLY_HELP_GRID_LIMIT_MD": (
    "**Étude : Limitation réseau**\n\n"
    "Cette étude quantifie l’impact de la limitation d’injection au point de raccordement.\n\n"
    "**Indicateurs affichés**\n\n"
    "- **Énergie perdue (kWh)** : énergie qui **aurait pu être injectée** mais ne l’a pas été à cause d’une limitation réseau "
    "(issue du paramètre PVSyst **EGrdLim**). Plus cette valeur est élevée, plus la contrainte réseau réduit la production injectée.\n\n"
    "- **% de perte** : part de l’énergie perdue par rapport à l’énergie **potentielle** au réseau :\n"
    "  `perte % = Énergie perdue / (Énergie injectée + Énergie perdue)`\n"
    "  → utile pour comparer plusieurs variantes (même si la production totale change).\n\n"
    "- **Heures limitées** : durée (en heures) pendant laquelle une limitation a été active.\n"
    "  Calcul : nombre de pas où **EGrdLim > 0**, converti en heures via le pas de temps détecté.\n"
    "  → indique si la limitation est **fréquente** (beaucoup d’heures) ou **ponctuelle** (peu d’heures).\n\n"
    "- **Facteur de charge annuel** : calculé uniquement si la **capacité réseau (kW)** est renseignée.\n"
    "  Formule : `LF = Énergie injectée (kWh) / (Capacité (kW) × Heures totales (h))`\n"
    "  → représente l’utilisation moyenne annuelle de la capacité de raccordement.\n\n"
    "**Comment interpréter l’exemple**\n\n"
    "- `931 524 kWh` perdus et `3.53 %` : la limitation existe mais reste modérée en proportion.\n"
    "- `586 h` : la limitation est présente sur une quantité non négligeable d’heures.\n"
    "- `17.12 %` : en moyenne annuelle, l’injection active équivaut à ~17% de la capacité de raccordement.\n\n"
    "⚠️ Les résultats dépendent des paramètres exportés par PVSyst et du pas de temps détecté."
  ),

    "TOOL_TMY_COMPARE_TITLE": "Comparaison de TMY",
    "TOOL_TMY_COMPARE_DESC": "Comparer deux fichiers TMY (GHI/DNI/DHI/Temp) sur un pas horaire commun (60 min) et analyser les écarts.",

    "TMY_COMPARE_UPLOAD_A": "Fichier TMY A",
    "TMY_COMPARE_UPLOAD_B": "Fichier TMY B",

    "TMY_COMPARE_TARGET_IRR_UNIT": "Unité d'irradiance cible",
    "TMY_COMPARE_ENERGY_UNIT": "Unité d'énergie (intégration)",
    "TMY_COMPARE_RESAMPLE_1H": "Ré-échantillonner à 1h si sub-horaire",
    "TMY_COMPARE_THRESHOLD_MEAN_PCT": "Seuil d'alerte (écart moyen en %)",

    "TMY_COMPARE_RUN": "Run",
    "TMY_COMPARE_RUNNING": "Comparaison en cours…",
    "TMY_COMPARE_DONE": "Comparaison terminée.",
    "TMY_COMPARE_NEED_TWO_FILES": "Veuillez sélectionner deux fichiers TMY (A et B).",

    "TMY_COMPARE_SUMMARY": "Résumé",
    "TMY_COMPARE_ENERGY_FULL": "Irradiation annuelle (fichiers complets)",
    "TMY_COMPARE_METRICS": "Métriques (période commune, alignée horaire)",
    "TMY_COMPARE_NO_COMMON_VARS": "Aucune variable commune trouvée (GHI/DNI/DHI/Temp...).",

    "TMY_COMPARE_PLOTS": "Graphiques",
    "TMY_COMPARE_NO_PLOTS": "Aucun graphique disponible (variables manquantes).",
    "TMY_COMPARE_VAR_BLOCK": "Variable : {var}",
    "TMY_COMPARE_DELTA": "Delta (A − B)",

    "TMY_COMPARE_FILE": "Fichier",
    "TMY_COMPARE_DOWNLOAD_PDF": "Télécharger le PDF (rapport de comparaison)",
    "TMY_COMPARE_NO_OUTPUTS_YET": "Aucun résultat pour l'instant. Lance une comparaison pour générer un rapport.",

    "TMY_COMPARE_VAR_GHI": "Irradiance globale horizontale (GHI)",
    "TMY_COMPARE_VAR_DNI": "Irradiance directe normale (DNI)",
    "TMY_COMPARE_VAR_DHI": "Irradiance diffuse horizontale (DHI)",
    "TMY_COMPARE_VAR_TEMP": "Température ambiante",
    "TMY_COMPARE_VAR_WIND": "Vitesse du vent",

    "TMY_COMPARE_COL_VARIABLE": "Variable",
    "TMY_COMPARE_COL_N": "Nb points",
    "TMY_COMPARE_COL_MEAN_A": "Moyenne (A)",
    "TMY_COMPARE_COL_MEAN_B": "Moyenne (B)",
    "TMY_COMPARE_COL_BIAS": "Biais moyen (A − B)",
    "TMY_COMPARE_COL_MAE": "Erreur absolue moyenne (MAE)",
    "TMY_COMPARE_COL_RMSE": "Erreur quadratique moyenne (RMSE)",
    "TMY_COMPARE_COL_MEAN_PCT": "Écart relatif moyen (%)",
    "TMY_COMPARE_COL_MAX_PCT": "Écart relatif max (%)",
    "TMY_COMPARE_COL_MAX_ABS": "Écart absolu max",

    "TMY_COMPARE_STEP_NATIVE_A": "Pas de temps natif (A)",
    "TMY_COMPARE_STEP_NATIVE_B": "Pas de temps natif (B)",
    "TMY_COMPARE_STEP_USED": "Pas de temps utilisé pour la comparaison",
    "TMY_COMPARE_ALERT": "Alertes",
}
