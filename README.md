# PVInsight

**PVInsight** est un outil d’analyse interactif destiné aux ingénieurs et chargés d’études photovoltaïques.  
Il regroupe plusieurs modules d’analyse autour des **données météorologiques (TMY)** et des **résultats horaires PVSyst**, avec une interface **Streamlit** simple et robuste.

---

## 🎯 Objectifs

- Analyser rapidement des fichiers **TMY PVSyst** (horaire ou sub-hourly)
- Comparer deux jeux de données météo (TMY)
- Analyser les **Hourly Results PVSyst** :
  - dépassement de seuil de puissance
  - distribution de puissance
  - clipping onduleur
- Générer des **rapports Excel et PDF**
- Visualiser les résultats **directement dans l’interface web**
- Fournir une base claire et extensible pour de futurs outils (V2, V3…)

---

## 🧱 Architecture générale

PVInsight est structuré en **trois couches distinctes** :

### 1. Core (métier / calcul)
- Parsing des fichiers PVSyst
- Normalisation temporelle et d’unités
- Analyses statistiques et énergétiques
- Génération des résultats structurés

### 2. UI (Streamlit)
- Navigation par boutons (pas de multipage Streamlit natif)
- Sidebar globale (langue, unités, options)
- Pages outils :
  - Analyse TMY
  - Comparaison TMY
  - Hourly Results
- Graphiques interactifs (Plotly)
- Téléchargement des rapports

### 3. Utils (transverse)
- Gestion des unités
- Séries temporelles
- Validation de données
- Logs d’exécution
- Gestion des dossiers de sortie (`outputs/latest/`)

PVInsight/
├─ config.py
├─ requirements.txt
├─ assets/
│  ├─ logo.png
│  ├─ logo.ico
│  └─ i18n/
│     ├─ __init__.py
│     ├─ fr.py
│     └─ en.py
├─ outputs/
│  └─ latest/
├─ utils/
│  ├─ __init__.py
│  ├─ i18n.py
│  ├─ paths.py
│  ├─ formatting.py
│  ├─ columns.py
│  ├─ energy.py
│  ├─ io.py
│  ├─ run_log.py
│  ├─ time_series.py
│  ├─ units.py
│  ├─ validation.py
│  └─ (autres helpers si besoin)
├─ core/
│  ├─ __init__.py
│  ├─ meteo/
│  │  ├─ __init__.py
│  │  ├─ tmy_pvsyst.py
│  │  ├─ tmy_analysis.py
│  │  └─ tmy_compare.py
│  └─ production/
│     ├─ __init__.py
│     ├─ hourly_pipeline.py
│     ├─ hourly_io.py
│     ├─ hourly_models.py
│     ├─ hourly_analyzer.py
│     ├─ hourly_export_excel.py
│     └─ hourly_export_pdf.py
└─ app/
   ├─ __init__.py
   ├─ _bootstrap.py
   ├─ Home.py
   └─ ui/
      ├─ __init__.py
      ├─ layout.py
      ├─ state.py
      ├─ inputs.py
      ├─ widgets.py
      ├─ views.py
      ├─ common.py
      ├─ render_tmy.py
      └─ render_hourly.py

---

## 📁 Organisation des sorties

PVInsight **n’archive pas les runs** par défaut.

Tous les résultats sont **réécrits à chaque analyse** dans :
outputs/latest/
├─ tmy_analysis/
├─ tmy_compare/
└─ hourly_results/

Chaque outil contient :
- `figures/` → images / graphiques
- `reports/` → Excel + PDF
- `logs/` → logs texte d’exécution

👉 Cette approche évite l’encombrement disque et simplifie le partage.

---

## 🚀 Lancer l’application

### 1. Créer un environnement Python

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Lancer Streamlit
```bash
streamlit run app/Home.py
```
L’application s’ouvre automatiquement dans le navigateur.

## Outils disponibles (V1)
### ☀️ Analyse TMY

- Lecture fichiers TMY PVSyst (horaire ou sub-hourly)
- Harmonisation temporelle automatique
- Statistiques GHI / DNI / température
- Graphiques interactifs
- Export PDF & Excel

### 🔄 Comparaison TMY

- Comparaison de deux fichiers TMY
- Alignement des périodes communes
- Différences absolues et relatives
- Rapport comparatif PDF

### ⚡ Hourly Results (PVSyst)

- Analyse des résultats horaires de production
- Dépassement de seuil de puissance
- Distribution de puissance
- Clipping onduleur (EOutInv / IL_Pmax)
- Visualisation + exports

### 🌍 Internationalisation (i18n)

- Langue actuelle : français
- Anglais prêt via assets/i18n/en.py
- Tous les textes UI passent par un dictionnaire
- Changement de langue depuis la sidebar

### 🛠️ Dépendances principales

- pandas / numpy : traitement des données
- plotly : graphiques interactifs
- streamlit : interface web
- xlsxwriter / openpyxl : export Excel
- reportlab : export PDF
- Pillow : gestion des logos
- Voir requirements.txt pour le détail.

### 📌 État du projet

- Version : 0.1.0
- Statut : V1 fonctionnelle

### ⚠️ Notes importantes

- PVInsight est conçu pour un usage interne / professionnel
- Les résultats dépendent de la qualité des fichiers PVSyst fournis
- Aucun envoi de données : tout est traité localement

## Architecture détaillée

config.py                     → Configuration globale (paths, options par défaut)
requirements.txt              → Dépendances Python

assets/
├─ logo.png                   → Logo UI
├─ logo.ico                   → Icône application
└─ i18n/
   ├─ fr.py                   → Textes UI français
   └─ en.py                   → Textes UI anglais

outputs/
└─ latest/                    → Résultats réécrits à chaque analyse

utils/
├─ i18n.py                    → Traduction t(key, lang)
├─ paths.py                   → Gestion dossiers outputs/latest
├─ formatting.py              → Formatage nombres / affichage
├─ columns.py                 → Validation & suggestions colonnes
├─ energy.py                  → Helpers énergie / puissance
├─ io.py                      → I/O générique (bytes, texte, encodage)
├─ run_log.py                 → Logs d’exécution par outil
├─ time_series.py             → Outils séries temporelles (pas, resample)
├─ units.py                   → Gestion & conversion des unités
└─ validation.py              → Contrôles de robustesse données

core/
├─ meteo/
│  ├─ tmy_pvsyst.py           → Lecture/parsing fichiers TMY PVSyst
│  ├─ tmy_analysis.py         → Analyse TMY (backend)
│  └─ tmy_compare.py          → Comparaison de deux TMY
└─ production/
   ├─ hourly_pipeline.py      → Orchestrateur Hourly Results
   ├─ hourly_io.py            → Parsing Hourly Results PVSyst
   ├─ hourly_models.py        → Dataclasses contexte/options
   ├─ hourly_analyzer.py      → Analyses (seuil, clipping, distribution)
   ├─ hourly_export_excel.py  → Export Excel Hourly
   └─ hourly_export_pdf.py    → Export PDF Hourly

app/
├─ _bootstrap.py              → Initialisation environnement app
├─ Home.py                    → Point d’entrée Streamlit + router
└─ ui/
   ├─ layout.py               → Layout global & sidebar
   ├─ state.py                → Gestion session_state
   ├─ inputs.py               → Inputs métier réutilisables
   ├─ widgets.py              → Widgets UI génériques
   ├─ views.py                → Pages outils (Home / TMY / Hourly)
   ├─ common.py               → Helpers UI communs
   ├─ render_tmy.py           → Rendu résultats TMY
   └─ render_hourly.py        → Rendu résultats Hourly
