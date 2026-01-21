# 💎 LVMH ROI Calculator - Sustainable IT Investment

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.0-38B2AC?style=for-the-badge&logo=tailwind-css)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

Une application web luxueuse et performante conçue pour aider les Maisons LVMH à évaluer le retour sur investissement (ROI) de leurs équipements IT, en pondérant **l'impact financier** et **l'empreinte écologique**.

L'application intègre une analyse comparative propulsée par **IA (Llama 3 via DeepInfra)** pour fournir des recommandations stratégiques.



---

## 🚀 Fonctionnalités Clés

* **🔐 Authentification Sécurisée** : Système de session utilisateur (Compte démo inclus).
* **🏛️ Sélection des Maisons** : Personnalisation du calcul pour les différentes maisons du groupe (Louis Vuitton, Dior, Sephora, etc.).
* **💻 Saisie d'Équipements** : Catalogue pré-défini d'équipements IT (Smartphones, Laptops, Tablettes) avec données écologiques et financières.
* **⚖️ Calculateur Pondéré** : Curseur interactif pour ajuster la stratégie (ex: 70% Écologique / 30% Financier).
* **📊 Visualisation des Résultats** : Scores détaillés, graphiques et indicateurs de performance.
* **🤖 Intelligence Artificielle** : Analyse comparative de scénarios multiples générée par IA pour identifier les meilleurs "trade-offs".
* **📱 Design Responsive** : Interface moderne et élégante utilisant Tailwind CSS.

---

## 🛠️ Stack Technique



* **Backend** : Python 3.11, FastAPI, SQLAlchemy, SQLite.
* **Frontend** : Jinja2 Templates, Tailwind CSS (CDN), Vanilla JS.
* **Visualisation** : Chart.js.
* **Markdown** : Marked.js.
* **IA** : OpenAI Client (connecté à DeepInfra / Meta-Llama-3-70B).

---

## 📂 Structure du Projet

```text
alberthon-code/
├── app/
│   ├── main.py          # Point d'entrée et routes (API & Views)
│   ├── models.py        # Modèles de base de données (User, Calculation)
│   ├── database.py      # Configuration SQLite
│   └── auth.py          # Logique d'authentification
├── static/              # Fichiers statiques (CSS, JS)
├── templates/           # Vues HTML (Jinja2)
├── environment.yml      # Configuration Conda
└── database.db          # Base de données (générée automatiquement)

```

---

## ⚙️ Installation

### Prérequis

* Python 3.11+
* Conda (recommandé) ou Pip

### Méthode 1 : Via Conda (Recommandé)

```bash
# 1. Créer l'environnement à partir du fichier yml
conda env create -f environment.yml

# 2. Activer l'environnement
conda activate alberthon

```

### Méthode 2 : Via Pip

```bash
# Installer les dépendances manuellement
pip install fastapi uvicorn[standard] sqlalchemy python-multipart jinja2 openai

```

---

## 🚀 Démarrage

1. **Configuration de l'API Key**
Ouvrez `app/main.py` et assurez-vous que votre clé API DeepInfra est configurée :
```python
DEEPINFRA_API_KEY = "VOTRE_CLE_ICI"

```


2. **Lancer le serveur**
À la racine du projet, exécutez :
```bash
uvicorn app.main:app --reload

```


3. **Accéder à l'application**
Ouvrez votre navigateur sur : `http://127.0.0.1:8000`

---

## 🔑 Compte de Démonstration

Pour tester l'application, utilisez les identifiants suivants :

* **Identifiant :** `demo`
* **Mot de passe :** `demo123`

---

## 🧠 Fonctionnement de l'IA

L'application utilise un appel asynchrone (`fetch` en JS) vers une route API dédiée `/api/analyze-comparison`.
Cela permet de :

1. Charger l'interface utilisateur instantanément.
2. Afficher un **loader** pendant que le modèle Llama 3 analyse les données.
3. Restituer l'analyse stratégique formatée en **Markdown** directement dans la page.