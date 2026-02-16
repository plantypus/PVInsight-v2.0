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
