
# Architecture du projet & procédure d’ajout d’outils
**PVInsight – Streamlit App**

Ce document décrit :
1. L’architecture complète du projet Streamlit
2. Le rôle de chaque dossier et script
3. Le processus standardisé pour créer et ajouter un nouvel outil
4. Le format officiel d’une page outil (scalable et maintenable)

---

## 1. Vue d’ensemble de l’architecture

```
project_root/
│
├── app/
│   ├── app_streamlit.py
│   ├── bootstrap.py
│   │
│   ├── ui/
│   │   ├── i18n.py
│   │   ├── state.py
│   │   ├── theme.py
│   │   ├── layout.py
│   │   ├── tool_layout.py
│   │   └── tool_state.py
│   │
│   └── pages/
│       ├── 00_home.py
│       ├── 01_settings.py
│       ├── 10_tool_template.py
│       └── 99_exit.py
│
├── config/
│   ├── config.py
│   └── tools_registry.py
│
├── assets/
│   ├── logo.png
│   └── i18n/
│       ├── fr.py
│       └── en.py
│
└── Description.md
```

---

## 2. Principes généraux

- `app/` est la racine Streamlit
- Les imports internes se font sans préfixe `app.`
- Toute chaîne visible utilisateur passe par l’i18n
- La navigation est centralisée
- Les outils sont déclarés dans un registre unique

---

## 3. Rôle des principaux scripts

### app_streamlit.py
Point d’entrée de l’application :
- initialise le state global
- déclare les pages (Home, Settings, Tools, Exit)
- lance la navigation

### tools_registry.py
Registre central des outils :
- alimente l’accueil
- alimente la navigation
- permet d’activer/désactiver un outil

### Pages
- **00_home.py** : accueil et accès aux outils
- **01_settings.py** : réglages utilisateur
- **10_tool_template.py** : référence de mise en page
- **99_exit.py** : page de sortie (fermeture onglet)

### UI
- **layout.py** : sidebar standard
- **tool_layout.py** : header + sections d’outils
- **tool_state.py** : state isolé par outil

---

## 4. Procédure d’ajout d’un outil

### Étape 1 — Créer la page
Créer :
```
app/pages/NN_nom_outil.py
```

### Étape 2 — Ajouter au registre
Dans `config/tools_registry.py` :
- tool_id
- page
- icône
- clés i18n

### Étape 3 — Ajouter les traductions
Dans `assets/i18n/fr.py` et `en.py` :
- TOOL_<ID>_TITLE
- TOOL_<ID>_DESC

### Étape 4 — Initialiser le state outil
Utiliser `init_tool_state()` avec des defaults

### Étape 5 — Appliquer le layout standard
Sections :
- Inputs
- Run
- Results
- Export

---

## 5. Standardisation d’un outil

- Nom fichier : `NN_snake_case.py`
- Tool ID : `UPPER_SNAKE_CASE`
- State : `tool.<ID>.<param>`
- i18n obligatoire

---

Ce document fait foi pour toute évolution du projet.
