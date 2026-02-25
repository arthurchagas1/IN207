import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Accueil", page_icon="🏠", layout="wide")

st.title("🏠 Accueil du projet IN207")
st.subheader("Base de données relationnelle sur les transports publics (GTFS Île-de-France Mobilités)")

st.markdown(
    """
## Objectif du projet

Ce projet illustre les étapes complètes de conception d'une base de données relationnelle :

1. **MCD** (Modèle Conceptuel de Données)
2. **MLD** (Modèle Logique de Données)
3. **DDL** (création et peuplement de la base)
4. **Requêtes SQL**
5. **Valorisation des données** (visualisations / tableaux de bord)

## Application métier choisie

Nous modélisons un **système d'information de transport public** basé sur un jeu de données GTFS (Île-de-France Mobilités), incluant :
- les **agences/opérateurs**
- les **lignes**
- les **courses (trips)**
- les **arrêts / stations**
- les **horaires de passage**
- les **correspondances**
- les **calendriers de circulation**
"""
)

data_dir = Path("data")
st.markdown("## Vérification des données")
if data_dir.exists():
    files = sorted([p.name for p in data_dir.glob("*.txt")])
    st.success(f"Dossier `data/` détecté ({len(files)} fichiers .txt)")
    st.write(files)
else:
    st.warning("Le dossier `data/` n'existe pas encore. Placez vos fichiers GTFS dans `data/`.")
