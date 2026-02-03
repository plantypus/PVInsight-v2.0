# assets/i18n/en.py

TEXTS = {
    # =========================================================================
    # App (global)
    # =========================================================================
    "APP_PAGE_TITLE": "PVInsight",
    "APP_TITLE": "PVInsight — PVSyst Analysis",
    "APP_VERSION_LABEL": "Version",
    "APP_DESCRIPTION": (
        "Streamlit app (empty for now) designed to host analysis tools "
        "for PVSyst exports (hourly results, monthly summaries, PR, losses, etc.)."
    ),

    # =========================================================================
    # Navigation / Pages
    # =========================================================================
    "PAGE_HOME_TITLE": "Home",
    "PAGE_SETTINGS_TITLE": "Settings",
    "PAGE_EXIT_TITLE": "Exit",

    # Sidebar / common buttons
    "BTN_GO_HOME": "🏠 Home",
    "BTN_EXIT": "⛔ Exit",

    # =========================================================================
    # Language
    # =========================================================================
    "LANG_LABEL": "Language",
    "LANG_FR": "French",
    "LANG_EN": "English",

    # =========================================================================
    # Home page
    # =========================================================================
    "HOME_WELCOME": "Welcome",
    "HOME_TOOLS_TITLE": "Tools",
    "HOME_TOOLS_EMPTY": "No business tools yet (empty site).",
    "HOME_SETTINGS_SHORTCUT": "⚙️ Open settings",

    # =========================================================================
    # Settings page
    # =========================================================================
    "SETTINGS_TITLE": "Settings",
    "SETTINGS_SUBTITLE": "User settings and default parameters.",
    "SETTINGS_SECTION_UI": "Interface",
    "SETTINGS_RESET": "Reset to defaults",
    "SETTINGS_RESET_DONE": "Settings reset.",

    # =========================================================================
    # Exit page
    # =========================================================================
    "EXIT_TITLE": "Goodbye",
    "EXIT_TEXT": (
        "You can close this tab.\n\n"
        "Note: Streamlit cannot automatically close the browser tab."
    ),
    "EXIT_CLOSE_TAB": "You can close this tab.",
    "EXIT_CLOUD_NOTE": "On Streamlit Cloud, the app keeps running on the server side.",


    # =========================================================================
    # Tool placeholders (future)
    # =========================================================================
    "TOOL_PLACEHOLDER_TITLE": "Tool (placeholder)",
    "TOOL_PLACEHOLDER_DESC": "Empty business page, to be completed later.",
    
    "NAV_TOOLS_GROUP": "Tools",

    "TOOL_TEMPLATE_TITLE": "Tool template",
    "TOOL_TEMPLATE_DESC": "Standard example page (Inputs → Run → Results → Export) to validate the architecture.",

    "SECTION_INPUTS": "Inputs",
    "SECTION_RUN": "Run",
    "SECTION_RESULTS": "Results",
    "SECTION_EXPORT": "Export",

    # --- TMY analysis tool ---
    "TOOL_TMY_ANALYSIS_TITLE": "TMY file analysis",
    "TOOL_TMY_ANALYSIS_DESC": (
        "Analysis and report generation from a TMY weather file "
        "(PVSyst format). Statistics, data quality and annual irradiation."
    ),

    "TMY_UPLOAD_LABEL": "TMY file (PVSyst format)",
    "TMY_TARGET_IRR_UNIT": "Target irradiance unit",
    "TMY_ENERGY_UNIT": "Energy unit",
    "TMY_RESAMPLE_1H": "Resample sub-hourly data to 1h",

    "TMY_RUN_ANALYSIS": "Run analysis",
    "TMY_RUNNING": "Running analysis…",
    "TMY_DONE": "Analysis completed.",

    "TMY_SUMMARY": "Summary",
    "TMY_ENERGY": "Annual irradiation",
    "TMY_STATS": "Basic statistics",
    "TMY_WARNINGS": "Warnings",
    "TMY_OUTPUTS": "Generated files",

    "TMY_DOWNLOAD_PDF": "Download PDF report",
    "TMY_DOWNLOAD_LOG": "Download log file",
    "TMY_NO_ENERGY": "Annual irradiation could not be computed.",

    "TMY_TIMESTAMP_OUTPUTS": "Add timestamp to generated files",
    "TMY_NO_OUTPUTS_YET": "No outputs generated yet.",

    "TMY_TIMESTAMP_OUTPUTS": "Add timestamp to generated files",
    "TMY_NO_OUTPUTS_YET": "No results yet: click Run analysis.",

    "TMY_CURVES_TITLE": "Annual curves (interactive)",
    "TMY_DISTRIBUTIONS_TITLE": "Distributions (interactive)",

    "TMY_DATE": "Date",
    "TMY_COUNT": "Count",
    "TMY_VAR": "Variable",
    "TMY_VALUE": "Value",
    "TMY_UNIT": "Unit",

    "TMY_TEMP_LABEL": "Temperature",
    "TMY_GHI_NOT_AVAILABLE": "GHI not available.",
    "TMY_TEMP_NOT_AVAILABLE": "Temperature not available.",

    "TMY_GHI_DISTRIB_LABEL": "GHI – histogram (values > 0, 200-step bins)",
    "TMY_TEMP_DISTRIB_LABEL": "Temperature – histogram",
    "TMY_GHI_DISTRIB_EMPTY": "GHI distribution unavailable (no values > 0).",
    "TMY_TEMP_DISTRIB_EMPTY": "Temperature distribution unavailable.",

    # Hourly results analysis
  "TOOL_HOURLY_RESULTS_TITLE": "Hourly Results Analysis (PVSyst)",
  "TOOL_HOURLY_RESULTS_DESC": "Analyze a PVSyst hourly export and generate summaries + reports (Excel/PDF).",

  "HOURLY_UPLOAD_LABEL": "PVSyst file (Hourly results) — CSV/TXT",
  "HOURLY_TIMESTAMP_OUTPUTS": "Add timestamp to exports (prevents overwrite)",
  "HOURLY_THRESHOLD_COLUMN_LABEL": "Column used for threshold & distribution",
  "HOURLY_THRESHOLD_COLUMN_HELP": "Default: E_Grid. Threshold must be in the same unit as this column.",
  "HOURLY_THRESHOLD_VALUE_LABEL": "Threshold (same unit as column)",
  "HOURLY_THRESHOLD_VALUE_HELP": "Used by the Threshold study and the Distribution study.",

  "HOURLY_INPUTS_GUIDE_TITLE": "What are these inputs used for?",
  "HOURLY_INPUTS_GUIDE_THRESHOLD": "Threshold: computes hours and sum above threshold (monthly/seasonal + monthly share).",
  "HOURLY_INPUTS_GUIDE_DISTRIBUTION": "Distribution: bins production hours by ratio (vs annual maximum) on the selected column.",
  "HOURLY_INPUTS_GUIDE_CLIPPING": "Inverter clipping: requires EOutInv and IL_Pmax (otherwise marked unavailable).",

  "HOURLY_RUN": "Run",
  "HOURLY_RUNNING": "Running analysis…",
  "HOURLY_DONE": "Analysis completed.",
  "HOURLY_FAILED": "Analysis failed.",
  "HOURLY_NO_OUTPUTS_YET": "No results yet. Run the analysis.",

  "HOURLY_SUMMARY": "Summary",
  "HOURLY_SUMMARY_FILE": "File",
  "HOURLY_SUMMARY_PVSYST_VERSION": "PVSyst version",
  "HOURLY_SUMMARY_SIM_DATE": "Simulation date",
  "HOURLY_SUMMARY_PERIOD": "Covered period",
  "HOURLY_SUMMARY_ROWS": "Row count",
  "HOURLY_SUMMARY_COLUMNS": "Available columns",
  "HOURLY_SUMMARY_THRESHOLD": "Threshold",

  "HOURLY_TAB_GRAPHS": "Charts",
  "HOURLY_TAB_DISTRIBUTION": "Distribution & tables",

  "HOURLY_RESULTS_THRESHOLD": "Study: Threshold",
  "HOURLY_RESULTS_DISTRIBUTION": "Study: Distribution",
  "HOURLY_RESULTS_CLIPPING": "Study: Inverter clipping",

  "HOURLY_THRESHOLD_NOT_AVAILABLE": "Threshold study is unavailable (missing column).",
  "HOURLY_DISTRIBUTION_NOT_AVAILABLE": "Distribution study is unavailable (missing column).",
  "HOURLY_CLIPPING_NOT_AVAILABLE": "Clipping study is unavailable (missing columns).",
  "HOURLY_CLIPPING_NOT_RUN": "No clipping data.",

  "HOURLY_EMPTY": "No usable data.",
  "HOURLY_MISSING_COLUMNS": "Missing columns",
  "HOURLY_SUGGESTED_COLUMNS": "Similar columns (suggestions)",

  "HOURLY_THR_OPERATING_HOURS": "Operating hours (>0)",
  "HOURLY_THR_HOURS_ABOVE": "Hours above threshold",
  "HOURLY_THR_SHARE_ABOVE": "Share of operating time above threshold",
  "HOURLY_THR_SUM_ABOVE": "Sum above threshold",

  "HOURLY_CLIP_HOURS": "Clipping hours",
  "HOURLY_CLIP_PCT": "Clipping share (of potential)",
  "HOURLY_CLIP_ENERGY": "Clipped energy",

  "HOURLY_TABLE_THRESHOLD_MONTHLY": "Threshold — Monthly",
  "HOURLY_TABLE_THRESHOLD_SEASONAL": "Threshold — Seasonal",
  "HOURLY_COL_MONTH": "Month",
  "HOURLY_COL_SEASON": "Season",
  "HOURLY_COL_HOURS_ABOVE": "Hours above threshold",
  "HOURLY_COL_SUM_ABOVE": "Sum above threshold",
  "HOURLY_COL_CLASS": "Class",
  "HOURLY_COL_PCT_TIME": "Share of time",
  "HOURLY_COL_SUM": "Sum",

  "HOURLY_CHART_MONTHLY_HOURS": "Monthly — Hours above threshold",
  "HOURLY_CHART_MONTHLY_SHARE": "Monthly — Share above threshold",
  "HOURLY_CHART_CLIPPING_MONTHLY": "Monthly — Clipping share",
  "HOURLY_Y_HOURS": "Hours",
  "HOURLY_Y_PERCENT": "%",

  "HOURLY_GENERATE_EXCEL": "Generate Excel",
  "HOURLY_GENERATE_PDF": "Generate PDF",
  "HOURLY_GENERATE_LOG": "Generate log",
  "HOURLY_EXCEL_READY": "Excel ready.",
  "HOURLY_PDF_READY": "PDF ready.",
  "HOURLY_LOG_READY": "Log ready.",
  "HOURLY_NO_EXPORTS_YET": "No exports generated yet.",

  "HOURLY_DOWNLOAD_EXCEL": "Download Excel",
  "HOURLY_DOWNLOAD_PDF": "Download PDF",
  "HOURLY_DOWNLOAD_LOG": "Download log",

  "HOURLY_INPUTS_GUIDE_NIGHT": "Night disconnection: ignores negative values (grid import) in Threshold/Distribution while computing night consumption separately.",
  "HOURLY_NIGHT_DISCONNECT_LABEL": "Night disconnection (ignore negative import for Threshold/Distribution)",
  "HOURLY_NIGHT_DISCONNECT_HELP": "If enabled, negative values of the selected column are clamped to 0 for operating time, threshold and distribution. Night consumption is computed separately from raw negative values.",
  "HOURLY_SUMMARY_NIGHT_OPTION": "Night option",
  "HOURLY_NIGHT_DISCONNECT_ON": "Night disconnection enabled",
  "HOURLY_NIGHT_DISCONNECT_OFF": "Night disconnection disabled",

  "HOURLY_RESULTS_NIGHT": "Night consumption",
  "HOURLY_NIGHT_CONSUMPTION": "Night consumption",
  "HOURLY_NIGHT_HOURS": "Import hours",

  "HOURLY_CHART_NIGHT_IMPORT": "Monthly — night consumption",

  "HOURLY_GLOBAL_PRODUCTION_TITLE": "Global production",
  "HOURLY_GLOBAL_PROJECT": "Project",
  "HOURLY_GLOBAL_PROJECT_FILE": "Project file",
  "HOURLY_GLOBAL_VARIANT": "Variant",
  "HOURLY_GLOBAL_TIMESTEP": "Detected timestep",
  "HOURLY_GLOBAL_OPERATING_HOURS": "Operating hours",
  "HOURLY_GLOBAL_NET_PRODUCTION": "Net production (with import)",
  "HOURLY_GLOBAL_PRODUCTION_NO_IMPORT": "Production without import (negatives clamped to 0)",
  "HOURLY_GLOBAL_NIGHT_CONSUMPTION": "Night consumption (auxiliaries)",
  "HOURLY_GLOBAL_IMPORT_HOURS": "Import hours",

  "HOURLY_GLOBAL_PRODUCTION_TITLE": "Global production",
  "HOURLY_GLOBAL_NOT_AVAILABLE": "Global summary unavailable (missing column).",
  "HOURLY_GLOBAL_TIMESTEP_QUALITY": "Timestep quality",

  "HOURLY_GLOBAL_NET_PRODUCTION": "Net production (with import)",
  "HOURLY_GLOBAL_PRODUCTION_NO_IMPORT": "Production without import (negatives clamped to 0)",
  "HOURLY_GLOBAL_NIGHT_CONSUMPTION": "Night consumption (auxiliaries)",
  "HOURLY_GLOBAL_IMPORT_HOURS": "Import hours",

  "HOURLY_CHART_MONTHLY_ENERGY_ABOVE": "Monthly — energy above threshold",
  "HOURLY_Y_ENERGY_KWH": "Energy (kWh)",

  "HOURLY_COL_ENERGY_ABOVE_KWH": "Energy above threshold (kWh)",
  "HOURLY_COL_HOURS": "Hours",
  "HOURLY_COL_ENERGY_KWH": "Energy (kWh)",

  "HOURLY_THR_ENERGY_ABOVE": "Energy above threshold",

  "HOURLY_INPUTS_GUIDE_GRID_CAPACITY": "Grid capacity (optional): enables annual/monthly load factor calculation when available.",

  "HOURLY_GRID_CAPACITY_LABEL": "Grid capacity (kW) — optional",
  "HOURLY_GRID_CAPACITY_HELP": "Connection/injection capacity (kW). Leave empty if unknown.",
  "HOURLY_GRID_CAPACITY_PLACEHOLDER": "e.g. 3000",

  "HOURLY_GLOBAL_GRID_CAPACITY": "Grid capacity",
  "HOURLY_GLOBAL_GRID_CAPACITY_NONE": "Not provided",
  "HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR": "Annual load factor (grid)",
  "HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR_NONE": "Not computed (capacity not provided)",

  "HOURLY_RESULTS_GRID_LIMIT": "Study: Grid limitation",
  "HOURLY_GRID_LIMIT_NOT_AVAILABLE": "Grid limitation study unavailable (missing columns).",
  "HOURLY_CHART_GRID_LIMIT_LOST_KWH": "Grid limitation — lost energy (monthly)",
  "HOURLY_CHART_GRID_LIMIT_LOST_PCT": "Grid limitation — loss % (monthly)",
  "HOURLY_GRID_LOST_ENERGY": "Lost energy",
  "HOURLY_GRID_LOST_PCT": "Loss %",
  "HOURLY_GRID_HOURS_LIMITED": "Limited hours",
  "HOURLY_GRID_INJECTED": "Injected energy",
  "HOURLY_GRID_ANNUAL_LF": "Annual load factor",
  "HOURLY_GRID_ANNUAL_LF_NONE": "Not computed (capacity not provided)",
  "HOURLY_TABLE_GRID_LIMIT_MONTHLY": "Grid limitation — monthly",

  "HOURLY_RESULTS_LOAD_FACTOR": "Study: Grid load & quality",
  "HOURLY_LOAD_FACTOR_NOT_AVAILABLE": "Load & quality study unavailable (missing columns).",
  "HOURLY_CHART_COSPHI_MONTHLY": "cos(phi) — monthly",
  "HOURLY_CHART_SATURATION_DIST": "Apparent saturation — distribution",
  "HOURLY_Y_COSPHI": "cos(phi)",

  "HOURLY_LF_COSPHI": "cos(phi) (annual)",
  "HOURLY_LF_Q_SHARE": "Reactive share (annual)",
  "HOURLY_LF_ANNUAL_LF": "Annual load factor",
  "HOURLY_LF_ANNUAL_LF_NONE": "Not computed (capacity not provided)",
  "HOURLY_LF_NOT_AVAILABLE": "N/A",

  "HOURLY_TABLE_LOAD_FACTOR_MONTHLY": "Grid load & quality — monthly",
  "HOURLY_TABLE_SATURATION_DIST": "Apparent saturation — distribution",

  "HOURLY_LF_S_APPARENT": "Apparent (kWh equiv.)",
  "HOURLY_LF_Q_REACTIVE": "Reactive (kWh equiv.)",
  "HOURLY_LF_P_ACTIVE": "Active (kWh)",

  "HOURLY_HELP_BUTTON": "❓ Help",
  "HOURLY_HELP_LOAD_FACTOR_MD": (
    "**Grid load & quality**\n\n"
    "- **cos(φ) (annual)** ≈ *P / S*: active injected energy (kWh) divided by apparent energy (kVAh equivalent).\n"
    "- **Reactive share (annual)** ≈ *Q / S*: reactive energy (kvarh equivalent) relative to apparent.\n"
    "- **Annual load factor** (if capacity provided): *P / (Capacity × Total hours)*.\n\n"
    "⚠️ These are energy-based indicators (annual/monthly aggregates) and depend on exported PVSyst parameters."
  ),
  "HOURLY_HELP_GRID_LIMIT_MD": (
    "**Grid limitation**\n\n"
    "- **Lost energy**: integral of **EGrdLim** (kWh).\n"
    "- **Loss %**: Lost / (Injected + Lost).\n"
    "- **Limited hours**: number of steps with **EGrdLim > 0** (converted to hours using the detected timestep).\n"
    "- If a **grid capacity** is provided, an **annual load factor** can be computed."
  ),
  "HOURLY_HELP_THRESHOLD_MD": (
    "**Threshold**\n\n"
    "- Computes time and energy **above a threshold** on the selected column (e.g., E_Grid).\n"
    "- Outputs: hours above, energy above, share of operating time, and monthly/seasonal breakdown.\n"
    "- **Night disconnection** (if enabled): negative values are ignored for operating/threshold."
  ),

  "HOURLY_HELP_GRID_LIMIT_MD": (
    "**Study: Grid limitation**\n\n"
    "This study quantifies the impact of injection curtailment at the grid connection point.\n\n"
    "**Displayed indicators**\n\n"
    "- **Lost energy (kWh)**: energy that **could have been injected** but was curtailed due to grid limitation "
    "(from the PVSyst parameter **EGrdLim**). A higher value indicates a stronger grid constraint on injected production.\n\n"
    "- **Loss (%)**: share of lost energy relative to the **potential** energy at the grid:\n"
    "  `loss % = Lost energy / (Injected energy + Lost energy)`\n"
    "  → useful to compare different design variants, even if total production differs.\n\n"
    "- **Limited hours**: total duration (in hours) during which grid limitation was active.\n"
    "  Computed as the number of time steps where **EGrdLim > 0**, converted to hours using the detected timestep.\n"
    "  → indicates whether curtailment is **frequent** (many hours) or **occasional** (few hours).\n\n"
    "- **Annual load factor**: computed only if a **grid capacity (kW)** is provided.\n"
    "  Formula: `LF = Injected energy (kWh) / (Capacity (kW) × Total hours (h))`\n"
    "  → represents the average annual utilisation of the grid connection capacity.\n\n"
    "**How to interpret the example**\n\n"
    "- `931,524 kWh` lost and `3.53 %`: curtailment exists but remains moderate in relative terms.\n"
    "- `586 h`: grid limitation occurs over a non-negligible number of hours.\n"
    "- `17.12 %`: on an annual average, injected active power corresponds to ~17% of the grid capacity.\n\n"
    "⚠️ Results depend on the parameters exported from PVSyst and on the detected timestep."
  ),


    "TOOL_TMY_COMPARE_TITLE": "TMY Comparison",
    "TOOL_TMY_COMPARE_DESC": "Compare two TMY files (GHI/DNI/DHI/Temp) on a common hourly step (60 min) and analyze differences.",

    "TMY_COMPARE_UPLOAD_A": "TMY file A",
    "TMY_COMPARE_UPLOAD_B": "TMY file B",

    "TMY_COMPARE_TARGET_IRR_UNIT": "Target irradiance unit",
    "TMY_COMPARE_ENERGY_UNIT": "Energy unit (integration)",
    "TMY_COMPARE_RESAMPLE_1H": "Resample to 1h if sub-hourly",
    "TMY_COMPARE_THRESHOLD_MEAN_PCT": "Alert threshold (mean difference %)",

    "TMY_COMPARE_RUN": "Run",
    "TMY_COMPARE_RUNNING": "Running comparison…",
    "TMY_COMPARE_DONE": "Comparison completed.",
    "TMY_COMPARE_NEED_TWO_FILES": "Please select two TMY files (A and B).",

    "TMY_COMPARE_SUMMARY": "Summary",
    "TMY_COMPARE_ENERGY_FULL": "Annual irradiation (full files)",
    "TMY_COMPARE_METRICS": "Metrics (common period, hourly-aligned)",
    "TMY_COMPARE_NO_COMMON_VARS": "No common variables found (GHI/DNI/DHI/Temp...).",

    "TMY_COMPARE_PLOTS": "Plots",
    "TMY_COMPARE_NO_PLOTS": "No plots available (missing variables).",
    "TMY_COMPARE_VAR_BLOCK": "Variable: {var}",
    "TMY_COMPARE_DELTA": "Delta (A − B)",

    "TMY_COMPARE_FILE": "File",
    "TMY_COMPARE_DOWNLOAD_PDF": "Download PDF (comparison report)",
    "TMY_COMPARE_NO_OUTPUTS_YET": "No results yet. Run a comparison to generate a report.",

    "TMY_COMPARE_VAR_GHI": "Global horizontal irradiance (GHI)",
    "TMY_COMPARE_VAR_DNI": "Direct normal irradiance (DNI)",
    "TMY_COMPARE_VAR_DHI": "Diffuse horizontal irradiance (DHI)",
    "TMY_COMPARE_VAR_TEMP": "Ambient temperature",
    "TMY_COMPARE_VAR_WIND": "Wind speed",

    "TMY_COMPARE_COL_VARIABLE": "Variable",
    "TMY_COMPARE_COL_N": "Samples",
    "TMY_COMPARE_COL_MEAN_A": "Mean (A)",
    "TMY_COMPARE_COL_MEAN_B": "Mean (B)",
    "TMY_COMPARE_COL_BIAS": "Mean bias (A − B)",
    "TMY_COMPARE_COL_MAE": "Mean absolute error (MAE)",
    "TMY_COMPARE_COL_RMSE": "Root mean squared error (RMSE)",
    "TMY_COMPARE_COL_MEAN_PCT": "Mean relative diff (%)",
    "TMY_COMPARE_COL_MAX_PCT": "Max relative diff (%)",
    "TMY_COMPARE_COL_MAX_ABS": "Max absolute diff",

    "TMY_COMPARE_STEP_NATIVE_A": "Native time step (A)",
    "TMY_COMPARE_STEP_NATIVE_B": "Native time step (B)",
    "TMY_COMPARE_STEP_USED": "Time step used for comparison",
    "TMY_COMPARE_ALERT": "Alert",
}


