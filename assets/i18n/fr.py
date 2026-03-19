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
    "HOURLY_GRID_LOST_ENERGY": "Énergie perdue par bridage",
    "HOURLY_GRID_LOST_PCT": "Part perdue",
    "HOURLY_GRID_HOURS_LIMITED": "Durée bridée",
    "HOURLY_GRID_INJECTED": "Énergie injectée",
    "HOURLY_GRID_LIMIT_NOT_AVAILABLE": "Analyse de bridage réseau non disponible.",

    "HOURLY_LIMIT_COMPLEMENTARY_STUDY_TITLE": "Étude complémentaire de limitation",
    "HOURLY_THR_HOURS_ABOVE": "Durée au-dessus de la limite",
    "HOURLY_THR_SHARE_ABOVE": "Part du temps de fonctionnement au-dessus",
    "HOURLY_THR_ENERGY_ABOVE": "Énergie au-dessus de la limite",
    "HOURLY_THRESHOLD_NOT_AVAILABLE": "Étude de limitation non disponible.",

    "HOURLY_SECTION_LOAD_FACTOR_TITLE": "Analyse active / réactive réseau",
    "HOURLY_HELP_LOAD_FACTOR_MD": "Cette section présente les grandeurs active, réactive et apparente ainsi qu'un indicateur cos(phi) lorsque les colonnes nécessaires sont disponibles.",
    "HOURLY_LF_P_ACTIVE": "Énergie active",
    "HOURLY_LF_Q_REACTIVE": "Énergie réactive",
    "HOURLY_LF_S_APPARENT": "Énergie apparente",
    "HOURLY_LF_COSPHI": "cos(phi)",
    "HOURLY_LF_Q_SHARE": "Part réactive",
    "HOURLY_LOAD_FACTOR_ESTIMABLE": "La simulation active / réactive détaillée n'est pas présente dans le fichier, mais un impact potentiel pourra être estimé dans une évolution ultérieure.",
    "HOURLY_LOAD_FACTOR_NOT_AVAILABLE": "Analyse active / réactive non disponible.",

    "HOURLY_DETAILS_THRESHOLD_TITLE": "Détails de l'étude de limitation",
    "HOURLY_TABLE_THRESHOLD_MONTHLY": "Tableau mensuel de limitation",
    "HOURLY_COL_MONTH": "Mois",
    "HOURLY_COL_HOURS_ABOVE": "Heures au-dessus",
    "HOURLY_COL_ENERGY_ABOVE_KWH": "Énergie au-dessus (kWh)",
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
        "La recommandation de bridage s'appuie sur l'énergie au-dessus de la limite étudiée "
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
        "de sa valeur maximale observée sur ses heures productives, et la part d'énergie au-dessus "
        "de la limite reste limitée ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_CAUTION": (
        "Un bridage peut être envisagé avec prudence : la centrale fonctionne en moyenne à **{utilization_pct}** "
        "de sa valeur maximale observée sur ses heures productives, avec **{energy_above_pct}** d'énergie "
        "au-dessus de la limite étudiée."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_RECOMMENDED": (
        "Un bridage n'est pas particulièrement recommandé à ce niveau : la centrale fonctionne déjà à "
        "**{utilization_pct}** de sa valeur maximale observée sur ses heures productives ou la part d'énergie "
        "au-dessus de la limite devient significative ({energy_above_pct})."
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

    "HOURLY_GLOBAL_PR": "PR annuel moyen",

    "HOURLY_SYSTEM_SUMMARY_TITLE": "Synthèse système",
    "HOURLY_HELP_SYSTEM_SUMMARY_MD": (
        "Cette synthèse résume la production annuelle hors soutirage nocturne, les pertes de clipping, "
        "le soutirage, le bridage éventuel, l'état global du système et une recommandation de bridage. "
        "Critères d'état système : très peu contraint < 1 %, faiblement contraint de 1 à < 3 %, "
        "modérément contraint de 3 à < 6 %, fortement contraint ≥ 6 % de pertes totales rapportées "
        "à la production sans soutirage nocturne. La recommandation de bridage s'appuie sur l'énergie "
        "au-dessus de la limite étudiée et sur le taux moyen de fonctionnement sur heures productives, "
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
        "Le PR annuel moyen est de **{pr}**. "
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
        "et la part d'énergie au-dessus de la limite reste limitée ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_CAUTION": (
        "Un bridage peut être envisagé avec prudence : la centrale fonctionne en moyenne à **{utilization_pct}** "
        "de son niveau de haut fonctionnement habituel (P99) sur ses heures productives, "
        "avec **{energy_above_pct}** d'énergie au-dessus de la limite étudiée."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_RECOMMENDED": (
        "Un bridage n'est pas particulièrement recommandé à ce niveau : la centrale fonctionne déjà à "
        "**{utilization_pct}** de son niveau de haut fonctionnement habituel (P99) sur ses heures productives "
        "ou la part d'énergie au-dessus de la limite devient significative ({energy_above_pct})."
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
        "le PR calculé sur les seules heures de production positive, le productible spécifique si disponible, et E_Grid. "
        "Le ratio GlobEff / GlobInc représente la part de l'irradiation sur le plan capteurs qui reste effectivement exploitable "
        "après IAM et ombrage."
    ),
    "HOURLY_SYSTEM_SENTENCE_PERFORMANCE_NO_PRODUCTIBLE": (
        "Le PR annuel moyen est de **{pr}**."
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
        "Le PR annuel moyen est de **{pr}**. "
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


}
