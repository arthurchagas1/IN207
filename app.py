import streamlit as st

st.set_page_config(
    page_title="IN207 - Base de données GTFS IDFM",
    page_icon="🚆",
    layout="wide"
)

st.title("🚆 IN207 — Introduction aux Bases de Données")
st.markdown(
    """
Bienvenue dans l'application pédagogique de modélisation et d'interrogation d'une base de données relationnelle.

### Sujet choisi
**Réseau de transport public (GTFS Île-de-France Mobilités)**

Utilisez le menu de navigation à gauche pour consulter :
- **Accueil**
- **MCD**
- **MLD**
- **DDL**
- **Requêtes SQL**
- **Valorisation des données**
"""
)
