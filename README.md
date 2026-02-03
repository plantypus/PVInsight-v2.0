# 🌞 PVInsight 2.0

**PVInsight 2.0** est une plateforme modulaire d’analyse, de visualisation et d’aide à la décision pour les projets photovoltaïques.  
Elle combine **Python**, **Streamlit** et des scripts métiers spécialisés pour couvrir l’ensemble du cycle d’analyse :  
données météo (TMY), production, PR, contraintes réseau, géométrie 3D, CFD, et analyses avancées.

> 🎯 Objectif : proposer des **outils robustes, maintenables et bilingues (FR/EN)**, pensés pour un usage interne professionnel et évolutif.

---

## ✨ Principes clés

- 🧩 **Architecture modulaire** (un outil = un module clair)
- 🌍 **Interface Streamlit unifiée**
- 🌐 **Internationalisation (i18n) FR / EN**
- 🧠 **Séparation stricte métier / interface**
- 📦 **Exports standards** (Excel, images, données structurées)
- 🚀 **Scalabilité** : ajout d’outils sans refactor global

---

## 🔧 Séparation des responsabilités

### `core/` – Logique métier
- Calculs
- Lecture de fichiers
- Analyses
- Génération de données
- **Aucun affichage Streamlit**
- Langue **anglais uniquement**

### `app/` – Interface utilisateur
- Streamlit
- Mise en page
- Navigation
- i18n
- États de session
- UX / UI

---

## 🧰 Outils disponibles (exemples)

- 🌤️ **TMY Analysis**
  - Lecture automatique multi-sources (PVSyst, SolarGIS, etc.)
  - Harmonisation unités
  - Comparaison de fichiers météo

- 📊 **Hourly Results Analysis**
  - Analyse des résultats horaires PVSyst
  - Production, PR, limitations, synthèses temporelles

- 🌬️ **Geometry / CFD Tools**
  - Génération de géométrie PV
  - Visualisation interne PyVista
  - Pré-traitement CFD

*(La liste évolue avec le projet)*

---

## 🌍 Internationalisation (i18n)

- Toutes les chaînes UI passent par les dictionnaires `i18n/fr.py` et `i18n/en.py`
- Les scripts métiers (`core/`) restent **neutres et indépendants de la langue**
- Commutation de langue globale via l’état Streamlit

---

## ➕ Ajouter un nouvel outil

1. **Créer le script métier**
core/<domaine>/<mon_outil>.py

2. **Créer la page Streamlit**
app/pages/XX_mon_outil.py

3. **Déclarer l’outil**
config/tools_registry.py

4. **Ajouter les clés i18n**
app/i18n/fr.py
app/i18n/en.py


👉 Aucun impact sur les autres outils.

---

## ▶️ Lancer l’application

```bash
streamlit run app/app_streamlit.py
```

Le script bootstrap.py s’occupe automatiquement :
 - de l’initialisation des chemins,
 - du chargement des styles,
 - de la mise en place de l’état global.

## 📦 Dépendances

Voir le fichier `requirements.txt`.

Principales librairies utilisées :

  - streamlit

  - pandas

  - numpy

  - matplotlib

## 🧠 Philosophie du projet

PVInsight 2.0 est pensé comme :

  - un socle technique durable,

  - un outil métier avant tout,

  - une boîte à outils évolutive,

  - un projet où la lisibilité prime sur la magie,

  - une base saine pour des analyses photovoltaïques avancées.

## 👤 Auteur

Simon Demarche
Développement interne – Innovations territoriales / Photovoltaïque

## 📌 Statut

🚧 En développement actif
Architecture stabilisée – outils ajoutés progressivement.
