# PVInsight 2.6

PVInsight est une application Streamlit modulaire pour l'analyse de donnees photovoltaiques.
Le projet est organise pour separer clairement la logique metier (`core/`) et l'interface (`app/`).

## Objectif

- Centraliser plusieurs outils d'analyse dans une interface unique.
- Produire des resultats exploitables (tableaux, graphiques, exports).
- Garder une base de code maintenable et evolutive.

## Outils principaux

- TMY Analysis
- TMY Compare
- Hourly Results Analysis
- PAN vs Datasheet Compare
- Market Analysis
- BESS PV Sizing (V2)

## Ameliorations realisees (precedentes discussions)

- Ajout d'un nouvel outil `BESS PV Sizing` avec screening MW x MWh, optimisation horaire et recommandations automatiques.
- Introduction d'un moteur BESS V2 (modes techno-economique utilisateur, techno-economique par defaut, et optimisation marginale).
- Ajout des KPI economiques avances (CAPEX/OPEX annualises, marge nette, payback simple, NPV simplifiee, remplacement).
- Ajout d'options techniques avancees BESS (charge reseau, limite d'injection, pertes auxiliaires, cout de degradation).
- Renforcement de l'analyse horaire: etude approximative tan(phi), meilleure lecture des pertes de limitation, et gestion explicite du seuil a 0.
- Evolution des exports Excel/PDF de l'analyse horaire pour refléter les indicateurs de pertes (lost energy / lost share).
- Durcissement du traitement IAM (gestion des angles dupliques et avertissements qualite sur profil PAN).
- Enrichissement i18n FR/EN pour les nouveaux ecrans, aides contextuelles et metriques.
- Stabilisation de l'affichage des logos locaux via rendu inline (sidebar + accueil).
- Ajout de `scipy` dans `requirements.txt` pour le solveur LP BESS.

## Architecture

- `app/`: pages Streamlit, navigation, UI, i18n.
- `core/`: calculs metier et pipelines d'analyse.
- `utils/`: lecteurs, formatage, helpers transverses.
- `assets/`: logo et ressources de traduction.
- `config/`: configuration globale et registre des outils.

## Confidentialite et gestion des donnees

Le projet applique les principes suivants:

- Pas d'affichage des noms de fichiers uploades dans les sorties utilisateurs.
- Redaction des informations sensibles (noms de projet, auteur, variantes) dans les logs applicatifs.
- Generation des exports via fichiers temporaires et conservation en memoire pour telechargement.
- Aucune persistance volontaire des fichiers uploades dans les pages d'analyse actives.

Important:

- Sur Streamlit Community Cloud, `st.file_uploader` fournit les fichiers en memoire (RAM).
- Les logs Cloud restent accessibles aux mainteneurs de l'application: ne pas y imprimer de donnees sensibles.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app/app_streamlit.py
```

## Ajouter un outil

1. Creer la logique metier dans `core/<domaine>/`.
2. Creer la page Streamlit dans `app/pages/`.
3. Declarer l'outil dans `config/tools_registry.py`.
4. Ajouter les cles de traduction dans `assets/i18n/fr.py` et `assets/i18n/en.py`.

## Version

Version courante: **2.6**

## Statut

Projet en developpement actif (usage interne).
