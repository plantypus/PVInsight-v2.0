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

    "HOURLY_HEATMAP_TITLE": "Grid injection heatmap (month × hour)",

    "HOURLY_HEATMAP_CAPTION": (
        "Average injected power P_grid (kW), "
        "computed from E_Grid and the time step Δt."
    ),

    "HOURLY_HEATMAP_MISSING_COLUMN": "Required column missing for heatmap",

    "HOURLY_HEATMAP_NOT_AVAILABLE": (
        "Heatmap unavailable: missing data or invalid datetime index."
    ),
    "HOURLY_HEATMAP_COLORBAR_TITLE_P_GRID": "Injected power (P_grid)",
    "HOURLY_HEATMAP_UNIT_KW": "kW",

#new keys i18n
    "HOURLY_TAB_MAIN_ANALYSIS": "Main analysis",
    "HOURLY_TAB_DETAILED_ANALYSIS": "Detailed analysis",

    "HOURLY_HELP_FILE_SUMMARY_MD": (
        "This section summarizes the main information from the analyzed hourly file: "
        "project identity, variant, PVsyst version, covered period, and timestep quality."
    ),
    "HOURLY_HELP_AVAILABLE_STUDIES_MD": (
        "This section indicates which studies are available based on the columns detected in the file "
        "and the analyses effectively computed."
    ),
    "HOURLY_HELP_GLOBAL_RESULTS_MD": (
        "This section presents the overall energy summary of the simulation: "
        "production, night import, operating hours, and annual load factor when available."
    ),
    "HOURLY_HELP_CLIPPING_MD": (
        "Inverter clipping corresponds to energy lost when the available DC power "
        "exceeds the conversion/injection capability of the inverters."
    ),
    "HOURLY_HELP_HEATMAP_MD": (
        "The heatmap shows the average production distribution by month and hour of day. "
        "It helps identify periods of high production."
    ),
    "HOURLY_HELP_POWER_DISTRIBUTION_MD": (
        "This table presents a simplified distribution of production using classes relative "
        "to the observed maximum."
    ),

    "HOURLY_SUMMARY_COLUMNS_EXPANDER": "Show column list",

    "HOURLY_AVAILABLE_STUDIES_TITLE": "Available studies",

    "HOURLY_AVAIL_STUDY": "Study",
    "HOURLY_AVAIL_STATUS": "Status",
    "HOURLY_AVAIL_DETAIL": "Detail",

    "HOURLY_STATUS_AVAILABLE": "Available",
    "HOURLY_STATUS_PARTIAL": "Partial",
    "HOURLY_STATUS_MISSING": "Not available",
    "HOURLY_STATUS_ESTIMABLE": "Estimable",

    "HOURLY_AVAIL_GLOBAL_RESULTS": "Global results",
    "HOURLY_AVAIL_GLOBAL_RESULTS_DETAIL": "Overall energy summary of the file.",
    "HOURLY_AVAIL_CLIPPING": "Inverter clipping",
    "HOURLY_AVAIL_CLIPPING_DETAIL": "IL_Pmax loss analysis if the required columns are present.",
    "HOURLY_AVAIL_HEATMAP": "Production heatmap",
    "HOURLY_AVAIL_HEATMAP_DETAIL": "Production visualization by month and hour.",
    "HOURLY_AVAIL_GRID_LIMIT_BASE": "Simulated base curtailment",
    "HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_YES": "The file contains EGrdLim: simulated base curtailment can be analyzed.",
    "HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_NO": "No simulated curtailment detected through EGrdLim.",
    "HOURLY_AVAIL_LIMIT_STUDY": "Complementary limit study",
    "HOURLY_AVAIL_LIMIT_STUDY_DETAIL": "User threshold analysis based on the selected production column.",
    "HOURLY_AVAIL_LOAD_FACTOR": "Active / reactive grid analysis",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_AVAILABLE": "Apparent and reactive columns are available in the file.",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_ESTIMABLE": "The dedicated simulation is not present, but an estimation could be considered.",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_MISSING": "The required columns are not available in the file.",

    "HOURLY_SECTION_CLIPPING_TITLE": "Inverter clipping",
    "HOURLY_CLIPPING_NOT_AVAILABLE": "Inverter clipping analysis not available.",
    "HOURLY_CLIP_ENERGY": "Clipping energy loss",
    "HOURLY_CLIP_PCT": "Clipping share",
    "HOURLY_CLIP_HOURS": "Clipping steps/occurrences",
    "HOURLY_CLIP_MAX_VALUE": "Maximum clipping value",
    "HOURLY_CHART_CLIPPING_MONTHLY": "Monthly inverter clipping losses",

    "HOURLY_SECTION_LIMIT_STUDY_TITLE": "Threshold / curtailment study",
    "HOURLY_LIMIT_CURRENT_STATE_TITLE": "Current simulation state",
    "HOURLY_LIMIT_COMPLEMENTARY_STUDY_TITLE": "Complementary limitation study",
    "HOURLY_LIMIT_METHOD": "Method",
    "HOURLY_LIMIT_METHOD_MEASURED": "Measured in file",
    "HOURLY_LIMIT_METHOD_ESTIMATED": "Estimated from provided capacity",

    "HOURLY_CHART_DURATION_CURVE_THRESHOLD": "Duration curve with threshold",
    "HOURLY_X_DURATION_RANK": "Rank",
    "HOURLY_Y_POWER_OR_ENERGY": "Value",

    "HOURLY_SECTION_LOAD_FACTOR_TITLE": "Active / reactive grid analysis",
    "HOURLY_LOAD_FACTOR_ESTIMABLE": (
        "The detailed active / reactive simulation is not present in the file, "
        "but a potential impact could be estimated in a future update."
    ),

    "HOURLY_DETAILS_THRESHOLD_TITLE": "Threshold study details",
    "HOURLY_DETAILS_GRID_LIMIT_TITLE": "Grid curtailment details",
    "HOURLY_DETAILS_LOAD_FACTOR_TITLE": "Active / reactive grid details",
    "HOURLY_DETAILS_POWER_DISTRIBUTION_TITLE": "Detailed power distribution",


    "TOOL_HOURLY_RESULTS_TITLE": "Hourly Results Analysis",
    "TOOL_HOURLY_RESULTS_DESC": "Analyze a PVsyst hourly file to summarize production, clipping, grid curtailment, and electrical indicators.",

    "SECTION_INPUTS": "Inputs",
    "SECTION_RUN": "Run",
    "SECTION_RESULTS": "Results",
    "SECTION_EXPORT": "Exports",

    "HOURLY_INPUTS_GUIDE_TITLE": "Parameter guide",
    "HOURLY_INPUTS_GUIDE_LIMIT_VALUE": "Define the analyzed column and the studied limit value for the complementary analysis.",
    "HOURLY_INPUTS_GUIDE_GRID_CAPACITY_REVISED": "Optionally provide a grid capacity to estimate curtailment if the file does not contain EGrdLim.",
    "HOURLY_INPUTS_GUIDE_CLIPPING": "Inverter clipping is analyzed automatically if the required columns are present.",
    "HOURLY_INPUTS_GUIDE_NIGHT": "The night disconnection option ignores negative values in some complementary analyses.",
    "HOURLY_INPUTS_GUIDE_LOAD_FACTOR": "The active / reactive analysis depends on the columns available in the file.",

    "HOURLY_UPLOAD_LABEL": "PVsyst hourly file (.csv, .txt)",
    "HOURLY_TIMESTAMP_OUTPUTS": "Add timestamp to exported files",

    "HOURLY_LIMIT_COLUMN_LABEL": "Column used for limit study",
    "HOURLY_LIMIT_COLUMN_HELP": "Column used for the complementary limit study. Default: E_Grid.",
    "HOURLY_LIMIT_VALUE_LABEL": "Studied limit value / power",
    "HOURLY_LIMIT_VALUE_HELP": "Value used to analyze the share of production above a chosen limit.",

    "HOURLY_NIGHT_DISCONNECT_LABEL": "Enable night disconnection",
    "HOURLY_NIGHT_DISCONNECT_HELP": "If enabled, negative values are ignored in some limit and distribution analyses. Night import is still computed separately.",

    "HOURLY_GRID_CAPACITY_LABEL_REVISED": "Grid capacity (optional)",
    "HOURLY_GRID_CAPACITY_HELP_REVISED": "Grid capacity used to estimate curtailment when the file does not already contain EGrdLim.",

    "HOURLY_RUN": "Run analysis",
    "HOURLY_RUNNING": "Running analysis…",
    "HOURLY_DONE": "Analysis completed.",
    "HOURLY_FAILED": "Analysis failed.",
    "HOURLY_NO_OUTPUTS_YET": "No results available yet.",

    "HOURLY_TAB_MAIN_ANALYSIS": "Main analysis",
    "HOURLY_TAB_DETAILED_ANALYSIS": "Detailed analysis",

    "HOURLY_SUMMARY": "Simulation summary",
    "HOURLY_HELP_FILE_SUMMARY_MD": "This section summarizes the main information from the analyzed hourly file: project, variant, PVsyst version, covered period, and timestep quality.",
    "HOURLY_SUMMARY_FILE": "File",
    "HOURLY_SUMMARY_PVSYST_VERSION": "PVsyst version",
    "HOURLY_SUMMARY_SIM_DATE": "Simulation date",
    "HOURLY_SUMMARY_PERIOD": "Period",
    "HOURLY_SUMMARY_ROWS": "Row count",
    "HOURLY_SUMMARY_COLUMNS": "Columns",
    "HOURLY_SUMMARY_COLUMNS_EXPANDER": "Show column list",
    "HOURLY_SUMMARY_NIGHT_OPTION": "Night option",

    "HOURLY_GLOBAL_PROJECT": "Project",
    "HOURLY_GLOBAL_PROJECT_FILE": "Project file",
    "HOURLY_GLOBAL_VARIANT": "Variant",
    "HOURLY_GLOBAL_TIMESTEP": "Timestep",
    "HOURLY_GLOBAL_TIMESTEP_QUALITY": "Timestep quality",
    "HOURLY_NIGHT_DISCONNECT_ON": "Night disconnection enabled",
    "HOURLY_NIGHT_DISCONNECT_OFF": "Night disconnection disabled",

    "HOURLY_AVAILABLE_STUDIES_TITLE": "Available studies",
    "HOURLY_HELP_AVAILABLE_STUDIES_MD": "This section indicates which studies are available depending on the detected columns and the analyses effectively computed.",
    "HOURLY_AVAIL_STUDY": "Study",
    "HOURLY_AVAIL_STATUS": "Status",
    "HOURLY_AVAIL_DETAIL": "Detail",
    "HOURLY_STATUS_AVAILABLE": "Available",
    "HOURLY_STATUS_PARTIAL": "Partial",
    "HOURLY_STATUS_MISSING": "Not available",
    "HOURLY_STATUS_ESTIMABLE": "Estimable",

    "HOURLY_AVAIL_GLOBAL_RESULTS": "Global results",
    "HOURLY_AVAIL_GLOBAL_RESULTS_DETAIL": "Overall energy summary of the file.",
    "HOURLY_AVAIL_CLIPPING": "Inverter clipping",
    "HOURLY_AVAIL_CLIPPING_DETAIL": "IL_Pmax loss analysis if the required columns are present.",
    "HOURLY_AVAIL_HEATMAP": "Production heatmap",
    "HOURLY_AVAIL_HEATMAP_DETAIL": "Production visualization by month and hour.",
    "HOURLY_AVAIL_GRID_LIMIT_BASE": "Simulated base curtailment",
    "HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_YES": "The file contains EGrdLim: simulated curtailment can be analyzed.",
    "HOURLY_AVAIL_GRID_LIMIT_BASE_DETAIL_NO": "No simulated curtailment detected through EGrdLim.",
    "HOURLY_AVAIL_LIMIT_STUDY": "Complementary limit study",
    "HOURLY_AVAIL_LIMIT_STUDY_DETAIL": "User-defined limit analysis based on the selected column.",
    "HOURLY_AVAIL_LOAD_FACTOR": "Active / reactive grid analysis",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_AVAILABLE": "Apparent and reactive columns are available in the file.",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_ESTIMABLE": "The dedicated simulation is not present, but an estimate could be considered.",
    "HOURLY_AVAIL_LOAD_FACTOR_DETAIL_MISSING": "The required columns are not available in the file.",

    "HOURLY_GLOBAL_PRODUCTION_TITLE": "Global results",
    "HOURLY_HELP_GLOBAL_RESULTS_MD": "This section presents the overall energy summary of the simulation: production, night import, operating hours, and annual load factor when available.",
    "HOURLY_GLOBAL_NOT_AVAILABLE": "Global results not available.",
    "HOURLY_MISSING_COLUMNS": "Missing columns",
    "HOURLY_SUGGESTED_COLUMNS": "Suggested columns",

    "HOURLY_GLOBAL_PRODUCTION_NO_IMPORT": "Production without import",
    "HOURLY_GLOBAL_NET_PRODUCTION": "Net production",
    "HOURLY_GLOBAL_NIGHT_CONSUMPTION": "Night import",
    "HOURLY_GLOBAL_OPERATING_HOURS": "Operating hours",
    "HOURLY_GLOBAL_IMPORT_HOURS": "Import hours",
    "HOURLY_GLOBAL_GRID_CAPACITY": "Grid capacity",
    "HOURLY_GLOBAL_GRID_CAPACITY_NONE": "Not provided",
    "HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR": "Annual load factor",
    "HOURLY_GLOBAL_ANNUAL_LOAD_FACTOR_NONE": "Not available",

    "HOURLY_SECTION_CLIPPING_TITLE": "Inverter clipping",
    "HOURLY_HELP_CLIPPING_MD": "Inverter clipping corresponds to energy lost when available power exceeds the inverter conversion capability. The displayed percentage is computed against inverter potential energy before clipping.",
    "HOURLY_CLIPPING_NOT_AVAILABLE": "Inverter clipping analysis not available.",
    "HOURLY_EMPTY": "No usable data.",
    "HOURLY_CLIP_ENERGY": "Clipping energy loss",
    "HOURLY_CLIP_PCT": "Clipping share",
    "HOURLY_CLIP_REFERENCE": "Percentage reference",
    "HOURLY_CLIP_HOURS": "Clipping duration",
    "HOURLY_CLIP_MAX_VALUE": "Maximum clipping value",
    "HOURLY_CLIP_REFERENCE_POTENTIAL_AC": "Relative to inverter potential energy before clipping",

    "HOURLY_HEATMAP_TITLE": "Production heatmap",
    "HOURLY_HELP_HEATMAP_MD": "The heatmap shows the average power distribution by month and hour of day. It is displayed in MW.",
    "HOURLY_HEATMAP_MISSING_COLUMN": "Missing column for heatmap",
    "HOURLY_HEATMAP_NOT_AVAILABLE": "Heatmap not available.",
    "HOURLY_HEATMAP_CAPTION_MW": "Heatmap of average power in MW by month and hour.",

    "HOURLY_SECTION_LIMIT_STUDY_TITLE": "Limit / curtailment study",
    "HOURLY_HELP_GRID_LIMIT_MD": "This section distinguishes curtailment already present in the simulation from the complementary study of a user-defined limit.",
    "HOURLY_LIMIT_CURRENT_STATE_TITLE": "Current simulation state",
    "HOURLY_LIMIT_METHOD": "Method",
    "HOURLY_LIMIT_METHOD_MEASURED": "Measured in file",
    "HOURLY_LIMIT_METHOD_ESTIMATED": "Estimated from provided capacity",
    "HOURLY_GRID_LOST_ENERGY": "Curtailment energy loss",
    "HOURLY_GRID_LOST_PCT": "Loss share",
    "HOURLY_GRID_HOURS_LIMITED": "Curtailed duration",
    "HOURLY_GRID_INJECTED": "Injected energy",
    "HOURLY_GRID_LIMIT_NOT_AVAILABLE": "Grid curtailment analysis not available.",

    "HOURLY_LIMIT_COMPLEMENTARY_STUDY_TITLE": "Complementary limit study",
    "HOURLY_THR_HOURS_ABOVE": "Duration above limit",
    "HOURLY_THR_SHARE_ABOVE": "Share of operating time above limit",
    "HOURLY_THR_ENERGY_ABOVE": "Energy above limit",
    "HOURLY_THRESHOLD_NOT_AVAILABLE": "Limit study not available.",

    "HOURLY_SECTION_LOAD_FACTOR_TITLE": "Active / reactive grid analysis",
    "HOURLY_HELP_LOAD_FACTOR_MD": "This section presents active, reactive, and apparent quantities as well as a cos(phi) indicator when the required columns are available.",
    "HOURLY_LF_P_ACTIVE": "Active energy",
    "HOURLY_LF_Q_REACTIVE": "Reactive energy",
    "HOURLY_LF_S_APPARENT": "Apparent energy",
    "HOURLY_LF_COSPHI": "cos(phi)",
    "HOURLY_LF_Q_SHARE": "Reactive share",
    "HOURLY_LOAD_FACTOR_ESTIMABLE": "The detailed active / reactive simulation is not present in the file, but a potential impact could be estimated in a future update.",
    "HOURLY_LOAD_FACTOR_NOT_AVAILABLE": "Active / reactive analysis not available.",

    "HOURLY_DETAILS_THRESHOLD_TITLE": "Limit study details",
    "HOURLY_TABLE_THRESHOLD_MONTHLY": "Monthly limit table",
    "HOURLY_COL_MONTH": "Month",
    "HOURLY_COL_HOURS_ABOVE": "Hours above",
    "HOURLY_COL_ENERGY_ABOVE_KWH": "Energy above (kWh)",
    "HOURLY_TABLE_THRESHOLD_SEASONAL": "Seasonal limit table",
    "HOURLY_COL_SEASON": "Season",

    "HOURLY_DETAILS_GRID_LIMIT_TITLE": "Grid curtailment details",
    "HOURLY_TABLE_GRID_LIMIT_MONTHLY": "Monthly grid curtailment table",

    "HOURLY_DETAILS_CLIPPING_TITLE": "Inverter clipping details",

    "HOURLY_DETAILS_LOAD_FACTOR_TITLE": "Active / reactive grid details",
    "HOURLY_TABLE_LOAD_FACTOR_MONTHLY": "Monthly active / reactive table",
    "HOURLY_TABLE_SATURATION_DIST": "Saturation distribution",
    "HOURLY_COL_CLASS": "Class",
    "HOURLY_COL_HOURS": "Hours",
    "HOURLY_COL_PCT_TIME": "Time share",

    "HOURLY_DETAILS_POWER_DISTRIBUTION_TITLE": "Detailed power distribution",
    "HOURLY_HELP_POWER_DISTRIBUTION_MD": "This table presents a simplified production distribution using classes relative to the observed maximum.",
    "HOURLY_DISTRIBUTION_NOT_AVAILABLE": "Power distribution not available.",
    "HOURLY_COL_ENERGY_KWH": "Energy (kWh)",

    "HOURLY_GENERATE_EXCEL": "Generate Excel export",
    "HOURLY_EXCEL_READY": "Excel export ready.",
    "HOURLY_GENERATE_PDF": "Generate PDF export",
    "HOURLY_PDF_READY": "PDF export ready.",
    "HOURLY_GENERATE_LOG": "Generate log",
    "HOURLY_LOG_READY": "Log ready.",
    "HOURLY_NO_EXPORTS_YET": "No exports generated yet.",
    "HOURLY_DOWNLOAD_EXCEL": "Download Excel",
    "HOURLY_DOWNLOAD_PDF": "Download PDF",
    "HOURLY_DOWNLOAD_LOG": "Download log",

    "HOURLY_SYSTEM_SUMMARY_TITLE": "System summary",
    "HOURLY_HELP_SYSTEM_SUMMARY_MD": (
        "This summary consolidates annual production excluding night import, clipping losses, "
        "night import, possible grid curtailment, the overall system state, and a curtailment recommendation. "
        "System state criteria: very low constraint < 1%, low constraint from 1 to < 3%, moderate constraint "
        "from 3 to < 6%, high constraint ≥ 6% of total losses relative to production excluding night import. "
        "The curtailment recommendation is based on energy above the studied limit and on the average operating "
        "rate during productive hours, computed relative to the maximum observed positive value."
    ),
    "HOURLY_SYSTEM_SENTENCE_GENERAL": "The plant produces **{prod_mwh}** MWh/year excluding night import.",
    "HOURLY_SYSTEM_SENTENCE_CLIP_NIGHT": (
        "Overpower losses amount to **{clip_mwh}** MWh/year, i.e. {clip_pct} of production excluding night import. "
        "Night import amounts to **{night_mwh}** MWh/year, i.e. {night_pct} of production excluding night import."
    ),
    "HOURLY_SYSTEM_SENTENCE_GRID": (
        "A grid curtailment is also present in the simulation, with **{grid_mwh}** MWh/year lost, "
        "i.e. {grid_pct} of production excluding night import."
    ),
    "HOURLY_SYSTEM_SENTENCE_STATE": "Overall, the plant shows a **{state}** operating state.",
    "HOURLY_SYSTEM_STATE_VERY_LOW_CONSTRAINT": "very low constraint",
    "HOURLY_SYSTEM_STATE_LOW_CONSTRAINT": "low constraint",
    "HOURLY_SYSTEM_STATE_MODERATE_CONSTRAINT": "moderate constraint",
    "HOURLY_SYSTEM_STATE_HIGH_CONSTRAINT": "high constraint",
    "HOURLY_BRIDGING_RECOMMENDATION_FAVORABLE": (
        "Curtailment appears feasible: the plant operates on average at {utilization_pct} "
        "of its maximum observed value during productive hours, and the share of energy above "
        "the studied limit remains low ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_CAUTION": (
        "Curtailment may be considered with caution: the plant operates on average at {utilization_pct} "
        "of its maximum observed value during productive hours, with {energy_above_pct} of energy "
        "above the studied limit."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_RECOMMENDED": (
        "Curtailment is not especially recommended at this level: the plant already operates at "
        "{utilization_pct} of its maximum observed value during productive hours or the share of "
        "energy above the studied limit becomes significant ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_AVAILABLE": (
        "No curtailment recommendation is available until a relevant studied limit is defined."
    ),
    "HOURLY_CLIP_PCT_PRIMARY": "Clipping share / production excluding night import",
    "HOURLY_CLIP_REFERENCE_PRIMARY": "Primary reference",
    "HOURLY_CLIP_PCT_SECONDARY": "Clipping share / potential energy",
    "HOURLY_CLIP_REFERENCE_SECONDARY": "Secondary reference",
    "HOURLY_CLIP_REFERENCE_PROD_WO_NIGHT": "Relative to production excluding night import",
    "HOURLY_CLIP_REFERENCE_POTENTIAL_AC": "Relative to potential energy before clipping",
    "HOURLY_UTILIZATION_REFERENCE_MAX_OBSERVED": "Maximum observed positive value",

    "HOURLY_AVAIL_PERFORMANCE": "Monthly performance",
    "HOURLY_AVAIL_PERFORMANCE_DETAIL": "Monthly performance table with irradiation, PR, specific yield, and E_Grid.",

    "HOURLY_GLOBAL_PR": "Annual mean PR",

    "HOURLY_SYSTEM_SUMMARY_TITLE": "System summary",
    "HOURLY_HELP_SYSTEM_SUMMARY_MD": (
        "This summary consolidates annual production excluding night import, clipping losses, "
        "night import, possible grid curtailment, the overall system state, and a curtailment recommendation. "
        "System state criteria: very low constraint < 1%, low constraint from 1 to < 3%, moderate constraint "
        "from 3 to < 6%, high constraint ≥ 6% of total losses relative to production excluding night import. "
        "The curtailment recommendation is based on energy above the studied limit and on the average operating "
        "rate during productive hours, computed relative to the P99 percentile of observed positive values."
    ),
    "HOURLY_SYSTEM_SENTENCE_GENERAL": "The plant produces **{prod_mwh}** MWh/year excluding night import.",
    "HOURLY_SYSTEM_SENTENCE_CLIP_NIGHT": (
        "Overpower losses amount to **{clip_mwh}** MWh/year, i.e. {clip_pct} of production excluding night import. "
        "Night import amounts to **{night_mwh}** MWh/year, i.e. {night_pct} of production excluding night import."
    ),
    "HOURLY_SYSTEM_SENTENCE_GRID": (
        "A grid curtailment is also present in the simulation, with **{grid_mwh}** MWh/year lost, "
        "i.e. {grid_pct} of production excluding night import."
    ),
    "HOURLY_SYSTEM_SENTENCE_METEO": (
        "The site shows a {meteo} solar resource over the simulated period. "
        "Effective irradiation represents **{globeff_ratio}** of incident irradiation, "
        "indicating **{optics}** optical and/or shading losses."
    ),
    "HOURLY_SYSTEM_SENTENCE_PERFORMANCE": (
        "Annual mean PR is **{pr}**. "
        "Specific yield reaches **{productible}** kWh/kWc/year when the data is available."
    ),
    "HOURLY_SYSTEM_SENTENCE_STATE": "Overall, the plant shows a **{state}** operating state.",

    "HOURLY_SYSTEM_STATE_VERY_LOW_CONSTRAINT": "very low constraint",
    "HOURLY_SYSTEM_STATE_LOW_CONSTRAINT": "low constraint",
    "HOURLY_SYSTEM_STATE_MODERATE_CONSTRAINT": "moderate constraint",
    "HOURLY_SYSTEM_STATE_HIGH_CONSTRAINT": "high constraint",

    "HOURLY_METEO_MODEST": "moderate",
    "HOURLY_METEO_GOOD": "good",
    "HOURLY_METEO_VERY_GOOD": "very good",

    "HOURLY_OPTICS_LOW_LOSSES": "low",
    "HOURLY_OPTICS_MODERATE_LOSSES": "moderate",
    "HOURLY_OPTICS_MARKED_LOSSES": "marked",

    "HOURLY_BRIDGING_RECOMMENDATION_FAVORABLE": (
        "Curtailment appears feasible: the plant operates on average at {utilization_pct} "
        "of its usual high operating level (P99) during productive hours, and the share of energy "
        "above the studied limit remains low ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_CAUTION": (
        "Curtailment may be considered with caution: the plant operates on average at {utilization_pct} "
        "of its usual high operating level (P99) during productive hours, with {energy_above_pct} of "
        "energy above the studied limit."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_RECOMMENDED": (
        "Curtailment is not especially recommended at this level: the plant already operates at "
        "{utilization_pct} of its usual high operating level (P99) during productive hours or the share "
        "of energy above the studied limit becomes significant ({energy_above_pct})."
    ),
    "HOURLY_BRIDGING_RECOMMENDATION_NOT_AVAILABLE": (
        "No curtailment recommendation is available until a relevant studied limit is defined."
    ),

    "HOURLY_CLIP_PCT_PRIMARY": "Clipping share / production excluding night import",
    "HOURLY_CLIP_REFERENCE_PRIMARY": "Primary reference",
    "HOURLY_CLIP_PCT_SECONDARY": "Clipping share / potential energy",
    "HOURLY_CLIP_REFERENCE_SECONDARY": "Secondary reference",
    "HOURLY_CLIP_REFERENCE_PROD_WO_NIGHT": "Relative to production excluding night import",
    "HOURLY_CLIP_REFERENCE_POTENTIAL_AC": "Relative to potential energy before clipping",

    "HOURLY_PERFORMANCE_MONTHLY_TITLE": "Monthly performance",
    "HOURLY_HELP_PERFORMANCE_MONTHLY_MD": (
        "This table consolidates by month incident irradiation, effective irradiation, the GlobEff/GlobInc ratio, "
        "PR, specific yield when available, and E_Grid. The last row provides an annual summary."
    ),
    "HOURLY_DETAILS_PERFORMANCE_TITLE": "Monthly performance details",

    "HOURLY_COL_GLOBINC": "GlobInc (kWh/m²)",
    "HOURLY_COL_GLOBEFF": "GlobEff (kWh/m²)",
    "HOURLY_COL_GLOBEFF_RATIO": "GlobEff / GlobInc",
    "HOURLY_COL_PR": "PR",
    "HOURLY_COL_PRODUCTIBLE": "Specific Yield (kWh/kWc)",
    "HOURLY_COL_EGRID_MWH": "E_Grid (MWh)",

    "HOURLY_UTILIZATION_REFERENCE_P99": "P99 percentile of positive values",

    "HOURLY_COL_GLOBHOR": "GlobHor (kWh/m²)",
    "HOURLY_COL_TILT_GAIN": "Tilt gain",
    "HOURLY_HELP_PERFORMANCE_MONTHLY_MD": (
        "This table consolidates monthly horizontal irradiation (GlobHor), irradiation in the plane of array (GlobInc), "
        "effective irradiation (GlobEff), tilt gain (GlobInc / GlobHor), optical ratio (GlobEff / GlobInc), "
        "PR computed only over positive-production hours, specific yield when available, and E_Grid. "
        "The GlobEff / GlobInc ratio represents the share of irradiation in the plane of array that remains effectively usable "
        "after IAM and shading."
    ),
    "HOURLY_SYSTEM_SENTENCE_PERFORMANCE_WITH_PRODUCTIBLE": (
        "Annual mean PR is **{pr}**. "
        "Specific yield reaches **{productible}** kWh/kWc/year."
    ),
    "HOURLY_SYSTEM_SENTENCE_PERFORMANCE_NO_PRODUCTIBLE": (
        "Annual mean PR is {pr}."
    ),
    "HOURLY_SYSTEM_SENTENCE_OPTICS": (
        "Tilt-related gain reaches {tilt_gain} between the horizontal plane and the plane of array. "
        "Remaining optical efficiency after IAM and shading is {optical_efficiency}."
    ),
    "HOURLY_SYSTEM_SENTENCE_UTILIZATION": (
        "The mean operating rate during productive hours is {utilization_pct}, "
        "computed relative to {ref_label}."
    ),
    "HOURLY_UTILIZATION_REFERENCE_P99": "the P99 percentile of positive power values",
    "HOURLY_DCAC_RECOMMENDATION_RELEVANT": (
        "A DC/AC ratio review appears relevant: clipping losses remain very low and "
        "the plant operating level stays moderate during productive hours."
    ),
    "HOURLY_DCAC_RECOMMENDATION_POSSIBLE": (
        "A DC/AC ratio review may be considered: the plant appears weakly constrained by clipping "
        "and its operating level remains relatively limited."
    ),
    "HOURLY_DCAC_RECOMMENDATION_NOT_PRIORITY": (
        "A DC/AC ratio review does not appear to be a priority at this stage."
    ),
    "HOURLY_DCAC_RECOMMENDATION_NOT_AVAILABLE": (
        "No specific conclusion is available regarding the DC/AC ratio."
    ),

    "HOURLY_SYSTEM_SENTENCE_OPTICS_FULL": (
        "Tilt-related gain reaches {tilt_gain} between the horizontal plane and the plane of array. "
        "Remaining optical efficiency after IAM and shading is {optical_efficiency}."
    ),
    "HOURLY_SYSTEM_SENTENCE_OPTICS_ONLY": (
        "Remaining optical efficiency after IAM and shading is {optical_efficiency}."
    ),

    # TMY compare
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

  # --- Compare PAN vs Datasheet ---
  "COMPARE_PAN_DS_TITLE": "PAN vs Datasheet Comparison",
  "COMPARE_PAN_DS_DESC": "Compares STC electrical values and selected mechanical characteristics between a PVsyst module file (.PAN) and a manufacturer datasheet (PDF).",

  "COMPARE_PAN_DS_INPUTS_HELP": "1) Select a manufacturer (defines the PDF reader). 2) Upload a .PAN file and a datasheet PDF. 3) Run the comparison.",

  "COMPARE_PAN_DS_MFR_SELECT": "Manufacturer (datasheet)",
  "COMPARE_PAN_DS_MFR_HELP": "The selected manufacturer determines which PDF reader will be used in the core module.",
  "COMPARE_PAN_DS_MFR_JINKO": "Jinko Solar",
  "COMPARE_PAN_DS_MFR_DMEGC": "DMEGC",
  "COMPARE_PAN_DS_MFR_ASTRONERGY": "Astronergy",
  "COMPARE_PAN_DS_MFR_DAS_SOLAR": "DAS Solar",
  "COMPARE_PAN_DS_MFR_CANADIAN_SOLAR": "Canadian Solar",

  "COMPARE_PAN_DS_UPLOAD_PAN": "PVsyst file (.PAN)",
  "COMPARE_PAN_DS_UPLOAD_DS": "Manufacturer datasheet (PDF)",

  "COMPARE_PAN_DS_CLEANUP_TMP": "Delete temporary files",
  "COMPARE_PAN_DS_CLEANUP_TMP_HELP": "If enabled, the PDF written to disk for parsing may be deleted after parsing (useful for stateless runs).",

  "COMPARE_PAN_DS_RUN": "Run comparison",
  "COMPARE_PAN_DS_RUNNING": "Running comparison…",
  "COMPARE_PAN_DS_DONE": "Comparison completed.",
  "COMPARE_PAN_DS_ERROR": "Error while comparing.",
  "COMPARE_PAN_DS_NEED_FILES": "Please provide both a .PAN file and a datasheet PDF.",

  "COMPARE_PAN_DS_WARNINGS_TITLE": "Warnings",
  "COMPARE_PAN_DS_SUMMARY_TITLE": "Summary",
  "COMPARE_PAN_DS_SUM_MANUFACTURER": "Manufacturer (code)",
  "COMPARE_PAN_DS_SUM_PAN_MODEL": "Model (PAN)",
  "COMPARE_PAN_DS_SUM_DS_MODEL": "Model (datasheet)",
  "COMPARE_PAN_DS_SUM_PICK_MODE": "Variant selection (mode)",
  "COMPARE_PAN_DS_SUM_FIELDS": "Number of fields",
  "COMPARE_PAN_DS_SUM_OK": "OK fields",
  "COMPARE_PAN_DS_SUM_WARN": "Out-of-tolerance fields",
  "COMPARE_PAN_DS_SUM_MISSING": "Missing fields",

  "COMPARE_PAN_DS_TABLE_TITLE": "Comparison details",
  "COMPARE_PAN_DS_NO_ROWS": "No comparison rows available.",
  "COMPARE_PAN_DS_NO_OUTPUTS_YET": "No results yet.",

  "COMPARE_PAN_DS_COL_LABEL": "Parameter",
  "COMPARE_PAN_DS_COL_UNIT": "Unit",
  "COMPARE_PAN_DS_COL_PAN": "PAN",
  "COMPARE_PAN_DS_COL_DS": "Datasheet",
  "COMPARE_PAN_DS_COL_DABS": "Abs Δ",
  "COMPARE_PAN_DS_COL_DPCT": "Δ %",
  "COMPARE_PAN_DS_COL_STATUS": "Status",
  "COMPARE_PAN_DS_COL_TOL_ABS": "Abs tolerance",
  "COMPARE_PAN_DS_COL_TOL_PCT": "Tolerance %",
  
  # --- Compare PAN vs Datasheet (IAM + Exports + Generalities + Project) ---

  "COMPARE_PAN_DS_GENERALITIES_TITLE": "General information",
  "COMPARE_PAN_DS_GEN_DATE": "Analysis date",
  "COMPARE_PAN_DS_GEN_MFR": "Selected manufacturer",
  "COMPARE_PAN_DS_GEN_PAN_FILE": "PAN file",
  "COMPARE_PAN_DS_GEN_DS_FILE": "Datasheet file",
  "COMPARE_PAN_DS_GEN_PAN_MODEL": "PAN model",
  "COMPARE_PAN_DS_GEN_PAN_POWER": "PAN power (W)",
  "COMPARE_PAN_DS_GEN_DS_VARIANT": "Datasheet variant",
  "COMPARE_PAN_DS_GEN_DS_POWER": "Datasheet power (W)",

  "COMPARE_PAN_DS_PROJECT_EXPANDER": "Project information (optional – included in PDF report)",
  "COMPARE_PAN_DS_PROJECT_NAME": "Project name",
  "COMPARE_PAN_DS_PROJECT_NO": "Project number",
  "COMPARE_PAN_DS_SOLAR_ENGINEER": "Solar engineer",

  "COMPARE_PAN_DS_GRAPHS_TITLE": "Graphs",
  "COMPARE_PAN_DS_IAM_NOT_AVAILABLE": "IAM profile not available in the PAN file.",
  "COMPARE_PAN_DS_IAM_MODE": "IAM mode",
  "COMPARE_PAN_DS_IAM_PROFILE": "Profile name",
  "COMPARE_PAN_DS_IAM_TYPE": "Profile type",
  "COMPARE_PAN_DS_IAM_X": "Incidence angle (°)",
  "COMPARE_PAN_DS_IAM_Y": "IAM factor",
  "COMPARE_PAN_DS_IAM_LOSS": "IAM losses (%)",
  "COMPARE_PAN_DS_IAM_TABLE_TITLE": "IAM profile table",
  "COMPARE_PAN_DS_IAM_COL_ANGLE": "Angle (°)",
  "COMPARE_PAN_DS_IAM_COL_IAM": "IAM",
  "COMPARE_PAN_DS_IAM_COL_LOSS": "Losses (%)",
  "COMPARE_PAN_DS_IAM_WARNINGS_TITLE": "IAM warnings",
  "COMPARE_PAN_DS_IAM_STATS_TITLE": "IAM diagnostics",

  "COMPARE_PAN_DS_COMPARE_SKIPPED": "Comparison disabled: model (brand / power) does not strictly match.",
  "COMPARE_PAN_DS_AVAILABLE_VARIANTS": "Available datasheet variants (for diagnostics)",

  "COMPARE_PAN_DS_COL_SECTION": "Section",
  "COMPARE_PAN_DS_COL_LABEL": "Parameter",
  "COMPARE_PAN_DS_COL_UNIT": "Unit",
  "COMPARE_PAN_DS_COL_DS": "Datasheet",
  "COMPARE_PAN_DS_COL_PAN": "PAN",
  "COMPARE_PAN_DS_COL_DABS": "Absolute deviation",
  "COMPARE_PAN_DS_COL_DPCT": "Deviation (%)",
  "COMPARE_PAN_DS_COL_STATUS": "Status",
  "COMPARE_PAN_DS_COL_TOL_ABS": "Abs. tolerance",
  "COMPARE_PAN_DS_COL_TOL_PCT": "% tolerance",

  "COMPARE_PAN_DS_NO_OUTPUTS_YET": "No results yet. Run the analysis to generate a report.",
  "COMPARE_PAN_DS_DOWNLOAD_PDF": "Download PDF report",
  "COMPARE_PAN_DS_DOWNLOAD_LOG": "Download log file (text)",
  "COMPARE_PAN_DS_EXPORTS_READY": "Exports are available below (PDF / log).",

  # --- Compare PAN vs Datasheet (UI/Help additions) ---

  "COMPARE_PAN_DS_TIMESTAMP_OUTPUTS": "Add timestamp to exports",
  "COMPARE_PAN_DS_RUN_HELP": "Run the PAN vs datasheet analysis and generate a PDF report + a log file.",
  "COMPARE_PAN_DS_EXPORT_TITLE": "Exports",

  "COMPARE_PAN_DS_HELP_GENERALITIES": (
      "Traceability and identification summary: analysis date, selected manufacturer, "
      "input files, model and power. Prevents comparing different PV module models."
  ),

  "COMPARE_PAN_DS_HELP_COMPARISON": (
      "Strict comparison of key parameters that drive module performance versus irradiance "
      "(STC points, temperature coefficients, bifaciality, Rshunt). "
      "High deviation (%) usually indicates model mismatch or inconsistent parameterization."
  ),

  "COMPARE_PAN_DS_HELP_IAM": (
      "The IAM profile (Incidence Angle Modifier) represents optical losses when light hits the module "
      "at non-normal angles. As incidence angle increases, IAM decreases → IAM losses increase. "
      "This affects energy yield in the morning/evening and during winter."
  ),

  "COMPARE_PAN_DS_HELP_EXPORTS": (
      "Download the PDF report and the text log generated during the last run."
  ),

  # --- Compare PAN vs Datasheet — Electrical explainer ---

  "COMPARE_PAN_DS_ELEC_EXPLAINER_TITLE": "Understanding electrical parameters",
  "COMPARE_PAN_DS_ELEC_EXPLAINER_SECION" : "Technical explanations",

  "COMPARE_PAN_DS_ELEC_EXPLAINER_TEXT": """
  Understanding PV Module Electrical Parameters

  ---

  ## 🔹 STC Data (Standard Test Conditions)

  STC = 1000 W/m², 25°C cell temperature.

  ### Isc – Short-circuit current

  - Maximum current delivered at given irradiance.
  - Increases almost linearly with irradiance.
  - Slightly increases with temperature (α > 0).
  - Mainly irradiance-driven parameter.

  ---

  ### Voc – Open-circuit voltage

  - Maximum voltage without load.
  - Decreases when temperature increases (β < 0).
  - Critical for string design (overvoltage risk in cold conditions).

  ---

  ### Vmpp & Impp – Maximum power point

  - Define the optimal operating point.
  - Vmpp decreases with temperature.
  - Impp slightly increases with irradiance.
  - Their product gives Pmax.

  ---

  ## 🔹 Temperature coefficients

  These parameters describe module sensitivity to cell temperature.

  ### α – Isc temperature coefficient (%/°C)

  - Usually small and positive (~ +0.04 to +0.06 %/°C).
  - Limited impact on total power.

  ### β – Voc temperature coefficient (%/°C)

  - Always negative (~ −0.25 to −0.35 %/°C).
  - Significant impact in hot climates.

  ### γ – Pmax temperature coefficient (%/°C)

  - Most important thermal parameter.
  - Typically between −0.28 and −0.35 %/°C.
  - Example: -0.30 %/°C → +20°C → -6% power.

  ### μIsc (mA/°C) & μVoc (mV/°C)

  - Absolute versions of the above coefficients.
  - Useful to verify internal consistency between absolute and percentage values.

  ---

  ## 🔹 RShunt – Shunt Resistance

  RShunt represents internal leakage paths inside the solar cell.

  - Higher RShunt → lower leakage → better low-irradiance performance.
  - Low RShunt → degraded I/V curve at low voltage.
  - Strong impact under diffuse and low irradiance conditions.

  ### Default PVsyst formula:

  Rshunt = Vmpp / (0.2 × (Isc − Impp))

  where:
  - Vmpp = voltage at maximum power
  - Isc = short-circuit current
  - Impp = current at maximum power

  The 0.2 factor is an empirical approximation of the differential conductance near MPP.

  This value is estimated from STC data only.
  The PAN file may contain an optimized value derived from the one-diode model.

  ---

  ## 🔹 IAM – Incidence Angle Modifier

  IAM describes optical losses due to angle of incidence.

  - IAM = 1 → normal incidence.
  - IAM < 1 → optical losses.
  - Strong impact in morning, evening and winter.

  Even with identical STC data, an unfavorable IAM profile reduces annual yield.

  ---

  ## 🔹 Bifaciality

  - Ratio of rear-side to front-side power.
  - Factor 0.7 → 70% rear performance.
  - Critical parameter for ground-mounted plants with high albedo.

  ---

  ## 🔹 Maximum system voltage

  - Maximum allowed module system voltage.
  - Critical for string sizing at low temperatures.
  """,

}


