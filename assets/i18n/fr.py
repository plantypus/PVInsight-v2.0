# assets/i18n/fr.py

TEXTS = {
    # =========================================================================
    # App (global)
    # =========================================================================
    "APP_PAGE_TITLE": "PVInsight",
    "APP_TITLE": "PVInsight — Analyse PVSyst",
    "APP_VERSION_LABEL": "Version",
    "APP_DESCRIPTION": (
        "Outil Streamlit d’analyse de production de centrales solaires (hourly results, bilans mensuels, PR, pertes, etc.)."
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
    "HOURLY_THRESHOLD_DISABLED_ZERO": "La limite etudiee est a 0: l'analyse complementaire n'est pas calculee.",
  "HOURLY_DISTRIBUTION_NOT_AVAILABLE": "L’étude Distribution est indisponible (colonne manquante).",
  "HOURLY_CLIPPING_NOT_AVAILABLE": "L’étude Clipping est indisponible (colonnes manquantes).",
  "HOURLY_CLIPPING_NOT_RUN": "Aucune donnée de clipping.",

  "HOURLY_EMPTY": "Pas de données exploitables.",
  "HOURLY_MISSING_COLUMNS": "Colonnes manquantes",
  "HOURLY_SUGGESTED_COLUMNS": "Colonnes proches (suggestions)",

  "HOURLY_THR_OPERATING_HOURS": "Heures de fonctionnement (>0)",
  "HOURLY_THR_HOURS_ABOVE": "Heures > seuil",
  "HOURLY_THR_SHARE_ABOVE": "Part perdue / production sans soutirage",
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

  "HOURLY_COL_ENERGY_ABOVE_KWH": "Énergie perdue (kWh)",
  "HOURLY_COL_HOURS": "Heures",
  "HOURLY_COL_ENERGY_KWH": "Énergie (kWh)",

  "HOURLY_THR_ENERGY_ABOVE": "Énergie perdue par limitation",

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

    "HOURLY_HEATMAP_TITLE": "Heatmap de l’injection réseau (mois × heure)",

    "HOURLY_HEATMAP_CAPTION": (
        "Valeur moyenne de la puissance injectée P_grid (kW), "
        "calculée à partir de l’énergie E_Grid et du pas de temps Δt."
    ),

    "HOURLY_HEATMAP_MISSING_COLUMN": "Colonne requise absente pour la heatmap",

    "HOURLY_HEATMAP_NOT_AVAILABLE": (
        "Heatmap indisponible : données manquantes ou index temporel invalide."
    ),
    
    "HOURLY_HEATMAP_COLORBAR_TITLE_P_GRID": "Puissance injectée (P_grid)",
    "HOURLY_HEATMAP_UNIT_KW": "kW",
# new keys i18n
    "HOURLY_TAB_MAIN_ANALYSIS": "Analyse principale",
    "HOURLY_TAB_DETAILED_ANALYSIS": "Analyses détaillées",

    "HOURLY_HELP_FILE_SUMMARY_MD": (
        "Cette section résume les informations principales du fichier horaire analysé : "
        "identité du projet, variante, version PVSyst, période couverte et qualité du pas de temps."
    ),
    "HOURLY_HELP_AVAILABLE_STUDIES_MD": (
        "Cette section indique quelles études sont disponibles selon les colonnes détectées dans le fichier "
        "et les analyses effectivement calculées."
    ),
    "HOURLY_HELP_GLOBAL_RESULTS_MD": (
        "Cette section présente la synthèse énergétique globale de la simulation : "
        "production, soutirage nocturne, heures de fonctionnement et, si possible, facteur de charge annuel."
    ),
    "HOURLY_HELP_CLIPPING_MD": (
        "Le clipping onduleur correspond à l'énergie perdue lorsque la puissance disponible côté DC "
        "dépasse la capacité de conversion/injection des onduleurs."
    ),
    "HOURLY_HELP_HEATMAP_MD": (
        "La heatmap montre la répartition moyenne de la production selon les mois et les heures de la journée. "
        "Elle aide à repérer les périodes de forte production."
    ),
    "HOURLY_HELP_POWER_DISTRIBUTION_MD": (
        "Cette table présente une répartition simplifiée de la production selon des classes relatives "
        "au maximum observé."
    ),

    "HOURLY_SUMMARY_COLUMNS_EXPANDER": "Afficher la liste des colonnes",

    "HOURLY_AVAILABLE_STUDIES_TITLE": "Études disponibles",

    "HOURLY_AVAIL_STUDY": "Étude",
    "HOURLY_AVAIL_STATUS": "Statut",
    "HOURLY_AVAIL_DETAIL": "Détail",

    "HOURLY_STATUS_AVAILABLE": "Disponible",
    "HOURLY_STATUS_PARTIAL": "Partielle",
    "HOURLY_STATUS_MISSING": "Non disponible",
    "HOURLY_STATUS_ESTIMABLE": "Estimable",

    "HOURLY_AVAIL_GLOBAL_RESULTS": "Résultats généraux",
    "HOURLY_AVAIL_GLOBAL_RESULTS_DETAIL": "Synthèse énergétique globale du fichier.",
    "HOURLY_AVAIL_CLIPPING": "Clipping onduleur",
    "HOURLY_AVAIL_CLIPPING_DETAIL": "Analyse des pertes IL_Pmax si les colonnes nécessaires sont présentes.",
    "HOURLY_AVAIL_HEATMAP": "Heatmap de production",
    "HOURLY_AVAIL_HEATMAP_DETAIL": "Visualisation de la production par mois et par heure.",
    "HOURLY_AVAIL_GRID_LIMIT_BASE": "Bridage déjà simulé",
    "HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_YES": "Le fichier contient EGrdLim : le bridage de base simulé peut être analysé.",
    "HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_NO": "Aucun bridage simulé détecté via EGrdLim.",
    "HOURLY_AVAIL_LIMIT_STUDY": "Étude de limitation complémentaire",
    "HOURLY_AVAIL_LIMIT_STUDY_DETAIL": "Analyse d'un seuil utilisateur à partir de la colonne de production choisie.",
    "HOURLY_AVAIL_LOAD_FACTOR": "Analyse active / réactive réseau",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_AVAILABLE": "Les colonnes apparente et réactive sont disponibles dans le fichier.",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_ESTIMABLE": "La simulation dédiée n'est pas présente, mais une estimation pourra être envisagée.",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_MISSING": "Les colonnes nécessaires ne sont pas disponibles dans le fichier.",

    "HOURLY_SECTION_CLIPPING_TITLE": "Clipping onduleur",
    "HOURLY_CLIPPING_NOT_AVAILABLE": "Analyse du clipping onduleur non disponible.",
    "HOURLY_CLIP_ENERGY": "Énergie perdue par clipping",
    "HOURLY_CLIP_PCT": "Part du clipping",
    "HOURLY_CLIP_HOURS": "Pas/occurrences de clipping",
    "HOURLY_CLIP_MAX_VALUE": "Valeur maximale de clipping",
    "HOURLY_CHART_CLIPPING_MONTHLY": "Pertes mensuelles par clipping onduleur",

    "HOURLY_SECTION_LIMIT_STUDY_TITLE": "Étude seuil / bridage",
    "HOURLY_LIMIT_CURRENT_STATE_TITLE": "État actuel de la simulation",
    "HOURLY_LIMIT_COMPLEMENTARY_STUDY_TITLE": "Étude complémentaire de limitation",
    "HOURLY_LIMIT_METHOD": "Méthode",
    "HOURLY_LIMIT_METHOD_MEASURED": "Mesurée dans le fichier",
    "HOURLY_LIMIT_METHOD_ESTIMATED": "Estimée à partir de la capacité renseignée",
    "HOURLY_LIMIT_DETECTED_COLUMN": "Colonne utilisee", 
    "HOURLY_CHART_DURATION_CURVE_THRESHOLD": "Courbe de durée avec seuil",
    "HOURLY_X_DURATION_RANK": "Rang",
    "HOURLY_Y_POWER_OR_ENERGY": "Valeur",

    "HOURLY_SECTION_LOAD_FACTOR_TITLE": "Analyse active / réactive réseau",
    "HOURLY_LOAD_FACTOR_ESTIMABLE": (
        "La simulation active / réactive détaillée n'est pas présente dans le fichier, "
        "mais un impact potentiel pourra être estimé dans une évolution ultérieure."
    ),

    "HOURLY_DETAILS_THRESHOLD_TITLE": "Détails de l'étude de seuil",
    "HOURLY_DETAILS_GRID_LIMIT_TITLE": "Détails du bridage réseau",
    "HOURLY_DETAILS_LOAD_FACTOR_TITLE": "Détails active / réactive réseau",
    "HOURLY_DETAILS_POWER_DISTRIBUTION_TITLE": "Distribution détaillée de puissance",

    "TOOL_HOURLY_RESULTS_TITLE": "Analyse des résultats horaires",
    "TOOL_HOURLY_RESULTS_DESC": "Analyse un fichier horaire PVSyst pour synthétiser la production, le clipping, le bridage réseau et les indicateurs électriques.",

    "SECTION_INPUTS": "Entrées",
    "SECTION_RUN": "Exécution",
    "SECTION_RESULTS": "Résultats",
    "SECTION_EXPORT": "Exports",

    "HOURLY_INPUTS_GUIDE_TITLE": "Guide des paramètres",
    "HOURLY_INPUTS_GUIDE_LIMIT_VALUE": "Définir la colonne analysée et la valeur limite étudiée pour l'analyse complémentaire.",
    "HOURLY_INPUTS_GUIDE_GRID_CAPACITY_REVISED": "Renseigner éventuellement une capacité réseau pour estimer un bridage si le fichier ne contient pas EGrdLim.",
    "HOURLY_INPUTS_GUIDE_CLIPPING": "Le clipping onduleur est analysé automatiquement si les colonnes nécessaires sont présentes.",
    "HOURLY_INPUTS_GUIDE_NIGHT": "L'option de déconnexion nocturne ignore les valeurs négatives dans certaines analyses complémentaires.",
    "HOURLY_INPUTS_GUIDE_LOAD_FACTOR": "L'analyse active / réactive dépend des colonnes disponibles dans le fichier.",

    "HOURLY_UPLOAD_LABEL": "Fichier horaire PVSyst (.csv, .txt)",
    "HOURLY_TIMESTAMP_OUTPUTS": "Ajouter un horodatage aux fichiers exportés",

    "HOURLY_LIMIT_COLUMN_LABEL": "Colonne utilisée pour l'étude de limitation",
    "HOURLY_LIMIT_COLUMN_HELP": "Colonne utilisée pour l'étude complémentaire de limitation. Par défaut : E_Grid.",
    "HOURLY_LIMIT_VALUE_LABEL": "Valeur / puissance limite étudiée",
    "HOURLY_LIMIT_VALUE_HELP": "Valeur utilisée pour analyser la part de production au-dessus d'une limite choisie.",

    "HOURLY_NIGHT_DISCONNECT_LABEL": "Activer la déconnexion nocturne",
    "HOURLY_NIGHT_DISCONNECT_HELP": "Si activé, les valeurs négatives sont ignorées dans certaines analyses de limitation et de distribution. Le soutirage nocturne reste calculé séparément.",

    "HOURLY_GRID_CAPACITY_LABEL_REVISED": "Capacité réseau (optionnelle)",
    "HOURLY_GRID_CAPACITY_HELP_REVISED": "Capacité réseau utilisée pour estimer un bridage si le fichier ne contient pas déjà EGrdLim.",

    "HOURLY_RUN": "Lancer l'analyse",
    "HOURLY_RUNNING": "Analyse en cours…",
    "HOURLY_DONE": "Analyse terminée.",
    "HOURLY_FAILED": "Échec de l'analyse.",
    "HOURLY_NO_OUTPUTS_YET": "Aucun résultat disponible pour le moment.",

    "HOURLY_TAB_MAIN_ANALYSIS": "Analyse principale",
    "HOURLY_TAB_DETAILED_ANALYSIS": "Analyses détaillées",

    "HOURLY_SUMMARY": "Résumé simulation",
    "HOURLY_HELP_FILE_SUMMARY_MD": "Cette section résume les informations principales du fichier horaire analysé : projet, variante, version PVSyst, période couverte et qualité du pas de temps.",
    "HOURLY_SUMMARY_FILE": "Fichier",
    "HOURLY_SUMMARY_PVSYST_VERSION": "Version PVSyst",
    "HOURLY_SUMMARY_SIM_DATE": "Date de simulation",
    "HOURLY_SUMMARY_PERIOD": "Période",
    "HOURLY_SUMMARY_ROWS": "Nombre de lignes",
    "HOURLY_SUMMARY_COLUMNS": "Colonnes",
    "HOURLY_SUMMARY_COLUMNS_EXPANDER": "Afficher la liste des colonnes",
    "HOURLY_SUMMARY_NIGHT_OPTION": "Option nuit",

    "HOURLY_GLOBAL_PROJECT": "Projet",
    "HOURLY_GLOBAL_PROJECT_FILE": "Fichier projet",
    "HOURLY_GLOBAL_VARIANT": "Variante",
    "HOURLY_GLOBAL_TIMESTEP": "Pas de temps",
    "HOURLY_GLOBAL_TIMESTEP_QUALITY": "Qualité du pas de temps",
    "HOURLY_NIGHT_DISCONNECT_ON": "Déconnexion nocturne activée",
    "HOURLY_NIGHT_DISCONNECT_OFF": "Déconnexion nocturne désactivée",

    "HOURLY_AVAILABLE_STUDIES_TITLE": "Études disponibles",
    "HOURLY_HELP_AVAILABLE_STUDIES_MD": "Cette section indique quelles études sont disponibles selon les colonnes détectées dans le fichier et les analyses effectivement calculées.",
    "HOURLY_AVAIL_STUDY": "Étude",
    "HOURLY_AVAIL_STATUS": "Statut",
    "HOURLY_AVAIL_DETAIL": "Détail",
    "HOURLY_STATUS_AVAILABLE": "Disponible",
    "HOURLY_STATUS_PARTIAL": "Partielle",
    "HOURLY_STATUS_MISSING": "Non disponible",
    "HOURLY_STATUS_ESTIMABLE": "Estimable",

    "HOURLY_AVAIL_GLOBAL_RESULTS": "Résultats généraux",
    "HOURLY_AVAIL_GLOBAL_RESULTS_DETAIL": "Synthèse énergétique globale du fichier.",
    "HOURLY_AVAIL_CLIPPING": "Clipping onduleur",
    "HOURLY_AVAIL_CLIPPING_DETAIL": "Analyse des pertes IL_Pmax si les colonnes nécessaires sont présentes.",
    "HOURLY_AVAIL_HEATMAP": "Heatmap de production",
    "HOURLY_AVAIL_HEATMAP_DETAIL": "Visualisation de la production par mois et par heure.",
    "HOURLY_AVAIL_GRID_LIMIT_BASE": "Bridage déjà simulé",
    "HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_YES": "Le fichier contient EGrdLim : le bridage simulé peut être analysé.",
    "HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_NO": "Aucun bridage simulé détecté via EGrdLim.",
    "HOURLY_AVAIL_LIMIT_STUDY": "Étude de limitation complémentaire",
    "HOURLY_AVAIL_LIMIT_STUDY_DETAIL": "Analyse d'une limite utilisateur à partir de la colonne choisie.",
    "HOURLY_AVAIL_LOAD_FACTOR": "Analyse active / réactive réseau",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_AVAILABLE": "Les colonnes apparente et réactive sont disponibles dans le fichier.",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_ESTIMABLE": "La simulation dédiée n'est pas présente, mais une estimation pourra être envisagée.",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_MISSING": "Les colonnes nécessaires ne sont pas disponibles dans le fichier.",

    "HOURLY_GLOBAL_PRODUCTION_TITLE": "Résultats généraux",
    "HOURLY_HELP_GLOBAL_RESULTS_MD": "Cette section présente la synthèse énergétique globale de la simulation : production, soutirage nocturne, heures de fonctionnement et facteur de charge annuel si disponible.",
    "HOURLY_GLOBAL_NOT_AVAILABLE": "Résultats généraux non disponibles.",
    "HOURLY_MISSING_COLUMNS": "Colonnes manquantes",
    "HOURLY_SUGGESTED_COLUMNS": "Colonnes suggérées",

    "HOURLY_GLOBAL_PRODUCTION_NO_IMPORT": "Production sans soutirage",
    "HOURLY_GLOBAL_NET_PRODUCTION": "Production nette",
    "HOURLY_GLOBAL_NIGHT_CONSUMPTION": "Soutirage nocturne",
    "HOURLY_GLOBAL_OPERATING_HOURS": "Heures de fonctionnement",
    "HOURLY_GLOBAL_IMPORT_HOURS": "Heures de soutirage",
    "HOURLY_GLOBAL_GRID_CAPACITY": "Capacité réseau",
    "HOURLY_GLOBAL_GRID_CAPACITY_NONE": "Non renseignée",
    "HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR": "Facteur de charge annuel",
    "HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR_NONE": "Non disponible",

    "HOURLY_SECTION_CLIPPING_TITLE": "Clipping onduleur",
    "HOURLY_HELP_CLIPPING_MD": "Le clipping onduleur correspond à l'énergie perdue lorsque la puissance disponible dépasse la capacité de conversion côté onduleur. Le pourcentage affiché est calculé par rapport à l'énergie potentielle onduleur avant clipping.",
    "HOURLY_CLIPPING_NOT_AVAILABLE": "Analyse du clipping onduleur non disponible.",
    "HOURLY_EMPTY": "Aucune donnée exploitable.",
    "HOURLY_CLIP_ENERGY": "Énergie perdue par clipping",
    "HOURLY_CLIP_PCT": "Part du clipping",
    "HOURLY_CLIP_REFERENCE": "Référence du pourcentage",
    "HOURLY_CLIP_HOURS": "Durée de clipping",
    "HOURLY_CLIP_MAX_VALUE": "Valeur maximale de clipping",
    "HOURLY_CLIP_REFERENCE_POTENTIAL_AC": "Par rapport à l'énergie potentielle onduleur avant clipping",

    "HOURLY_HEATMAP_TITLE": "Heatmap de production",
    "HOURLY_HELP_HEATMAP_MD": "La heatmap montre la répartition moyenne de la puissance selon les mois et les heures de la journée. Elle est affichée en MW.",
    "HOURLY_HEATMAP_MISSING_COLUMN": "Colonne manquante pour la heatmap",
    "HOURLY_HEATMAP_NOT_AVAILABLE": "Heatmap non disponible.",
    "HOURLY_HEATMAP_CAPTION_MW": "Heatmap de la puissance moyenne en MW par mois et par heure.",

    "HOURLY_SECTION_LIMIT_STUDY_TITLE": "Étude limite / bridage",
    "HOURLY_HELP_GRID_LIMIT_MD": "Cette section distingue le bridage déjà présent dans la simulation et l'étude complémentaire d'une limite utilisateur.",
    "HOURLY_LIMIT_CURRENT_STATE_TITLE": "État actuel de la simulation",
    "HOURLY_LIMIT_METHOD": "Méthode",
    "HOURLY_LIMIT_METHOD_MEASURED": "Mesurée dans le fichier",
    "HOURLY_LIMIT_METHOD_ESTIMATED": "Estimée à partir de la capacité renseignée",
    "HOURLY_LIMIT_DETECTED_COLUMN": "Colonne utilisee",
    "HOURLY_GRID_LOST_ENERGY": "Énergie perdue par bridage",
    "HOURLY_GRID_LOST_PCT": "Part perdue",
    "HOURLY_GRID_HOURS_LIMITED": "Durée bridée",
    "HOURLY_GRID_INJECTED": "Énergie injectée",
    "HOURLY_GRID_LIMIT_NOT_AVAILABLE": "Analyse de bridage réseau non disponible.",

    "HOURLY_LIMIT_COMPLEMENTARY_STUDY_TITLE": "Étude complémentaire de limitation",
    "HOURLY_THR_HOURS_ABOVE": "Durée au-dessus de la limite",
    "HOURLY_THR_SHARE_ABOVE": "Part perdue / production sans soutirage",
    "HOURLY_THR_ENERGY_ABOVE": "Énergie perdue par limitation",
    "HOURLY_THRESHOLD_NOT_AVAILABLE": "Étude de limitation non disponible.",
    "HOURLY_THRESHOLD_DISABLED_ZERO": "La limite etudiee est a 0: l'analyse complementaire n'est pas calculee.",
    "HOURLY_SECTION_LOAD_FACTOR_TITLE": "Analyse active / réactive réseau",
    "HOURLY_HELP_LOAD_FACTOR_MD": "Cette section presente les grandeurs active, reactive et apparente avec un indicateur cos(phi) annuel. Elle inclut aussi une analyse complementaire de tan(phi)=0.25 a 0.35 pour estimer la perte d'energie active et la puissance active minimale a declarer en injection (MW) pour ne pas impacter la production.",
    "HOURLY_LF_P_ACTIVE": "Énergie active",
    "HOURLY_LF_Q_REACTIVE": "Énergie réactive",
    "HOURLY_LF_S_APPARENT": "Énergie apparente",
    "HOURLY_LF_COSPHI": "cos(phi)",
    "HOURLY_LF_Q_SHARE": "Part réactive",
    "HOURLY_LF_ACTIVE_LOSS_KWH": "Perte active théorique due au facteur de puissance",
    "HOURLY_LF_ACTIVE_LOSS_PCT": "Part de perte active théorique",
    "HOURLY_LF_REFERENCE_DECLARED_POWER": "Puissance active de reference",
    "HOURLY_LF_REFERENCE_SOURCE": "Source de la puissance de référence",
    "HOURLY_LF_REFERENCE_SOURCE_INPUT": "Capacité réseau renseignée",
    "HOURLY_LF_REFERENCE_SOURCE_PEAK": "Pic de puissance active observé",
    "HOURLY_LF_SCENARIOS_TITLE": "Scénarios tan(phi) 0.25 à 0.35",
    "HOURLY_LF_COL_CASE": "Cas",
    "HOURLY_LF_CASE_BEST": "Meilleur cas (tan(phi)=0.25)",
    "HOURLY_LF_CASE_WORST": "Pire cas (tan(phi)=0.35)",
    "HOURLY_LF_COL_TANPHI": "tan(phi)",
    "HOURLY_LF_COL_COSPHI": "cos(phi)",
    "HOURLY_LF_COL_ACTIVE_LIMIT_KW": "Limite active sous contrainte (MW)",
    "HOURLY_LF_COL_LOSS_KWH": "Énergie active perdue (kWh)",
    "HOURLY_LF_COL_LOSS_PCT": "Perte vs sans contrainte",
    "HOURLY_LF_COL_MIN_DECLARED_KVA": "Puissance active minimale a declarer sans impact (MW)",
    "HOURLY_LOAD_FACTOR_ESTIMABLE": "La simulation active / réactive détaillée n'est pas présente dans le fichier, mais un impact potentiel pourra être estimé dans une évolution ultérieure.",
    "HOURLY_LOAD_FACTOR_NOT_AVAILABLE": "Analyse active / réactive non disponible.",

    "HOURLY_DETAILS_THRESHOLD_TITLE": "Détails de l'étude de limitation",
    "HOURLY_TABLE_THRESHOLD_MONTHLY": "Tableau mensuel de limitation",
    "HOURLY_COL_MONTH": "Mois",
    "HOURLY_COL_HOURS_ABOVE": "Heures au-dessus",
    "HOURLY_COL_ENERGY_ABOVE_KWH": "Énergie perdue (kWh)",
    "HOURLY_TABLE_THRESHOLD_SEASONAL": "Tableau saisonnier de limitation",
    "HOURLY_COL_SEASON": "Saison",

    "HOURLY_DETAILS_GRID_LIMIT_TITLE": "Détails du bridage réseau",
    "HOURLY_TABLE_GRID_LIMIT_MONTHLY": "Tableau mensuel du bridage réseau",

    "HOURLY_DETAILS_CLIPPING_TITLE": "Détails du clipping onduleur",

    "HOURLY_DETAILS_LOAD_FACTOR_TITLE": "Détails active / réactive réseau",
    "HOURLY_TABLE_LOAD_FACTOR_MONTHLY": "Tableau mensuel active / réactive",
    "HOURLY_TABLE_SATURATION_DIST": "Répartition de saturation",
    "HOURLY_COL_CLASS": "Classe",
    "HOURLY_COL_HOURS": "Heures",
    "HOURLY_COL_PCT_TIME": "Part du temps",

    "HOURLY_DETAILS_POWER_DISTRIBUTION_TITLE": "Distribution détaillée de puissance",
    "HOURLY_HELP_POWER_DISTRIBUTION_MD": "Cette table présente une répartition simplifiée de la production selon des classes relatives au maximum observé.",
    "HOURLY_DISTRIBUTION_NOT_AVAILABLE": "Distribution de puissance non disponible.",
    "HOURLY_COL_ENERGY_KWH": "Énergie (kWh)",

    "HOURLY_GENERATE_EXCEL": "Générer l'export Excel",
    "HOURLY_EXCEL_READY": "Export Excel prêt.",
    "HOURLY_GENERATE_PDF": "Générer l'export PDF",
    "HOURLY_PDF_READY": "Export PDF prêt.",
    "HOURLY_GENERATE_LOG": "Générer le log",
    "HOURLY_LOG_READY": "Log prêt.",
    "HOURLY_NO_EXPORTS_YET": "Aucun export généré pour le moment.",
    "HOURLY_DOWNLOAD_EXCEL": "Télécharger l'Excel",
    "HOURLY_DOWNLOAD_PDF": "Télécharger le PDF",
    "HOURLY_DOWNLOAD_LOG": "Télécharger le log",

    "HOURLY_SYSTEM_SUMMARY_TITLE": "Synthèse système",
    "HOURLY_HELP_SYSTEM_SUMMARY_MD": (
        "Cette synthèse résume la production annuelle hors soutirage nocturne, "
        "les pertes de clipping, le soutirage, le bridage éventuel, l'état global du système "
        "et une recommandation de bridage. "
        "Critères d'état système : très peu contraint < 1 %, faiblement contraint de 1 à < 3 %, "
        "modérément contraint de 3 à < 6 %, fortement contraint ≥ 6 % de pertes totales rapportées "
        "à la production sans soutirage nocturne. "
        "La recommandation de bridage s'appuie sur l'énergie perdue liée à la limite étudiée "
        "et sur le taux moyen de fonctionnement sur heures productives, calculé par rapport à la "
        "valeur maximale positive observée."
    ),
    "HOURLY_SYSTEM_SENTENCE_GENERAL": "La centrale produit **{prod_mwh}** MWh/an hors soutirage nocturne.",
    "HOURLY_SYSTEM_SENTENCE_CLIP_NIGHT": (
        "Les pertes de surpuissance sont de **{clip_mwh}** MWh/an, soit **{clip_pct}** de la production sans soutirage nocturne. "
        "L'énergie de soutirage nocturne est de **{night_mwh}** MWh/an, soit **{night_pct}** de la production sans soutirage nocturne."
    ),
    "HOURLY_SYSTEM_SENTENCE_GRID": (
        "Un bridage réseau est également présent dans la simulation, avec **{grid_mwh}** MWh/an perdus, "
        "soit **{grid_pct}** de la production sans soutirage nocturne."
    ),
    "HOURLY_SYSTEM_SENTENCE_STATE": "Globalement, la centrale présente un fonctionnement **{state}**.",
    "HOURLY_SYSTEM_STATE_VERY_LOW_CONSTRAINT": "très peu contraint",
    "HOURLY_SYSTEM_STATE_LOW_CONSTRAINT": "faiblement contraint",
    "HOURLY_SYSTEM_STATE_MODERATE_CONSTRAINT": "modérément contraint",
    "HOURLY_SYSTEM_STATE_HIGH_CONSTRAINT": "fortement contraint",
    "HOURLY_BRIDGING_RECOMMENDATION_FAVORABLE": (
        "Un bridage semble envisageable : la centrale fonctionne en moyenne à **{utilization_pct}** "
        "de sa valeur maximale observée sur ses heures productives, et la part d'énergie perdue "
        "reste limitée ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_CAUTION": (
        "Un bridage peut être envisagé avec prudence : la centrale fonctionne en moyenne à **{utilization_pct}** "
        "de sa valeur maximale observée sur ses heures productives, avec **{energy_above_pct}** d'énergie "
        "perdue liée à la limite étudiée."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_RECOMMENDED": (
        "Un bridage n'est pas particulièrement recommandé à ce niveau : la centrale fonctionne déjà à "
        "**{utilization_pct}** de sa valeur maximale observée sur ses heures productives ou la part d'énergie "
        "perdue devient significative ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_AVAILABLE": (
        "Aucune recommandation de bridage n'est disponible tant qu'une limite étudiée pertinente n'est pas définie."
    ),
    "HOURLY_CLIP_PCT_PRIMARY": "Part du clipping / production sans soutirage nocturne",
    "HOURLY_CLIP_REFERENCE_PRIMARY": "Référence principale",
    "HOURLY_CLIP_PCT_SECONDARY": "Part du clipping / énergie potentielle",
    "HOURLY_CLIP_REFERENCE_SECONDARY": "Référence secondaire",
    "HOURLY_CLIP_REFERENCE_PROD_WO_NIGHT": "Par rapport à la production sans soutirage nocturne",
    "HOURLY_CLIP_REFERENCE_POTENTIAL_AC": "Par rapport à l'énergie potentielle avant clipping",
    "HOURLY_UTILIZATION_REFERENCE_MAX_OBSERVED": "Valeur maximale positive observée",


    "HOURLY_AVAIL_PERFORMANCE": "Performance mensuelle",
    "HOURLY_AVAIL_PERFORMANCE_DETAIL": "Table mensuelle de performance avec irradiation, PR, productible et E_Grid.",

    "HOURLY_GLOBAL_PR": "PR bifacial annuel moyen",

    "HOURLY_SYSTEM_SUMMARY_TITLE": "Synthèse système",
    "HOURLY_HELP_SYSTEM_SUMMARY_MD": (
        "Cette synthèse résume la production annuelle hors soutirage nocturne, les pertes de clipping, "
        "le soutirage, le bridage éventuel, l'état global du système et une recommandation de bridage. "
        "Critères d'état système : très peu contraint < 1 %, faiblement contraint de 1 à < 3 %, "
        "modérément contraint de 3 à < 6 %, fortement contraint ≥ 6 % de pertes totales rapportées "
        "à la production sans soutirage nocturne. La recommandation de bridage s'appuie sur l'énergie "
        "perdue liée à la limite étudiée et sur le taux moyen de fonctionnement sur heures productives, "
        "calculé par rapport au percentile P99 des valeurs positives observées."
    ),
    "HOURLY_SYSTEM_SENTENCE_GENERAL": "La centrale produit **{prod_mwh}** MWh/an hors soutirage nocturne.",
    "HOURLY_SYSTEM_SENTENCE_CLIP_NIGHT": (
        "Les pertes de surpuissance sont de **{clip_mwh}** MWh/an, soit **{clip_pct}** de la production sans soutirage nocturne. "
        "L'énergie de soutirage nocturne est de **{night_mwh}** MWh/an, soit **{night_pct}** de la production sans soutirage nocturne."
    ),
    "HOURLY_SYSTEM_SENTENCE_GRID": (
        "Un bridage réseau est également présent dans la simulation, avec **{grid_mwh}** MWh/an perdus, "
        "soit **{grid_pct}** de la production sans soutirage nocturne."
    ),
    "HOURLY_SYSTEM_SENTENCE_METEO": (
        "Le site présente une ressource solaire **{meteo}** sur la période simulée. "
        "L'irradiation effective représente **{globeff_ratio}** de l'irradiation incidente, "
        "ce qui traduit des pertes optiques et/ou d'ombrage **{optics}**."
    ),
    "HOURLY_SYSTEM_SENTENCE_PERFORMANCE": (
        "Le PR bifacial annuel moyen est de **{pr}**. "
        "Le productible spécifique atteint **{productible}** kWh/kWc/an lorsque la donnée est disponible."
    ),
    "HOURLY_SYSTEM_SENTENCE_STATE": "Globalement, la centrale présente un fonctionnement **{state}**.",

    "HOURLY_SYSTEM_STATE_VERY_LOW_CONSTRAINT": "très peu contraint",
    "HOURLY_SYSTEM_STATE_LOW_CONSTRAINT": "faiblement contraint",
    "HOURLY_SYSTEM_STATE_MODERATE_CONSTRAINT": "modérément contraint",
    "HOURLY_SYSTEM_STATE_HIGH_CONSTRAINT": "fortement contraint",

    "HOURLY_METEO_MODEST": "modérée",
    "HOURLY_METEO_GOOD": "élevée",
    "HOURLY_METEO_VERY_GOOD": "très élevée",

    "HOURLY_OPTICS_LOW_LOSSES": "faibles",
    "HOURLY_OPTICS_MODERATE_LOSSES": "modérées",
    "HOURLY_OPTICS_MARKED_LOSSES": "marquées",

    "HOURLY_BRIDGING_RECOMMENDATION_FAVORABLE": (
        "Un bridage semble envisageable : la centrale fonctionne en moyenne à **{utilization_pct}** "
        "de son niveau de haut fonctionnement habituel (P99) sur ses heures productives, "
        "et la part d'énergie perdue reste limitée ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_CAUTION": (
        "Un bridage peut être envisagé avec prudence : la centrale fonctionne en moyenne à **{utilization_pct}** "
        "de son niveau de haut fonctionnement habituel (P99) sur ses heures productives, "
        "avec **{energy_above_pct}** d'énergie perdue liée à la limite étudiée."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_RECOMMENDED": (
        "Un bridage n'est pas particulièrement recommandé à ce niveau : la centrale fonctionne déjà à "
        "**{utilization_pct}** de son niveau de haut fonctionnement habituel (P99) sur ses heures productives "
        "ou la part d'énergie perdue devient significative ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_AVAILABLE": (
        "Aucune recommandation de bridage n'est disponible tant qu'une limite étudiée pertinente n'est pas définie."
    ),

    "HOURLY_CLIP_PCT_PRIMARY": "Part du clipping / production sans soutirage nocturne",
    "HOURLY_CLIP_REFERENCE_PRIMARY": "Référence principale",
    "HOURLY_CLIP_PCT_SECONDARY": "Part du clipping / énergie potentielle",
    "HOURLY_CLIP_REFERENCE_SECONDARY": "Référence secondaire",
    "HOURLY_CLIP_REFERENCE_PROD_WO_NIGHT": "Par rapport à la production sans soutirage nocturne",
    "HOURLY_CLIP_REFERENCE_POTENTIAL_AC": "Par rapport à l'énergie potentielle avant clipping",

    "HOURLY_PERFORMANCE_MONTHLY_TITLE": "Performance mensuelle",
    "HOURLY_HELP_PERFORMANCE_MONTHLY_MD": (
        "Cette table regroupe par mois l'irradiation incidente, l'irradiation effective, le ratio GlobEff/GlobInc, "
        "le PR, le productible spécifique si disponible, et E_Grid. La dernière ligne donne un résumé annuel."
    ),
    "HOURLY_DETAILS_PERFORMANCE_TITLE": "Détails de la performance mensuelle",

    "HOURLY_COL_GLOBINC": "GlobInc (kWh/m²)",
    "HOURLY_COL_GLOBEFF": "GlobEff (kWh/m²)",
    "HOURLY_COL_GLOBEFF_RATIO": "GlobEff / GlobInc",
    "HOURLY_COL_PR": "PR",
    "HOURLY_COL_PRODUCTIBLE": "Productible (kWh/kWc)",
    "HOURLY_COL_EGRID_MWH": "E_Grid (MWh)",

    "HOURLY_UTILIZATION_REFERENCE_P99": "Percentile P99 des valeurs positives",

    "HOURLY_COL_GLOBHOR": "GlobHor (kWh/m²)",
    "HOURLY_COL_TILT_GAIN": "Gain inclinaison",
    "HOURLY_HELP_PERFORMANCE_MONTHLY_MD": (
        "Cette table regroupe par mois l'irradiation horizontale (GlobHor), l'irradiation dans le plan des capteurs (GlobInc), "
        "l'irradiation effective (GlobEff), le gain lié à l'inclinaison (GlobInc / GlobHor), le ratio optique (GlobEff / GlobInc), "
        "le PR bifacial calculé sur les seules heures de production positive, le productible spécifique si disponible, et E_Grid. "
        "Le ratio GlobEff / GlobInc représente la part de l'irradiation sur le plan capteurs qui reste effectivement exploitable "
        "après IAM et ombrage."
    ),
    "HOURLY_SYSTEM_SENTENCE_PERFORMANCE_NO_PRODUCTIBLE": (
        "Le PR bifacial annuel moyen est de **{pr}**."
    ),
    "HOURLY_SYSTEM_SENTENCE_OPTICS": (
        "Le gain lié à l'inclinaison atteint **{tilt_gain}** entre le plan horizontal et le plan capteurs. "
        "L'efficacité optique restante après IAM et ombrage est de **{optical_efficiency}**."
    ),
    "HOURLY_SYSTEM_SENTENCE_UTILIZATION": (
        "Le taux moyen de fonctionnement sur heures productives est de **{utilization_pct}**, "
        "calculé par rapport à {ref_label}."
    ),
    "HOURLY_UTILIZATION_REFERENCE_P99": "le percentile P99 des puissances positives",
    "HOURLY_DCAC_RECOMMENDATION_RELEVANT": (
        "Une revue du ratio DC/AC paraît pertinente : les pertes de clipping restent très faibles et "
        "le niveau de fonctionnement de la centrale demeure modéré sur ses heures productives."
    ),
    "HOURLY_DCAC_RECOMMENDATION_POSSIBLE": (
        "Une revue du ratio DC/AC peut être envisagée : la centrale semble peu contrainte côté clipping "
        "et son niveau de fonctionnement reste relativement limité."
    ),
    "HOURLY_DCAC_RECOMMENDATION_NOT_PRIORITY": (
        "Une revue du ratio DC/AC ne paraît pas prioritaire à ce stade."
    ),
    "HOURLY_DCAC_RECOMMENDATION_NOT_AVAILABLE": (
        "Aucune conclusion spécifique sur le ratio DC/AC n'est disponible."
    ),

    "HOURLY_SYSTEM_SENTENCE_OPTICS_FULL": (
        "Le gain lié à l'inclinaison atteint **{tilt_gain}** entre le plan horizontal et le plan capteurs. "
        "L'efficacité optique restante après IAM et ombrage est de **{optical_efficiency}**."
    ),
    "HOURLY_SYSTEM_SENTENCE_OPTICS_ONLY": (
        "L'efficacité optique restante après IAM et ombrage est de **{optical_efficiency}**."
    ),
    "HOURLY_SYSTEM_SENTENCE_PERFORMANCE_WITH_PRODUCTIBLE": (
        "Le PR bifacial annuel moyen est de **{pr}**. "
        "Le productible spécifique atteint **{productible}** kWh/kWc/an."
    ),


    #TMY compare tool
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

  # --- Compare PAN vs Datasheet ---
  "COMPARE_PAN_DS_TITLE": "Comparaison .PAN vs Datasheet",
  "COMPARE_PAN_DS_DESC": "Compare les valeurs électriques STC et quelques caractéristiques mécaniques entre un fichier PVsyst (.PAN) et une datasheet constructeur (PDF).",

  "COMPARE_PAN_DS_INPUTS_HELP": "1) Choisis un fabricant (détermine le reader PDF). 2) Charge un fichier .PAN et une datasheet PDF. 3) Lance la comparaison.",

  "COMPARE_PAN_DS_MFR_SELECT": "Fabricant (datasheet)",
  "COMPARE_PAN_DS_MFR_HELP": "Le fabricant sélectionné détermine quel reader PDF sera utilisé côté module métier.",
  "COMPARE_PAN_DS_MFR_JINKO": "Jinko Solar",
  "COMPARE_PAN_DS_MFR_DMEGC": "DMEGC",
  "COMPARE_PAN_DS_MFR_ASTRONERGY": "Astronergy",
  "COMPARE_PAN_DS_MFR_DAS_SOLAR": "DAS Solar",
  "COMPARE_PAN_DS_MFR_CANADIAN_SOLAR": "Canadian Solar",

  "COMPARE_PAN_DS_UPLOAD_PAN": "Fichier PVsyst (.PAN)",
  "COMPARE_PAN_DS_UPLOAD_DS": "Datasheet constructeur (PDF)",

  "COMPARE_PAN_DS_CLEANUP_TMP": "Supprimer les fichiers temporaires",
  "COMPARE_PAN_DS_CLEANUP_TMP_HELP": "Si activé, le PDF écrit sur disque pour lecture pourra être supprimé après parsing (utile en mode “stateless”).",

  "COMPARE_PAN_DS_RUN": "Lancer la comparaison",
  "COMPARE_PAN_DS_RUNNING": "Comparaison en cours…",
  "COMPARE_PAN_DS_DONE": "Comparaison terminée.",
  "COMPARE_PAN_DS_ERROR": "Erreur pendant la comparaison.",
  "COMPARE_PAN_DS_NEED_FILES": "Veuillez fournir un fichier .PAN et une datasheet PDF.",

  "COMPARE_PAN_DS_WARNINGS_TITLE": "Avertissements",
  "COMPARE_PAN_DS_SUMMARY_TITLE": "Résumé",
  "COMPARE_PAN_DS_SUM_MANUFACTURER": "Fabricant (code)",
  "COMPARE_PAN_DS_SUM_PAN_MODEL": "Modèle (PAN)",
  "COMPARE_PAN_DS_SUM_DS_MODEL": "Modèle (datasheet)",
  "COMPARE_PAN_DS_SUM_PICK_MODE": "Sélection variante (mode)",
  "COMPARE_PAN_DS_SUM_FIELDS": "Nombre de champs",
  "COMPARE_PAN_DS_SUM_OK": "Champs OK",
  "COMPARE_PAN_DS_SUM_WARN": "Champs en écart",
  "COMPARE_PAN_DS_SUM_MISSING": "Champs manquants",

  "COMPARE_PAN_DS_TABLE_TITLE": "Détails de comparaison",
  "COMPARE_PAN_DS_NO_ROWS": "Aucune ligne de comparaison disponible.",
  "COMPARE_PAN_DS_NO_OUTPUTS_YET": "Aucun résultat pour le moment.",

  "COMPARE_PAN_DS_COL_LABEL": "Paramètre",
  "COMPARE_PAN_DS_COL_UNIT": "Unité",
  "COMPARE_PAN_DS_COL_PAN": "PAN",
  "COMPARE_PAN_DS_COL_DS": "Datasheet",
  "COMPARE_PAN_DS_COL_DABS": "Δ absolu",
  "COMPARE_PAN_DS_COL_DPCT": "Δ %",
  "COMPARE_PAN_DS_COL_STATUS": "Statut",
  "COMPARE_PAN_DS_COL_TOL_ABS": "Tolérance abs.",
  "COMPARE_PAN_DS_COL_TOL_PCT": "Tolérance %",

  # --- Compare PAN vs Datasheet (IAM + Exports + Generalities + Project) ---

  "COMPARE_PAN_DS_GENERALITIES_TITLE": "Généralités",
  "COMPARE_PAN_DS_GEN_DATE": "Date d’analyse",
  "COMPARE_PAN_DS_GEN_MFR": "Fabricant sélectionné",
  "COMPARE_PAN_DS_GEN_PAN_FILE": "Fichier PAN",
  "COMPARE_PAN_DS_GEN_DS_FILE": "Fichier datasheet",
  "COMPARE_PAN_DS_GEN_PAN_MODEL": "Modèle (PAN)",
  "COMPARE_PAN_DS_GEN_PAN_POWER": "Puissance (PAN, W)",
  "COMPARE_PAN_DS_GEN_DS_VARIANT": "Variante (datasheet)",
  "COMPARE_PAN_DS_GEN_DS_POWER": "Puissance (datasheet, W)",

  "COMPARE_PAN_DS_PROJECT_EXPANDER": "Informations projet (optionnel – pour le rapport PDF)",
  "COMPARE_PAN_DS_PROJECT_NAME": "Nom du projet",
  "COMPARE_PAN_DS_PROJECT_NO": "N° projet",
  "COMPARE_PAN_DS_SOLAR_ENGINEER": "Ingénieur solaire",

  "COMPARE_PAN_DS_GRAPHS_TITLE": "Graphiques",
  "COMPARE_PAN_DS_IAM_NOT_AVAILABLE": "Profil IAM non disponible dans le fichier PAN.",
  "COMPARE_PAN_DS_IAM_MODE": "Mode IAM",
  "COMPARE_PAN_DS_IAM_PROFILE": "Nom du profil",
  "COMPARE_PAN_DS_IAM_TYPE": "Type de profil",
  "COMPARE_PAN_DS_IAM_X": "Angle d’incidence (°)",
  "COMPARE_PAN_DS_IAM_Y": "Facteur IAM",
  "COMPARE_PAN_DS_IAM_LOSS": "Pertes IAM (%)",
  "COMPARE_PAN_DS_IAM_TABLE_TITLE": "Table du profil IAM",
  "COMPARE_PAN_DS_IAM_COL_ANGLE": "Angle (°)",
  "COMPARE_PAN_DS_IAM_COL_IAM": "IAM",
  "COMPARE_PAN_DS_IAM_COL_LOSS": "Pertes (%)",
  "COMPARE_PAN_DS_IAM_WARNINGS_TITLE": "Avertissements IAM",
  "COMPARE_PAN_DS_IAM_STATS_TITLE": "Indicateurs IAM",

  "COMPARE_PAN_DS_COMPARE_SKIPPED": "Comparaison désactivée : le modèle (marque / puissance) ne correspond pas strictement.",
  "COMPARE_PAN_DS_AVAILABLE_VARIANTS": "Variantes disponibles dans la datasheet (diagnostic)",

  "COMPARE_PAN_DS_COL_SECTION": "Section",
  "COMPARE_PAN_DS_COL_LABEL": "Paramètre",
  "COMPARE_PAN_DS_COL_UNIT": "Unité",
  "COMPARE_PAN_DS_COL_DS": "Datasheet",
  "COMPARE_PAN_DS_COL_PAN": "PAN",
  "COMPARE_PAN_DS_COL_DABS": "Écart absolu",
  "COMPARE_PAN_DS_COL_DPCT": "Écart (%)",
  "COMPARE_PAN_DS_COL_STATUS": "Statut",
  "COMPARE_PAN_DS_COL_TOL_ABS": "Tolérance abs.",
  "COMPARE_PAN_DS_COL_TOL_PCT": "Tolérance %",

  "COMPARE_PAN_DS_NO_OUTPUTS_YET": "Aucun résultat pour le moment. Lancez l’analyse pour générer un rapport.",
  "COMPARE_PAN_DS_DOWNLOAD_PDF": "Télécharger le rapport PDF",
  "COMPARE_PAN_DS_DOWNLOAD_LOG": "Télécharger le fichier log (texte)",
  "COMPARE_PAN_DS_EXPORTS_READY": "Exports disponibles ci-dessous (PDF / log).",

  # --- Compare PAN vs Datasheet (UI/Help additions) ---

  "COMPARE_PAN_DS_TIMESTAMP_OUTPUTS": "Ajouter un horodatage aux exports",
  "COMPARE_PAN_DS_RUN_HELP": "Lance l’analyse PAN vs datasheet et génère un rapport PDF + un log.",
  "COMPARE_PAN_DS_EXPORT_TITLE": "Exports",

  "COMPARE_PAN_DS_HELP_GENERALITIES": (
      "Synthèse d’identification et de traçabilité : date d’analyse, fabricant sélectionné, "
      "fichiers utilisés, modèle et puissance. Utile pour éviter toute comparaison entre modules différents."
  ),

  "COMPARE_PAN_DS_HELP_COMPARISON": (
      "Comparaison stricte des paramètres influençant la performance du module selon l’irradiance "
      "(STC, coefficients de température, bifacialité, Rshunt). "
      "Un écart (%) élevé indique souvent une incohérence de modèle ou de paramétrage."
  ),

  "COMPARE_PAN_DS_HELP_IAM": (
      "Le profil IAM (Incidence Angle Modifier) décrit la perte optique lorsque la lumière arrive "
      "avec un angle non normal au module. Plus l’angle augmente, plus l’IAM diminue → pertes IAM augmentent. "
      "Impact direct sur la production en matin/soir et en hiver."
  ),

  "COMPARE_PAN_DS_HELP_EXPORTS": (
      "Télécharge le rapport PDF et le log texte générés lors de la dernière analyse."
  ),

  # --- Compare PAN vs Datasheet — Electrical explainer ---

  "COMPARE_PAN_DS_ELEC_EXPLAINER_TITLE": "Comprendre les paramètres électriques",
  "COMPARE_PAN_DS_ELEC_EXPLAINER_SECION" : "Explications Techniques",

  "COMPARE_PAN_DS_ELEC_EXPLAINER_TEXT": """
  Comprendre les paramètres électriques du module

  ---

  ## 🔹 Données STC (conditions standard)

  STC = 1000 W/m², 25°C cellule.

  ### Isc – Courant de court-circuit

  - Courant maximal fourni par le module à irradiance donnée.
  - Augmente quasi linéairement avec l’irradiance.
  - Augmente légèrement avec la température (α > 0).
  - Paramètre principalement piloté par l’irradiance.

  ---

  ### Voc – Tension à vide

  - Tension maximale sans charge.
  - Diminue lorsque la température augmente (β < 0).
  - Paramètre critique pour le dimensionnement des strings (surtension à froid).

  ---

  ### Vmpp & Impp – Point de puissance maximale

  - Définissent le point optimal de fonctionnement.
  - Vmpp diminue avec la température.
  - Impp augmente légèrement avec l’irradiance.
  - Leur produit donne la puissance maximale Pmax.

  ---

  ## 🔹 Coefficients de température

  Ces paramètres décrivent la sensibilité du module à la température cellule.

  ### α – Coefficient de Isc (%/°C)

  - Généralement faible et positif (~ +0.04 à +0.06 %/°C).
  - Impact limité sur la puissance globale.

  ### β – Coefficient de Voc (%/°C)

  - Toujours négatif (~ −0.25 à −0.35 %/°C).
  - Impact significatif en climat chaud.

  ### γ – Coefficient de Pmax (%/°C)

  - Paramètre thermique le plus important.
  - Typiquement entre −0.28 et −0.35 %/°C.
  - Exemple : -0.30 %/°C → +20°C → -6 % de puissance.

  ### μIsc (mA/°C) & μVoc (mV/°C)

  - Versions absolues des coefficients précédents.
  - Permettent de vérifier la cohérence entre valeurs absolues et valeurs en %/°C.

  ---

  ## 🔹 RShunt – Résistance de shunt

  RShunt représente les pertes internes dues aux chemins parasites dans la cellule.

  - Plus RShunt est élevée → moins de pertes → meilleur rendement à faible irradiance.
  - Faible RShunt → dégradation de la courbe I/V à basse tension.
  - Impact visible le matin, le soir et sous ciel couvert.

  ### Formule par défaut utilisée par PVsyst :

  Rshunt = Vmpp / (0.2 × (Isc − Impp))

  où :
  - Vmpp = tension au point de puissance max
  - Isc = courant de court-circuit
  - Impp = courant au point de puissance max

  Le facteur 0.2 correspond à une approximation empirique de la conductance différentielle autour du point MPP.

  Cette valeur est une estimation basée uniquement sur les données STC.
  Le fichier PAN peut contenir une valeur optimisée issue du modèle une-diode.

  ---

  ## 🔹 IAM – Incidence Angle Modifier

  L’IAM décrit la perte optique due à l’angle d’incidence.

  - IAM = 1 → incidence normale.
  - IAM < 1 → pertes optiques.
  - Impact important le matin, le soir et en hiver.

  Même avec des STC identiques, un profil IAM défavorable réduit la production annuelle.

  ---

  ## 🔹 Bifacialité

  - Rapport entre puissance arrière et avant.
  - Facteur 0.7 → 70 % de performance face arrière.
  - Paramètre déterminant pour centrales au sol à albédo élevé.

  ---

  ## 🔹 Tension système maximale

  - Limite électrique maximale du module.
  - Paramètre critique pour le dimensionnement des strings à basse température.
  """,

# MARKET ANALYSIS TOOL

    "MARKET_ANALYSIS_TITLE": "Analyse marché de l’électricité",
    "MARKET_ANALYSIS_DESC": "Analyse des prix de marché de l’électricité, croisement avec résultats horaires PVSyst, comparaison de variantes et screening BESS.",

    "MARKET_ANALYSIS_CONFIG_TITLE": "Configuration",
    "MARKET_ANALYSIS_MARKET_SOURCE": "Source marché",
    "MARKET_ANALYSIS_MARKET_SOURCE_API": "API Energy Charts",
    "MARKET_ANALYSIS_MARKET_SOURCE_CSV": "CSV marché local",
    "MARKET_ANALYSIS_ANALYSIS_MODE": "Mode d’analyse",
    "MARKET_ANALYSIS_MODE_SINGLE": "Variante unique",
    "MARKET_ANALYSIS_MODE_COMPARISON": "Comparaison 2 variantes",
    "MARKET_ANALYSIS_ENABLE_BESS": "Activer l’analyse BESS",
    "MARKET_ANALYSIS_MARKET_ZONE": "Pays / zone marché",
    "MARKET_ANALYSIS_YEAR": "Année",
    "MARKET_ANALYSIS_MARKET_CSV_UPLOAD": "CSV marché local",

    "MARKET_ANALYSIS_PVSYST_SOURCES_TITLE": "Sources PVSyst",
    "MARKET_ANALYSIS_PV_FILE_A": "Fichier horaire PVSyst - Variante A",
    "MARKET_ANALYSIS_PV_LABEL_A": "Label variante A",
    "MARKET_ANALYSIS_PV_FILE_B": "Fichier horaire PVSyst - Variante B",
    "MARKET_ANALYSIS_PV_LABEL_B": "Label variante B",

    "MARKET_ANALYSIS_BESS_PARAMS_TITLE": "Paramètres BESS (laisser vide pour utiliser les valeurs par défaut)",
    "MARKET_ANALYSIS_BESS_PARAM_CAPACITY": "Capacité batterie (MWh)",
    "MARKET_ANALYSIS_BESS_PARAM_CHARGE_POWER": "Puissance charge max (MW)",
    "MARKET_ANALYSIS_BESS_PARAM_DISCHARGE_POWER": "Puissance décharge max (MW)",
    "MARKET_ANALYSIS_BESS_PARAM_EFFICIENCY": "Rendement aller-retour (0-1)",
    "MARKET_ANALYSIS_BESS_PARAM_CHARGE_THRESHOLD": "Seuil charge (EUR/MWh)",
    "MARKET_ANALYSIS_BESS_PARAM_DISCHARGE_THRESHOLD": "Seuil décharge (EUR/MWh)",

    "MARKET_ANALYSIS_RUN_BUTTON": "Lancer l’analyse",
    "MARKET_ANALYSIS_RUNNING": "Analyse en cours...",
    "MARKET_ANALYSIS_INFO_WAITING": "Charge les données puis lance l’analyse.",
    "MARKET_ANALYSIS_ERROR_NEED_MARKET_CSV": "Veuillez charger un CSV marché.",
    "MARKET_ANALYSIS_ERROR_NEED_PV_A": "Veuillez charger le fichier PVSyst de la variante A.",
    "MARKET_ANALYSIS_ERROR_NEED_PV_B": "Veuillez charger le fichier PVSyst de la variante B.",
    "MARKET_ANALYSIS_WARNINGS_TITLE": "Warnings",

    "MARKET_ANALYSIS_TIME_SECTION_TITLE": "Temporalité et harmonisation",
    "MARKET_ANALYSIS_TIME_SECTION_DESC": "Le calcul marché ↔ PV est effectué sur des données harmonisées, tout en conservant les données originales pour la traçabilité et les exports.",
    "MARKET_ANALYSIS_TIME_EXPANDER": "Afficher les informations de temporalité et d’harmonisation",
    "MARKET_ANALYSIS_TIME_MARKET_ORIGINAL": "Pas de temps marché (original)",
    "MARKET_ANALYSIS_TIME_MARKET_ANALYSIS": "Pas de temps marché (analyse)",
    "MARKET_ANALYSIS_TIME_PV_A_ORIGINAL": "Pas de temps PV A (original)",
    "MARKET_ANALYSIS_TIME_PV_A_ANALYSIS": "Pas de temps PV A (analyse)",
    "MARKET_ANALYSIS_TIME_PV_B_ORIGINAL": "Pas de temps PV B (original)",
    "MARKET_ANALYSIS_TIME_PV_B_ANALYSIS": "Pas de temps PV B (analyse)",
    "MARKET_ANALYSIS_TIME_ANALYSIS_STEP": "Pas de temps utilisé pour l’analyse",
    "MARKET_ANALYSIS_TIME_MARKET_BLOCK": "Marché",
    "MARKET_ANALYSIS_TIME_PV_BLOCK": "PVSyst",
    "MARKET_ANALYSIS_TIME_ORIGINAL_ROWS": "Données originales conservées",
    "MARKET_ANALYSIS_TIME_ANALYSIS_ROWS": "Données utilisées pour l’analyse",
    "MARKET_ANALYSIS_TIME_RESAMPLED": "Resampling appliqué",
    "MARKET_ANALYSIS_TIME_METHOD": "Méthode",
    "MARKET_ANALYSIS_TIME_ENERGY_CONVERSION": "Conversion énergie",
    "MARKET_ANALYSIS_TIME_ANALYSIS_NOTE": "Le calcul marché ↔ PV est effectué sur les données harmonisées.",

    "MARKET_ANALYSIS_TAB_MAIN": "Principal",
    "MARKET_ANALYSIS_TAB_DETAILED": "Détaillé",

    "MARKET_ANALYSIS_EXEC_SUMMARY_TITLE": "Résumé exécutif",
    "MARKET_ANALYSIS_HELP_BUTTON": "🔴 ? Aide",
    "MARKET_ANALYSIS_HELP_TITLE": "Définitions et interprétation des grandeurs",
    "MARKET_ANALYSIS_HELP_PRICE_MEAN": "Prix moyen annuel : moyenne simple des prix horaires du marché sur la période étudiée.",
    "MARKET_ANALYSIS_HELP_NEGATIVE_HOURS": "Heures négatives : nombre d’heures où le prix de marché est inférieur à 0 €/MWh.",
    "MARKET_ANALYSIS_HELP_ENERGY_INJECTED": "Énergie injectée : énergie effectivement injectée après application de la coupure sur les heures à prix négatif.",
    "MARKET_ANALYSIS_HELP_MARKET_VALUE": "Valeur marché : valorisation théorique de l’énergie injectée en multipliant, heure par heure, l’énergie injectée par le prix de marché.",
    "MARKET_ANALYSIS_HELP_CURTAILED_ENERGY": "Énergie coupée : énergie théorique produite pendant les heures à prix négatif et supposée non injectée.",
    "MARKET_ANALYSIS_HELP_CAPTURE_PRICE": "Prix capté moyen : prix moyen effectivement capté par la production injectée. Il est calculé en divisant la valeur marché totale par l’énergie injectée.",
    "MARKET_ANALYSIS_HELP_CAPTURE_RATE": "Indice de captation : rapport entre le prix capté moyen et le prix moyen du marché. Une valeur supérieure à 1 signifie que la production est injectée en moyenne sur des heures mieux valorisées que le marché moyen.",
    "MARKET_ANALYSIS_HELP_CURTAILED_SHARE": "Part coupée : part de l’énergie théorique annuelle qui n’est pas injectée à cause des prix négatifs.",
    "MARKET_ANALYSIS_HELP_BESS": "Analyse BESS : estimation simplifiée du potentiel de stockage de l’énergie coupée, puis de sa restitution sur des heures à prix plus élevé.",

    "MARKET_ANALYSIS_KPI_PRICE_MEAN": "Prix moyen annuel",
    "MARKET_ANALYSIS_KPI_NEGATIVE_HOURS": "Heures négatives",
    "MARKET_ANALYSIS_KPI_ENERGY_INJECTED": "Énergie injectée",
    "MARKET_ANALYSIS_KPI_MARKET_VALUE": "Valeur marché",
    "MARKET_ANALYSIS_KPI_CURTAILED_ENERGY": "Énergie coupée",
    "MARKET_ANALYSIS_KPI_CAPTURE_PRICE": "Prix capté moyen",
    "MARKET_ANALYSIS_KPI_CAPTURE_RATE": "Indice de captation",
    "MARKET_ANALYSIS_KPI_CURTAILED_SHARE": "Part coupée",

    "MARKET_ANALYSIS_KPI_VARIANT_ENERGY": "Énergie {label}",
    "MARKET_ANALYSIS_KPI_VARIANT_VALUE": "Valeur {label}",
    "MARKET_ANALYSIS_KPI_VARIANT_CAPTURE_PRICE": "Prix capté moyen {label}",
    "MARKET_ANALYSIS_KPI_VARIANT_CURTAILED": "Énergie coupée {label}",

    "MARKET_ANALYSIS_CONCLUSIONS_TITLE": "Conclusions clés",
    "MARKET_ANALYSIS_CONCLUSION_LOW_NEGATIVE": "L’exposition aux prix négatifs est **faible** avec seulement **{value:.2f} %** d’énergie coupée.",
    "MARKET_ANALYSIS_CONCLUSION_MEDIUM_NEGATIVE": "L’exposition aux prix négatifs est **modérée** avec **{value:.2f} %** d’énergie coupée.",
    "MARKET_ANALYSIS_CONCLUSION_HIGH_NEGATIVE": "L’exposition aux prix négatifs est **significative** avec **{value:.2f} %** d’énergie coupée.",
    "MARKET_ANALYSIS_CONCLUSION_HIGH_PRICE_SHARE_HIGH": "Une part notable de la production tombe sur les heures chères, avec **{value:.2f} %** de l’énergie sur ces heures.",
    "MARKET_ANALYSIS_CONCLUSION_HIGH_PRICE_SHARE_LOW": "La part de production sur les heures chères reste limitée, avec **{value:.2f} %** de l’énergie sur ces heures.",
    "MARKET_ANALYSIS_CONCLUSION_CAPTURE_RATE_GOOD": "Le profil de production capte un prix moyen au moins égal au marché moyen, avec un indice de captation de **{value:.2f}**.",
    "MARKET_ANALYSIS_CONCLUSION_CAPTURE_RATE_LOW": "Le profil de production capte un prix moyen inférieur au marché moyen, avec un indice de captation de **{value:.2f}**.",
    "MARKET_ANALYSIS_CONCLUSION_MARKET_RESAMPLED": "Les prix marché ont été harmonisés au pas horaire pour l’analyse.",
    "MARKET_ANALYSIS_CONCLUSION_PV_RESAMPLED": "Les données PVSyst ont été harmonisées au pas horaire pour l’analyse.",

    "MARKET_ANALYSIS_MAIN_CHARTS_TITLE": "Graphiques principaux",

    "MARKET_ANALYSIS_BESS_TITLE": "Screening BESS",
    "MARKET_ANALYSIS_BESS_KPI_AVAILABLE": "Énergie stockable",
    "MARKET_ANALYSIS_BESS_KPI_DISCHARGED": "Énergie restituée",
    "MARKET_ANALYSIS_BESS_KPI_ADDED_VALUE": "Valeur ajoutée BESS",
    "MARKET_ANALYSIS_BESS_KPI_EQ_CYCLES": "Cycles équivalents",

    "MARKET_ANALYSIS_DETAIL_TITLE": "Hypothèses, métadonnées et pas de temps",
    "MARKET_ANALYSIS_META_GLOBAL": "Meta globale",
    "MARKET_ANALYSIS_META_MARKET": "Meta marché",
    "MARKET_ANALYSIS_META_PV_A": "Meta PV A",
    "MARKET_ANALYSIS_META_PV_B": "Meta PV B",
    "MARKET_ANALYSIS_BESS_ASSUMPTIONS_TITLE": "Hypothèses BESS utilisées",

    "MARKET_ANALYSIS_EXPORTS_TITLE": "Exports",
    "MARKET_ANALYSIS_EXPORT_MARKET_ORIGINAL": "Télécharger marché original (CSV)",
    "MARKET_ANALYSIS_EXPORT_MERGED": "Télécharger merged {label}",
    "MARKET_ANALYSIS_EXPORT_ANNUAL_A": "Télécharger résumé annuel A",
    "MARKET_ANALYSIS_EXPORT_MONTHLY_A": "Télécharger résumé mensuel A",
    "MARKET_ANALYSIS_EXPORT_SEASONAL_A": "Télécharger résumé saisonnier A",

    "MARKET_ANALYSIS_TABLES_TITLE": "Tableaux",
    "MARKET_ANALYSIS_TABLE_ANNUAL_A": "Résumé annuel variante A",
    "MARKET_ANALYSIS_TABLE_MONTHLY_A": "Résumé mensuel variante A",
    "MARKET_ANALYSIS_TABLE_SEASONAL_A": "Résumé saisonnier variante A",
    "MARKET_ANALYSIS_TABLE_MARKET_ONLY": "Résumé marché seul (analyse harmonisée)",
    "MARKET_ANALYSIS_TABLE_MARKET_INDICATORS": "Indicateurs marché",
    "MARKET_ANALYSIS_TABLE_PRICE_DISTRIBUTION": "Distribution des prix",
    "MARKET_ANALYSIS_TABLE_MONTHLY_MARKET": "Résumé mensuel marché",
    "MARKET_ANALYSIS_TABLE_SEASONAL_MARKET": "Résumé saisonnier marché",

    "MARKET_ANALYSIS_TABLE_TYPICAL_PROFILES": "Profils journaliers détaillés",
    "MARKET_ANALYSIS_TABLE_TYPICAL_PRICE": "Prix typique",
    "MARKET_ANALYSIS_TABLE_TYPICAL_PV_A": "Production typique A",
    "MARKET_ANALYSIS_TABLE_TYPICAL_PV_B": "Production typique B",

    "MARKET_ANALYSIS_TABLE_ORIGINAL_VS_ANALYSIS": "Données originales vs données d’analyse",
    "MARKET_ANALYSIS_TABLE_MARKET_ORIGINAL": "Marché original",
    "MARKET_ANALYSIS_TABLE_MARKET_ANALYSIS": "Marché harmonisé pour l’analyse",
    "MARKET_ANALYSIS_TABLE_PV_A_ORIGINAL": "PV A original",
    "MARKET_ANALYSIS_TABLE_PV_A_ANALYSIS": "PV A harmonisé pour l’analyse",
    "MARKET_ANALYSIS_TABLE_PV_B_ORIGINAL": "PV B original",
    "MARKET_ANALYSIS_TABLE_PV_B_ANALYSIS": "PV B harmonisé pour l’analyse",

    "MARKET_ANALYSIS_COMPARE_TITLE": "Comparaison variantes",
    "MARKET_ANALYSIS_COMPARE_ANNUAL": "Résumé annuel comparaison",
    "MARKET_ANALYSIS_COMPARE_MONTHLY": "Résumé mensuel comparaison",
    "MARKET_ANALYSIS_COMPARE_SEASONAL": "Résumé saisonnier comparaison",
    "MARKET_ANALYSIS_COMPARE_CONCLUSIONS": "Conclusions",

    "MARKET_ANALYSIS_BESS_VARIANT_TITLE": "BESS - {label}",
    "MARKET_ANALYSIS_BESS_ANNUAL": "Indicateurs annuels",
    "MARKET_ANALYSIS_BESS_MONTHLY": "Résumé mensuel",
    "MARKET_ANALYSIS_BESS_SEASONAL": "Résumé saisonnier",
    "MARKET_ANALYSIS_BESS_HOURLY_HEAD": "Série horaire BESS (head)",

    "MARKET_ANALYSIS_NA": "n/a",

    "MARKET_ANALYSIS_HELP_GENERAL_RESULTS_TITLE": "Aide — résultats généraux",
    "MARKET_ANALYSIS_HELP_GENERAL_RESULTS_BODY": """
Les résultats généraux synthétisent la performance économique du profil de production face aux prix de marché.

**Prix moyen annuel** : moyenne simple des prix horaires du marché sur la période étudiée.

**Heures négatives** : nombre d’heures où le prix de marché est inférieur à 0 €/MWh.

**Énergie injectée** : énergie effectivement injectée après application de l’hypothèse de coupure pendant les heures à prix négatif.

**Valeur marché** : valorisation théorique de l’énergie injectée, calculée heure par heure comme :
valeur = énergie injectée × prix de marché

**Énergie coupée** : énergie théorique produite pendant les heures à prix négatif et supposée non injectée.

**Prix capté moyen** : prix moyen effectivement capté par la production injectée.  
Il est calculé comme :
prix capté moyen = valeur marché / énergie injectée

Il permet de savoir si la production tombe plutôt sur des heures bien valorisées ou non.

**Indice de captation** : rapport entre le prix capté moyen et le prix moyen du marché.  
Il est calculé comme :
indice de captation = prix capté moyen / prix moyen du marché

- **> 1** : la production est injectée, en moyenne, sur des heures mieux valorisées que le marché moyen.
- **< 1** : la production est injectée, en moyenne, sur des heures moins valorisées que le marché moyen.
""",

    "MARKET_ANALYSIS_HELP_PROFILES_TITLE": "Aide — profils types",
    "MARKET_ANALYSIS_HELP_PROFILES_BODY": """
Les profils types représentent des courbes moyennes par heure de la journée, construites sur l’ensemble de l’année.

**Courbe de production** : production théorique moyenne de la centrale à chaque heure.

**Courbe d’injection** : énergie moyenne effectivement injectée à chaque heure après application de l’hypothèse de coupure pendant les heures à prix négatif.  
L’écart entre la courbe de production et la courbe d’injection représente donc l’effet moyen des épisodes de prix négatifs.

**Prix moyen** : prix moyen du marché pour chaque heure de la journée.

**P25 / P75** :
- **P25** : quartile inférieur ; 25 % des valeurs de prix sont en dessous
- **P75** : quartile supérieur ; 75 % des valeurs de prix sont en dessous

La bande **P25–P75** donne une idée de la variabilité habituelle du prix autour de sa moyenne horaire :
- bande étroite = prix plus stable
- bande large = prix plus variable
""",

"MARKET_ANALYSIS_HELP_CONFIG_TITLE": "Aide — configuration de l'analyse",

"MARKET_ANALYSIS_HELP_CONFIG_BODY": """
Cette section permet de configurer les données utilisées pour l'analyse croisée entre prix de marché et production PV.

**Source des prix de marché** :
- **API** : télécharge automatiquement les prix de marché (day-ahead) pour le pays et l’année sélectionnés.
- **CSV** : permet d’utiliser un fichier local de prix (exporté depuis cet outil ou issu d’une autre source).

**Zone de marché** :
Correspond à la zone de prix sélectionnée (France, Allemagne, Espagne, etc.).  
Les prix peuvent varier fortement d’un pays à l’autre.

**Année** :
Définit la période d’analyse des prix de marché.  
La production PVSyst sera alignée sur cette année (par jour et heure uniquement).

**Mode d’analyse** :
- **Variante unique** : analyse d’un seul fichier PVSyst.
- **Comparaison** : comparaison de deux variantes (ex : fixe vs tracker).

**Fichiers PVSyst** :
Importer un ou deux fichiers de résultats horaires PVSyst (.CSV ou .TXT).  
Seule la colonne **E_Grid** est utilisée (énergie injectée).

**Analyse stockage (optionnelle)** :
Permet d’activer une estimation simplifiée du potentiel de stockage (BESS).  
Si les paramètres sont laissés vides, des valeurs par défaut sont utilisées.

👉 Recommandation :
- utiliser une année représentative (ex : année récente)
- vérifier la cohérence entre le climat (PVSyst) et le marché choisi
""",

    "MARKET_ANALYSIS_COL_MONTH": "Mois",
    "MARKET_ANALYSIS_COL_SEASON": "Saison",
    "MARKET_ANALYSIS_COL_HOUR": "Heure",
    "MARKET_ANALYSIS_COL_TIMESTAMP": "Horodatage",
    "MARKET_ANALYSIS_COL_DATE": "Date",
    "MARKET_ANALYSIS_COL_YEAR": "Année",
    "MARKET_ANALYSIS_COL_DAY": "Jour",
    "MARKET_ANALYSIS_COL_BZN": "Zone de marché",
    "MARKET_ANALYSIS_COL_SOURCE": "Source",
    "MARKET_ANALYSIS_COL_SOURCE_MODE": "Mode source",
    "MARKET_ANALYSIS_COL_VARIANT": "Variante",
    "MARKET_ANALYSIS_COL_METRIC": "Indicateur",
    "MARKET_ANALYSIS_COL_VALUE": "Valeur",

    "MARKET_ANALYSIS_COL_PRICE": "Prix (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_MEAN": "Prix moyen (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_MEDIAN": "Prix médian (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_MIN": "Prix min (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_MAX": "Prix max (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_STD": "Écart-type prix (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_P10": "Prix P10 (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_P25": "Prix P25 (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_P75": "Prix P75 (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_P90": "Prix P90 (EUR/MWh)",
    "MARKET_ANALYSIS_COL_PRICE_CV": "Coeff. variation prix (%)",

    "MARKET_ANALYSIS_COL_NEGATIVE_HOURS": "Heures négatives",
    "MARKET_ANALYSIS_COL_NEGATIVE_DAYS": "Jours négatifs",
    "MARKET_ANALYSIS_COL_NEGATIVE_HOUR_SHARE": "Part d'heures négatives (%)",
    "MARKET_ANALYSIS_COL_N_HOURS": "Nombre d'heures",

    "MARKET_ANALYSIS_COL_ENERGY_THEORETICAL": "Énergie théorique (MWh)",
    "MARKET_ANALYSIS_COL_ENERGY_INJECTED": "Énergie injectée (MWh)",
    "MARKET_ANALYSIS_COL_ENERGY_CURTAILED": "Énergie coupée (MWh)",
    "MARKET_ANALYSIS_COL_MARKET_VALUE": "Valeur marché (EUR)",
    "MARKET_ANALYSIS_COL_MARKET_VALUE_RAW": "Valeur marché brute (EUR)",
    "MARKET_ANALYSIS_COL_NEGATIVE_HOURS_MARKET": "Heures négatives marché",
    "MARKET_ANALYSIS_COL_NEGATIVE_HOURS_WITH_GEN": "Heures négatives avec production",
    "MARKET_ANALYSIS_COL_DAYS_IN_PERIOD": "Nombre de jours",
    "MARKET_ANALYSIS_COL_NEGATIVE_DAYS_MARKET": "Jours négatifs marché",
    "MARKET_ANALYSIS_COL_NEGATIVE_DAYS_WITH_GEN": "Jours négatifs avec production",
    "MARKET_ANALYSIS_COL_ENERGY_HIGH_PRICE": "Énergie sur heures chères (MWh)",
    "MARKET_ANALYSIS_COL_CAPTURE_PRICE": "Prix capté moyen (EUR/MWh)",
    "MARKET_ANALYSIS_COL_CAPTURE_RATE": "Indice de captation",
    "MARKET_ANALYSIS_COL_CURTAILED_SHARE": "Part coupée (%)",
    "MARKET_ANALYSIS_COL_HIGH_PRICE_SHARE": "Part énergie sur heures chères (%)",
    "MARKET_ANALYSIS_COL_AVG_CURTAILED_PER_DAY": "Énergie coupée moyenne par jour (MWh)",
    "MARKET_ANALYSIS_COL_AVG_CURTAILED_PER_IMPACTED_DAY": "Énergie coupée moyenne par jour impacté (MWh)",

    "MARKET_ANALYSIS_COL_PV_MEAN": "Production moyenne (MWh)",
    "MARKET_ANALYSIS_COL_PV_MEDIAN": "Production médiane (MWh)",
    "MARKET_ANALYSIS_COL_PV_P25": "Production P25 (MWh)",
    "MARKET_ANALYSIS_COL_PV_P75": "Production P75 (MWh)",
    "MARKET_ANALYSIS_COL_PV_INJECTED_MEAN": "Injection moyenne (MWh)",
    "MARKET_ANALYSIS_COL_PV_INJECTED_MEDIAN": "Injection médiane (MWh)",
    "MARKET_ANALYSIS_COL_PV_CURTAILED_MEAN": "Énergie coupée moyenne (MWh)",

    "MARKET_ANALYSIS_COL_EGRID": "Production théorique (MWh)",
    "MARKET_ANALYSIS_COL_EGRID_INJECTED": "Énergie injectée (MWh)",
    "MARKET_ANALYSIS_COL_EGRID_CURTAILED": "Énergie coupée (MWh)",
    "MARKET_ANALYSIS_COL_IS_NEGATIVE": "Prix négatif",
    "MARKET_ANALYSIS_COL_IS_POSITIVE_GEN": "Production positive",
    "MARKET_ANALYSIS_COL_HAS_NEG_AND_GEN": "Prix négatif avec production",
    "MARKET_ANALYSIS_COL_IS_HIGH_PRICE": "Heure chère",

    "MARKET_ANALYSIS_COL_BESS_ENERGY_AVAILABLE": "Énergie stockable (MWh)",
    "MARKET_ANALYSIS_COL_BESS_CHARGED_SOURCE": "Énergie chargée depuis la source (MWh)",
    "MARKET_ANALYSIS_COL_BESS_DISCHARGED": "Énergie restituée (MWh)",
    "MARKET_ANALYSIS_COL_BESS_LOSSES": "Pertes totales (MWh)",
    "MARKET_ANALYSIS_COL_BESS_ADDED_VALUE": "Valeur ajoutée BESS (EUR)",
    "MARKET_ANALYSIS_COL_BESS_MAX_SOC": "SOC max (MWh)",
    "MARKET_ANALYSIS_COL_BESS_CHARGE_HOURS": "Heures de charge",
    "MARKET_ANALYSIS_COL_BESS_DISCHARGE_HOURS": "Heures de décharge",
    "MARKET_ANALYSIS_COL_BESS_RECOVERY_RATIO": "Taux de récupération",
    "MARKET_ANALYSIS_COL_BESS_SOC_BEFORE": "SOC avant (MWh)",
    "MARKET_ANALYSIS_COL_BESS_SOC_AFTER": "SOC après (MWh)",
    "MARKET_ANALYSIS_COL_BESS_CHARGE_SOURCE": "Charge depuis source (MWh)",
    "MARKET_ANALYSIS_COL_BESS_CHARGE_BATTERY": "Charge en batterie (MWh)",
    "MARKET_ANALYSIS_COL_BESS_DISCHARGE_BATTERY": "Décharge batterie (MWh)",
    "MARKET_ANALYSIS_COL_BESS_DISCHARGE_GRID": "Décharge réseau (MWh)",
    "MARKET_ANALYSIS_COL_BESS_CHARGE_LOSSES": "Pertes de charge (MWh)",
    "MARKET_ANALYSIS_COL_BESS_DISCHARGE_LOSSES": "Pertes de décharge (MWh)",
    "MARKET_ANALYSIS_COL_BESS_TOTAL_LOSSES": "Pertes totales BESS (MWh)",
    "MARKET_ANALYSIS_COL_BESS_MARKET_VALUE": "Valeur BESS (EUR)",
    "MARKET_ANALYSIS_COL_BESS_IS_CHARGING": "En charge",
    "MARKET_ANALYSIS_COL_BESS_IS_DISCHARGING": "En décharge",
    "MARKET_ANALYSIS_COL_MARKET_VALUE_WITH_BESS": "Valeur marché avec BESS (EUR)",

    "MARKET_ANALYSIS_SEASON_WINTER": "Hiver",
    "MARKET_ANALYSIS_SEASON_SPRING": "Printemps",
    "MARKET_ANALYSIS_SEASON_SUMMER": "Été",
    "MARKET_ANALYSIS_SEASON_AUTUMN": "Automne",

    "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_MARKET_VALUE": "La variante {better} crée plus de valeur marché que la variante {other}.",
    "MARKET_ANALYSIS_COMPARE_CONCLUSION_EQUAL_MARKET_VALUE": "{label_a} et {label_b} créent une valeur marché équivalente.",

    "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_CAPTURE_PRICE": "La variante {better} présente un meilleur prix capté moyen que la variante {other}.",
    "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_NEGATIVE_EXPOSURE": "La variante {better} réduit davantage l’exposition aux prix négatifs que la variante {other}.",
    "MARKET_ANALYSIS_COMPARE_CONCLUSION_BETTER_HIGH_PRICE_ALIGNMENT": "La variante {better} produit davantage sur les heures chères que la variante {other}.",

    "MARKET_ANALYSIS_COMPARE_CONCLUSION_ENERGY_TO_VALUE_FULL": "Le gain énergétique de la variante {better} se traduit pleinement, voire davantage, en gain de valeur marché par rapport à la variante {other}.",
    "MARKET_ANALYSIS_COMPARE_CONCLUSION_ENERGY_TO_VALUE_PARTIAL": "Le gain énergétique de la variante {better} ne se traduit que partiellement en gain de valeur marché par rapport à la variante {other}.",

    "MARKET_ANALYSIS_COMPARE_CONCLUSION_NONE": "Aucune conclusion comparative forte n’a pu être dégagée.",

    "TOOL_BESS_SIZING_TITLE": "Dimensionnement BESS PV",
    "TOOL_BESS_SIZING_DESC": "Screening de dimensionnement MW x MWh d'un BESS couple au PV avec optimisation horaire sur prix day-ahead.",

    "BESS_SIZING_INPUT_GUIDE_TITLE": "Configuration V1 - batterie couplee au PV",
    "BESS_SIZING_INPUT_GUIDE_BODY": (
        "- Charger le fichier PV annuel, le fichier TMY et la source prix (API recommandee).\n"
        "- Verifier ou corriger le mapping des colonnes detectees automatiquement.\n"
        "- Definir la grille de puissance et duree, puis lancer le screening."
    ),
    "BESS_SIZING_UPLOAD_PV": "Fichier production PV (annuel)",
    "BESS_SIZING_UPLOAD_TMY": "Fichier meteo TMY (horaire ou 15 min)",
    "BESS_SIZING_MARKET_SOURCE": "Source des prix day-ahead",
    "BESS_SIZING_MARKET_SOURCE_API": "API outil marche (recommande)",
    "BESS_SIZING_MARKET_SOURCE_CSV": "Fichier CSV prix",
    "BESS_SIZING_MARKET_BZN": "Zone de marche (BZN)",
    "BESS_SIZING_MARKET_YEAR": "Annee de prix",
    "BESS_SIZING_UPLOAD_MARKET": "Fichier prix day-ahead",

    "BESS_SIZING_COL_TIMESTAMP_PV": "Colonne timestamp PV",
    "BESS_SIZING_COL_VALUE_PV": "Colonne energie/puissance PV",
    "BESS_SIZING_COL_TIMESTAMP_TMY": "Colonne timestamp TMY",
    "BESS_SIZING_COL_VALUE_TMY": "Colonne signal TMY (coherence)",
    "BESS_SIZING_COL_TIMESTAMP_MARKET": "Colonne timestamp prix",
    "BESS_SIZING_COL_VALUE_MARKET": "Colonne prix",
    "BESS_SIZING_UNIT_PV": "Unite PV",
    "BESS_SIZING_UNIT_MARKET": "Unite prix",
    "BESS_SIZING_DETECTED_UNIT": "Unite detectee",

    "BESS_SIZING_SIZING_PARAMS_TITLE": "Parametres de screening",
    "BESS_SIZING_ANALYSIS_STRATEGY_INFO": (
        "Strategie V2: l'outil calcule systematiquement l'optimisation marginale et l'analyse CAPEX/OPEX "
        "(valeurs par defaut ou modifiees), puis compare la config optimisee au gain brut maximal."
    ),
    "BESS_SIZING_INPUT_TAB_TECH": "Technique",
    "BESS_SIZING_INPUT_TAB_ECON": "CAPEX / OPEX",
    "BESS_SIZING_POWER_MIN": "Puissance min (MW)",
    "BESS_SIZING_POWER_MAX": "Puissance max (MW)",
    "BESS_SIZING_POWER_STEP": "Pas puissance (MW)",
    "BESS_SIZING_DURATIONS": "Durees a tester (h)",
    "BESS_SIZING_DURATIONS_HELP": "Valeurs utility-scale recommandees: 2h, 4h, 6h, 8h, 10h.",
    "BESS_SIZING_SOC_MIN": "SOC min (0-1)",
    "BESS_SIZING_SOC_MAX": "SOC max (0-1)",
    "BESS_SIZING_SOC_INITIAL": "SOC initial (0-1)",
    "BESS_SIZING_ROUNDTRIP": "Rendement aller-retour cible (0-1)",
    "BESS_SIZING_ENFORCE_TERMINAL_SOC": "Imposer SOC final = SOC initial",
    "BESS_SIZING_SOLVER_MODE": "Solveur dispatch",
    "BESS_SIZING_SOLVER_AUTO": "LP si disponible (sinon heuristique)",
    "BESS_SIZING_SOLVER_HEURISTIC": "Heuristique uniquement",
    "BESS_SIZING_SOLVER_MODE_HELP": (
        "LP (lineaire) cherche l'optimum global sous contraintes horaires et est plus robuste. "
        "Heuristique applique des regles simples plus rapides mais potentiellement sous-optimales."
    ),
    "BESS_SIZING_RUN_SECTION_TITLE": "Execution du screening",
    "BESS_SIZING_EXPORT_SECTION_TITLE": "Exports",

    "BESS_SIZING_RUN_BUTTON": "Lancer le screening BESS",
    "BESS_SIZING_RUNNING": "Calcul en cours...",
    "BESS_SIZING_DONE": "Screening termine.",
    "BESS_SIZING_NO_RESULTS": "Aucun resultat pour le moment.",
    "BESS_SIZING_WARNINGS": "Avertissements",
    "BESS_SIZING_WARNINGS_EMPTY": "Aucun avertissement detecte.",
    "BESS_SIZING_TAB_MAIN": "Resultats principaux",
    "BESS_SIZING_TAB_SECONDARY": "Diagnostic et hypotheses",

    "BESS_SIZING_EXEC_SUMMARY": "Resume executif",
    "BESS_SIZING_KPI_BEST_CONFIG": "Configuration gain brut max",
    "BESS_SIZING_KPI_GAIN_ABS": "Gain annuel absolu",
    "BESS_SIZING_KPI_GAIN_REL": "Gain annuel relatif",
    "BESS_SIZING_KPI_CYCLES": "Cycles equivalents",
    "BESS_SIZING_TABLE_TITLE": "Tableau de synthese",
    "BESS_SIZING_CHARTS_TITLE": "Visualisations",
    "BESS_SIZING_CHART_SCORE_MATRIX_TITLE": "Matrice de score MW x duree",
    "BESS_SIZING_CHART_GAIN_POWER_TITLE": "Gain annuel vs puissance",
    "BESS_SIZING_CHART_GAIN_DURATION_TITLE": "Gain annuel vs duree",
    "BESS_SIZING_CHART_COMPARISON_TITLE": "Comparaison PV seul vs PV + BESS",
    "BESS_SIZING_CONFIG_SECTION_TITLE": "Configuration analysee",
    "BESS_SIZING_SELECT_CONFIG": "Configuration detaillee",
    "BESS_SIZING_TIMESERIES_TITLE": "Serie temporelle detaillee",
    "BESS_SIZING_START_DATE": "Debut periode",
    "BESS_SIZING_END_DATE": "Fin periode",
    "BESS_SIZING_EMPTY_PERIOD": "Aucune donnee sur la periode selectionnee.",
    "BESS_SIZING_HEATMAP_TITLE": "Heatmap charge/decharge",
    "BESS_SIZING_TMY_COHERENCE_TITLE": "Coherence TMY (V1)",
    "BESS_SIZING_TMY_NO_DATA": "Aucune donnee TMY exploitable.",
    "BESS_SIZING_TMY_COVERAGE": "Couverture TMY",
    "BESS_SIZING_TMY_MATCHED": "Heures alignees",
    "BESS_SIZING_TMY_TOTAL": "Heures PV totales",
    "BESS_SIZING_TMY_CORR": "Correlation PV/TMY",
    "BESS_SIZING_ASSUMPTIONS_TITLE": "Hypotheses modele V1",

    "BESS_SIZING_COL_CONFIG": "Configuration batterie",
    "BESS_SIZING_COL_POWER": "Puissance (MW)",
    "BESS_SIZING_COL_DURATION": "Duree (h)",
    "BESS_SIZING_COL_ENERGY": "Energie nominale (MWh)",
    "BESS_SIZING_COL_REVENUE_PV_ONLY": "Revenu PV seul (EUR/an)",
    "BESS_SIZING_COL_REVENUE_PV_BESS": "Revenu PV + BESS (EUR/an)",
    "BESS_SIZING_COL_GAIN_ABS": "Gain annuel absolu (EUR/an)",
    "BESS_SIZING_COL_GAIN_REL": "Gain annuel relatif (%)",
    "BESS_SIZING_COL_CAPTURE_PV_ONLY": "Capture price PV seul (EUR/MWh)",
    "BESS_SIZING_COL_CAPTURE_PV_BESS": "Capture price PV + BESS (EUR/MWh)",
    "BESS_SIZING_COL_ENERGY_CHARGED": "Energie chargee (MWh/an)",
    "BESS_SIZING_COL_ENERGY_DISCHARGED": "Energie dechargee (MWh/an)",
    "BESS_SIZING_COL_LOSSES": "Pertes (MWh/an)",
    "BESS_SIZING_COL_THROUGHPUT": "Throughput (MWh/an)",
    "BESS_SIZING_COL_CYCLES": "Cycles equivalents (an)",
    "BESS_SIZING_COL_UTILIZATION": "Taux d'utilisation (%)",
    "BESS_SIZING_COL_HOURS_POWER_SAT": "Heures saturation puissance",
    "BESS_SIZING_COL_HOURS_ENERGY_SAT": "Heures saturation energie",
    "BESS_SIZING_COL_SOLVER": "Solveur",
    "BESS_SIZING_COL_ENERGY_CHARGED_PV": "Energie chargee depuis PV (MWh/an)",
    "BESS_SIZING_COL_ENERGY_CHARGED_GRID": "Energie chargee depuis reseau (MWh/an)",
    "BESS_SIZING_COL_GAIN_SHARE_MAX": "Part du gain max atteinte (%)",
    "BESS_SIZING_COL_MARGINAL_MW": "Gain marginal (EUR/MW add.)",
    "BESS_SIZING_COL_MARGINAL_MWH": "Gain marginal (EUR/MWh add.)",
    "BESS_SIZING_COL_USED_CAPACITY": "Capacite utile mobilisee (%)",
    "BESS_SIZING_COL_UNDERUTILIZED": "Capacite peu utilisee (%)",
    "BESS_SIZING_COL_POWER_SAT_RATE": "Saturation puissance (%)",
    "BESS_SIZING_COL_ENERGY_SAT_RATE": "Saturation energie (%)",
    "BESS_SIZING_COL_NET_MARGIN": "Marge nette annualisee (EUR/an)",
    "BESS_SIZING_COL_NET_REVENUE": "Revenu net annuel (EUR/an)",
    "BESS_SIZING_COL_ANNUALIZED_COST": "Cout annualise total (EUR/an)",
    "BESS_SIZING_COL_CAPEX": "CAPEX total (EUR)",
    "BESS_SIZING_COL_OPEX": "OPEX annuel total (EUR/an)",
    "BESS_SIZING_COL_PAYBACK": "Temps de retour simple (ans)",
    "BESS_SIZING_COL_NPV": "VAN simplifiee (EUR)",

    "BESS_SIZING_TECH_EXTRA_TITLE": "Options techniques V2",
    "BESS_SIZING_HELP_TECH_EXTRA": (
        "Options de couplage et contraintes reseau: charge reseau, limite d'injection, cout de degradation, pertes auxiliaires."
    ),
    "BESS_SIZING_ALLOW_GRID_CHARGING": "Autoriser la charge depuis le reseau",
    "BESS_SIZING_HELP_ALLOW_GRID_CHARGING": (
        "Si active, la batterie peut charger sur le marche en plus du PV. Sinon, charge uniquement via le PV."
    ),
    "BESS_SIZING_USE_GRID_LIMIT": "Appliquer une limite d'injection reseau",
    "BESS_SIZING_HELP_GRID_LIMIT": (
        "Limite d'export au point de raccordement (MW). Permet d'analyser les cas de contrainte reseau."
    ),
    "BESS_SIZING_GRID_LIMIT_VALUE": "Limite d'injection (MW)",
    "BESS_SIZING_DEGRAD_COST": "Cout degradation variable (EUR/MWh throughput)",
    "BESS_SIZING_AUX_LOSSES": "Pertes auxiliaires (MWh/h)",
    "BESS_SIZING_ECON_TAB_TITLE": "Detail CAPEX / OPEX",
    "BESS_SIZING_HELP_ECON_TAB": (
        "Hypotheses economiques modifiables par l'utilisateur. Si elles ne sont pas modifiees, "
        "les valeurs par defaut chargees depuis la configuration sont utilisees."
    ),
    "BESS_SIZING_ECON_TAB_NOTE": (
        "Ces hypotheses pilotent la recommandation techno-economique (methode du coude cout-revenu)."
    ),
    "BESS_SIZING_RESET_ECON_DEFAULTS": "Reinitialiser CAPEX/OPEX par defaut",

    "BESS_SIZING_MODE_SECTION_TITLE": "Mode d'analyse V2",
    "BESS_SIZING_HELP_ANALYSIS_MODES": (
        "Mode A: techno-economique avec vos CAPEX/OPEX. "
        "Mode B: techno-economique avec hypotheses par defaut. "
        "Mode C: optimisation marginale sans CAPEX/OPEX."
    ),
    "BESS_SIZING_MODE_SELECTOR": "Choisir le mode d'analyse",
    "BESS_SIZING_MODE_A_LABEL": "Mode A - CAPEX/OPEX utilisateur",
    "BESS_SIZING_MODE_B_LABEL": "Mode B - CAPEX/OPEX par defaut",
    "BESS_SIZING_MODE_C_LABEL": "Mode C - Optimisation marginale",
    "BESS_SIZING_MODE_B_WARNING": "Mode B: hypotheses economiques simplifiees chargees depuis le fichier de configuration.",
    "BESS_SIZING_TARGET_SHARE": "Part cible du gain brut maximal (%)",
    "BESS_SIZING_HELP_TARGET_SHARE": (
        "Le mode C recommande la plus petite configuration atteignant au moins cette part du gain brut maximal."
    ),
    "BESS_SIZING_CAPEX_POWER": "CAPEX puissance (EUR/kW)",
    "BESS_SIZING_CAPEX_ENERGY": "CAPEX energie (EUR/kWh)",
    "BESS_SIZING_CAPEX_FIXED": "CAPEX fixe (EUR)",
    "BESS_SIZING_OPEX_FIXED_PCT": "OPEX fixe (% CAPEX/an)",
    "BESS_SIZING_OPEX_FIXED": "OPEX fixe (EUR/an)",
    "BESS_SIZING_OPEX_VARIABLE": "OPEX variable (EUR/MWh throughput)",
    "BESS_SIZING_PROJECT_LIFE": "Duree de vie projet (ans)",
    "BESS_SIZING_DISCOUNT_RATE": "Taux d'actualisation",
    "BESS_SIZING_REPLACEMENT_ENABLED": "Activer un remplacement simplifie",
    "BESS_SIZING_REPLACEMENT_YEAR": "Annee de remplacement",
    "BESS_SIZING_REPLACEMENT_FRACTION": "Fraction CAPEX remplacee (0-1)",
    "BESS_SIZING_RECOMMEND_METRIC": "Critere de recommandation techno-economique",
    "BESS_SIZING_RECOMMEND_METRIC_MARGIN": "Marge nette annualisee max",
    "BESS_SIZING_RECOMMEND_METRIC_NPV": "VAN simplifiee max",
    "BESS_SIZING_RECOMMEND_METRIC_PAYBACK": "Temps de retour minimal",

    "BESS_SIZING_KPI_TECHNO_CONFIG": "Reco techno-economique",
    "BESS_SIZING_KPI_MARGINAL_CONFIG": "Reco marginale",
    "BESS_SIZING_KPI_GAIN_SHARE": "Part gain max (reco marginale)",
    "BESS_SIZING_KPI_GAIN_SHARE_OPTIMIZED": "Part gain max (config optimisee)",
    "BESS_SIZING_KPI_NET_MARGIN": "Marge nette (reco techno)",
    "BESS_SIZING_KEY_COMPARE_TITLE": "Comparaison des configurations cles",
    "BESS_SIZING_HELP_KEY_COMPARE": "Compare les configurations brute max, techno-economique et marginale sur les KPI principaux.",

    "BESS_SIZING_CHART_GAIN_SIZE_TITLE": "Gain brut vs taille batterie",
    "BESS_SIZING_HELP_GAIN_SIZE": "Courbe gain brut annuel en fonction de la taille (MWh). Permet d'observer les rendements decroissants.",
    "BESS_SIZING_CHART_NET_SIZE_TITLE": "Gain net vs taille batterie",
    "BESS_SIZING_HELP_NET_SIZE": "Courbe marge nette annualisee vs taille. Utilisee en modes A/B pour la recommandation economique.",
    "BESS_SIZING_CHART_MARGINAL_MW_TITLE": "Valeur marginale du MW additionnel",
    "BESS_SIZING_HELP_MARGINAL_MW": "Gain additionnel apporte par un MW de puissance supplementaire.",
    "BESS_SIZING_CHART_MARGINAL_MWH_TITLE": "Valeur marginale du MWh additionnel",
    "BESS_SIZING_HELP_MARGINAL_MWH": "Gain additionnel apporte par un MWh de capacite energetique supplementaire.",
    "BESS_SIZING_CHART_GAIN_SHARE_TITLE": "Part du gain maximal atteinte",
    "BESS_SIZING_HELP_GAIN_SHARE": "Mesure le compromis: combien de gain maximal est atteint pour une taille donnee.",
    "BESS_SIZING_CONCLUSIONS_TITLE": "Conclusions automatiques",
    "BESS_SIZING_HELP_CONCLUSIONS": "Conclusions deduites des KPI et des recommandations (brut, techno-eco, marginal).",
    "BESS_SIZING_NO_CONCLUSIONS": "Aucune conclusion automatique disponible.",
    "BESS_SIZING_GLOSSARY_TITLE": "Definitions et interpretations",
    "BESS_SIZING_HELP_GLOSSARY": "Glossaire des principales grandeurs utilisees dans l'analyse V2.",
    "BESS_SIZING_GLOSS_POWER": "Puissance batterie",
    "BESS_SIZING_DEF_POWER": "Puissance maximale de charge/decharge instantanee (MW).",
    "BESS_SIZING_GLOSS_ENERGY": "Capacite energetique nominale",
    "BESS_SIZING_DEF_ENERGY": "Energie stockable nominale de la batterie (MWh).",
    "BESS_SIZING_GLOSS_USABLE": "Capacite utile",
    "BESS_SIZING_DEF_USABLE": "Part exploitable entre SOC min et SOC max.",
    "BESS_SIZING_GLOSS_DURATION": "Duree de stockage",
    "BESS_SIZING_DEF_DURATION": "Rapport energie/puissance en heures (MWh/MW).",
    "BESS_SIZING_GLOSS_RTE": "Rendement aller-retour",
    "BESS_SIZING_DEF_RTE": "Produit des rendements de charge et de decharge.",
    "BESS_SIZING_GLOSS_SOC": "SOC min / max",
    "BESS_SIZING_DEF_SOC": "Bornes minimales et maximales de l'etat de charge de la batterie.",
    "BESS_SIZING_GLOSS_THROUGHPUT": "Throughput annuel",
    "BESS_SIZING_DEF_THROUGHPUT": "Somme des energies transitant par la batterie sur l'annee.",
    "BESS_SIZING_GLOSS_CYCLE": "Cycle equivalent complet",
    "BESS_SIZING_DEF_CYCLE": "Throughput annuel rapporte a 2 fois la capacite nominale.",
    "BESS_SIZING_GLOSS_GROSS": "Gain brut d'arbitrage",
    "BESS_SIZING_DEF_GROSS": "Delta de revenu marche entre PV seul et PV+BESS avant couts.",
    "BESS_SIZING_GLOSS_NET": "Revenu net annuel",
    "BESS_SIZING_DEF_NET": "Gain brut moins OPEX annuel (hors annualisation CAPEX).",
    "BESS_SIZING_GLOSS_ANNUALIZED": "Cout annualise",
    "BESS_SIZING_DEF_ANNUALIZED": "CAPEX annualise + OPEX annuel total.",
    "BESS_SIZING_GLOSS_MARGINAL_OPT": "Optimisation marginale",
    "BESS_SIZING_DEF_MARGINAL_OPT": "Recherche d'un compromis taille/valeur plutot qu'un maximum brut absolu.",
    "BESS_SIZING_GLOSS_MARGINAL_GAIN": "Gain marginal",
    "BESS_SIZING_DEF_MARGINAL_GAIN": "Valeur additionnelle obtenue par MW ou MWh supplementaire.",
    "BESS_SIZING_GLOSS_KNEE": "Point de coude",
    "BESS_SIZING_DEF_KNEE": "Zone ou la pente des gains diminue fortement avec la taille.",
    "BESS_SIZING_GLOSS_CAP_SAT": "Saturation de capacite",
    "BESS_SIZING_DEF_CAP_SAT": "Frequence d'atteinte des bornes SOC min/max.",
    "BESS_SIZING_GLOSS_PWR_SAT": "Saturation de puissance",
    "BESS_SIZING_DEF_PWR_SAT": "Frequence d'atteinte des limites de charge/decharge en MW.",
    "BESS_SIZING_GLOSS_UNDER_OVER": "Sous-utilisation / surdimensionnement",
    "BESS_SIZING_DEF_UNDER_OVER": "Indice indiquant qu'une partie de la capacite reste peu mobilisee.",

    "BESS_SIZING_HELP_INPUTS": (
        "Importez les 3 sources (PV, TMY, prix), puis verifiez les colonnes detectees. "
        "Le pas de calcul final est toujours horaire."
    ),
    "BESS_SIZING_HELP_PARAMS": (
        "Definit la grille de test MW x duree et les hypotheses batterie (SOC, rendement, solveur). "
        "Le screening compare automatiquement chaque combinaison."
    ),
    "BESS_SIZING_HELP_RUN": (
        "Lance un backtest annuel avec connaissance parfaite des prix de l'annee fournie. "
        "Le modele n'autorise pas la recharge reseau en V1."
    ),
    "BESS_SIZING_HELP_EXEC_SUMMARY": (
        "Affiche la meilleure configuration selon le gain annuel absolu et ses indicateurs clefs."
    ),
    "BESS_SIZING_HELP_TABLE": (
        "Compare toutes les configurations testees avec revenus, gains, capture price et usage batterie."
    ),
    "BESS_SIZING_HELP_CHARTS": (
        "Visualise la zone de performance (MW x h) et les tendances du gain selon puissance et duree."
    ),
    "BESS_SIZING_HELP_SCORE_MATRIX": (
        "Chaque cellule represente le gain annuel pour un couple puissance-duree. "
        "Les zones les plus elevees indiquent les dimensionnements les plus attractifs."
    ),
    "BESS_SIZING_HELP_GAIN_POWER": (
        "Courbe enveloppe du meilleur gain obtenu pour chaque niveau de puissance, "
        "toutes durees confondues."
    ),
    "BESS_SIZING_HELP_GAIN_DURATION": (
        "Courbe enveloppe du meilleur gain obtenu pour chaque duree, "
        "toutes puissances confondues."
    ),
    "BESS_SIZING_HELP_COMPARISON": (
        "Barres: revenu annuel. Ligne: capture price moyen. "
        "Permet de voir si le BESS augmente a la fois la valeur totale et la qualite temporelle de l'injection."
    ),
    "BESS_SIZING_HELP_CONFIG": (
        "Selectionnez une configuration pour analyser son dispatch horaire et ses performances detaillees."
    ),
    "BESS_SIZING_HELP_TIMESERIES": (
        "Lecture chronologique prix/PV/charge/decharge/SOC sur la periode choisie pour verifier le comportement. "
        "Convention signe du graphe: charge positive, decharge affichee negative pour distinguer visuellement les flux."
    ),
    "BESS_SIZING_HELP_HEATMAP": (
        "Montre le net dispatch moyen par mois et par heure. "
        "Valeur positive = decharge nette vers reseau, valeur negative = charge nette depuis PV."
    ),
    "BESS_SIZING_HELP_WARNINGS": (
        "Liste les alertes de preparation de donnees et d'alignement temporel. "
        "A verifier avant interpretation business."
    ),
    "BESS_SIZING_HELP_TMY": (
        "Controle simple de coherence entre signal PV et signal TMY associe (couverture et correlation). "
        "Indicateur informatif en V1."
    ),
    "BESS_SIZING_HELP_ASSUMPTIONS": (
        "Rappel des hypotheses de modelisation utilisees pendant le calcul (roles des series, solveur, contraintes)."
    ),
    "BESS_SIZING_HELP_EXPORT": (
        "Exportez la synthese multi-configurations et la serie temporelle detaillee de la configuration selectionnee."
    ),

    "BESS_SIZING_EXPORT_SUMMARY": "Exporter synthese configurations (CSV)",
    "BESS_SIZING_EXPORT_DETAIL": "Exporter serie temporelle configuration (CSV)",

    "BESS_SIZING_ERROR_NEED_PV": "Veuillez charger un fichier PV.",
    "BESS_SIZING_ERROR_NEED_TMY": "Veuillez charger un fichier TMY.",
    "BESS_SIZING_ERROR_NEED_MARKET_CSV": "Veuillez charger un fichier prix en mode CSV.",
    "BESS_SIZING_ERROR_NEED_DURATION": "Veuillez selectionner au moins une duree batterie.",
    "BESS_SIZING_ERROR_POWER_RANGE": "La puissance min doit etre inferieure ou egale a la puissance max.",
    "BESS_SIZING_ERROR_SOC_BOUNDS": "Les bornes SOC doivent respecter 0 <= SOC min < SOC max <= 1.",
    "BESS_SIZING_ERROR_SOC_INITIAL": "Le SOC initial doit etre compris entre SOC min et SOC max.",

    "HOURLY_TANPHI_SECTION_TITLE": "Approximate tan(phi) impact study",
    "HOURLY_HELP_TANPHI_APPROX_MD": (
        "Etude d'approximation d'ingenierie de l'impact tan(phi) (pas 0.01 de 0.25 a 0.35). "
        "Ce module ne remplace pas une vraie resimulation PVsyst."
    ),
    "HOURLY_TANPHI_METHOD_CARD": (
        "Approximation d'ingenierie: on suppose un onduleur modele en puissance apparente (kVA), "
        "avec effet amont sur la capacite active (cos(phi)) et effet aval sur les pertes de courant (~1/cos^2)."
    ),
    "HOURLY_TANPHI_PRECISION_WARNING": (
        "Pour un calcul plus fiable, exporter depuis PVsyst des variables detaillees, en particulier EacOhmL et IL_Pmax."
    ),
    "HOURLY_TANPHI_REF_ASSUMPTION_NOTE": "Hypothese appliquee: tan(phi)_ref = 0 faute d'information explicite dans le fichier horaire.",
    "HOURLY_TANPHI_MODE_LABEL": "Mode de calcul",
    "HOURLY_TANPHI_MODE_ENHANCED": "enhanced approximation",
    "HOURLY_TANPHI_MODE_FALLBACK": "fallback minimal",
    "HOURLY_TANPHI_RANGE_LABEL": "Plage etudiee",
    "HOURLY_TANPHI_REF_LABEL": "Reference",
    "HOURLY_TANPHI_REF_COS_LABEL": "Reference cos(phi)",
    "HOURLY_TANPHI_REF_SOURCE_LABEL": "Source reference tan(phi)",
    "HOURLY_TANPHI_REF_SOURCE_COMPUTED": "Calculee depuis EApGrid/EReGrid",
    "HOURLY_TANPHI_REF_SOURCE_ASSUMED": "Supposee: tan(phi)_ref = 0",
    "HOURLY_TANPHI_REF_ENERGY_LABEL": "E_Grid annuel estime (reference)",
    "HOURLY_TANPHI_REF_EGRDLIM_LABEL": "EGrdLim annuel de reference (propage)",
    "HOURLY_TANPHI_COL_OUT": "Colonne onduleur",
    "HOURLY_TANPHI_COL_GRID": "Colonne injection reseau",
    "HOURLY_TANPHI_TABLE_TITLE": "Synthese scenarios tan(phi)",
    "HOURLY_TANPHI_COL_TANPHI": "tan_phi",
    "HOURLY_TANPHI_COL_COSPHI": "cos_phi",
    "HOURLY_TANPHI_COL_MODE": "mode_used",
    "HOURLY_TANPHI_COL_ANN_EGRID": "annual_EGrid_est_MWh",
    "HOURLY_TANPHI_COL_DELTA_MWH": "delta_vs_ref_MWh",
    "HOURLY_TANPHI_COL_DELTA_PCT": "delta_vs_ref_pct",
    "HOURLY_TANPHI_COL_PDECL": "P_decl_opt_MW",
    "HOURLY_TANPHI_COL_PEAK_OUT": "peak_EOutInv_est_MW",
    "HOURLY_TANPHI_COL_PEAK_GRID": "peak_EGrid_est_MW",
    "HOURLY_TANPHI_COL_WARNINGS": "warnings",
    "HOURLY_TANPHI_CHART_LOSS_TITLE": "tan(phi) vs annual energy loss/gain",
    "HOURLY_TANPHI_Y_LOSS": "Perte d'energie annuelle (MWh, negatif = gain)",
    "HOURLY_TANPHI_CHART_PDECL_TITLE": "tan(phi) vs optimal declared MW",
    "HOURLY_TANPHI_Y_PDECL": "Optimal declared active power (MW)",
    "HOURLY_TANPHI_EXTREMES_TITLE": "Extremes tan(phi) 0.25 et 0.35",
    "HOURLY_TANPHI_025_PDECL": "tan(phi)=0.25 puissance optimale a declarer",
    "HOURLY_TANPHI_025_LOSS_MWH": "tan(phi)=0.25 perte annuelle due au facteur de charge",
    "HOURLY_TANPHI_025_LOSS_PCT": "tan(phi)=0.25 perte due au facteur de charge",
    "HOURLY_TANPHI_035_PDECL": "tan(phi)=0.35 puissance optimale a declarer",
    "HOURLY_TANPHI_035_LOSS_MWH": "tan(phi)=0.35 perte annuelle due au facteur de charge",
    "HOURLY_TANPHI_035_LOSS_PCT": "tan(phi)=0.35 perte due au facteur de charge",
    "HOURLY_TANPHI_SIGNED_NOTE": "Convention de signe: valeur positive = perte, valeur negative = gain potentiel.",
    "HOURLY_TANPHI_LIMITS_TITLE": "Limites et avertissements",
    "HOURLY_TANPHI_LIMIT_ENGINEERING": "Resultat fourni a titre d'engineering estimate (approximation), pas comme recalcul exact PVsyst.",
    "HOURLY_TANPHI_LIMIT_NO_DIRECT_COS_ON_EGRID": "Le modele n'applique jamais directement E_Grid_est = cos(phi) * E_Grid.",
    "HOURLY_TANPHI_LIMIT_RESIM_PVSYST": "Pour des decisions critiques, privilegier une vraie resimulation PVsyst avec variables detaillees.",
    "HOURLY_TANPHI_REF_COMPUTED_NOTE": "Reference calculee depuis les energies apparente/reactive exportees dans le fichier horaire.",
    "HOURLY_TANPHI_NOT_AVAILABLE": "Etude tan(phi) indisponible avec les colonnes actuelles.",
    "HOURLY_AVAIL_TANPHI_APPROX": "Approximation tan(phi)",
    "HOURLY_AVAIL_TANPHI_APPROX_DETAIL": "Necessite EOutInv et E_Grid, avec fiabilite accrue si EacOhmL et IL_Pmax sont presents.",
}



