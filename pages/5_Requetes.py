import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Requêtes SQL", page_icon="🔎", layout="wide")

DB_PATH = "database.db"

def run_query(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()

st.title("🔎 Étape 4 — Requêtes SQL")

if not Path(DB_PATH).exists():
    st.warning("La base `database.db` n'existe pas encore. Allez d'abord sur la page **DDL**.")
    st.stop()

st.markdown("## A. 10 requêtes SQL (traduction des requêtes d’algèbre relationnelle)")

requetes_base = {
    "1. Lignes de bus (route_type = 3)": """
        SELECT route_id, route_short_name, route_long_name, route_type
        FROM routes
        WHERE route_type = 3
        ORDER BY route_short_name
        LIMIT 100;
    """,
    "2. Projection des arrêts (id, nom)": """
        SELECT stop_id, stop_name
        FROM stops
        ORDER BY stop_name
        LIMIT 100;
    """,
    "3. Courses avec infos de ligne (jointure TRIPS ⋈ ROUTES)": """
        SELECT t.trip_id, t.route_id, r.route_short_name, r.route_long_name, t.direction_id
        FROM trips t
        JOIN routes r ON r.route_id = t.route_id
        LIMIT 100;
    """,
    "4. Horaires et noms d’arrêts (STOP_TIMES ⋈ STOPS)": """
        SELECT st.trip_id, st.stop_sequence, st.arrival_time, st.departure_time, s.stop_name
        FROM stop_times st
        JOIN stops s ON s.stop_id = st.stop_id
        ORDER BY st.trip_id, st.stop_sequence
        LIMIT 100;
    """,
    "5. Stations uniquement (location_type = 1)": """
        SELECT stop_id, stop_name, location_type, parent_station
        FROM stops
        WHERE location_type = 1
        LIMIT 100;
    """,
    "6. Lignes ayant au moins une course": """
        SELECT DISTINCT r.route_id, r.route_short_name, r.route_long_name
        FROM routes r
        JOIN trips t ON t.route_id = r.route_id
        ORDER BY r.route_short_name
        LIMIT 100;
    """,
    "7. Parcours complets (TRIPS ⋈ STOP_TIMES ⋈ STOPS)": """
        SELECT t.trip_id, t.route_id, st.stop_sequence, s.stop_name, st.departure_time
        FROM trips t
        JOIN stop_times st ON st.trip_id = t.trip_id
        JOIN stops s ON s.stop_id = st.stop_id
        ORDER BY t.trip_id, st.stop_sequence
        LIMIT 200;
    """,
    "8. Arrêts parent/enfant (auto-jointure STOPS)": """
        SELECT enfant.stop_id AS stop_enfant, enfant.stop_name AS nom_enfant,
               parent.stop_id AS station_parent, parent.stop_name AS nom_parent
        FROM stops enfant
        JOIN stops parent ON enfant.parent_station = parent.stop_id
        LIMIT 100;
    """,
    "9. Division (lignes desservant TOUS les arrêts d’un petit ensemble cible)": """
        -- On prend 3 arrêts cibles (exemple : 3 premiers arrêts de type physique)
        WITH cible AS (
            SELECT stop_id
            FROM stops
            WHERE COALESCE(location_type,0)=0
            LIMIT 3
        ),
        route_stop AS (
            SELECT DISTINCT t.route_id, st.stop_id
            FROM trips t
            JOIN stop_times st ON st.trip_id = t.trip_id
        )
        SELECT r.route_id, r.route_short_name, r.route_long_name
        FROM routes r
        WHERE NOT EXISTS (
            SELECT 1
            FROM cible c
            WHERE NOT EXISTS (
                SELECT 1
                FROM route_stop rs
                WHERE rs.route_id = r.route_id
                  AND rs.stop_id = c.stop_id
            )
        )
        LIMIT 100;
    """,
    "10. Division (services actifs tous les jours ouvrés lun→ven)": """
        SELECT service_id
        FROM calendar
        WHERE monday = 1
          AND tuesday = 1
          AND wednesday = 1
          AND thursday = 1
          AND friday = 1
        LIMIT 100;
    """,
}

choix_a = st.selectbox("Choisissez une requête (partie A)", list(requetes_base.keys()))
st.code(requetes_base[choix_a], language="sql")
if st.button("▶️ Exécuter la requête A"):
    try:
        df = run_query(requetes_base[choix_a])
        st.dataframe(df, use_container_width=True)
        st.success(f"{len(df)} ligne(s) affichée(s)")
    except Exception as e:
        st.error(f"Erreur SQL : {e}")

st.markdown("---")
st.markdown("## B. 10 requêtes SQL supplémentaires (agrégations, GROUP BY, HAVING)")

requetes_agregats = {
    "1. Nombre de lignes par type (route_type)": """
        SELECT route_type, COUNT(*) AS nb_lignes
        FROM routes
        GROUP BY route_type
        ORDER BY nb_lignes DESC;
    """,
    "2. Nombre de courses par ligne": """
        SELECT r.route_id, r.route_short_name, COUNT(t.trip_id) AS nb_courses
        FROM routes r
        LEFT JOIN trips t ON t.route_id = r.route_id
        GROUP BY r.route_id, r.route_short_name
        ORDER BY nb_courses DESC
        LIMIT 50;
    """,
    "3. Nombre d’arrêts desservis par ligne": """
        SELECT t.route_id, COUNT(DISTINCT st.stop_id) AS nb_arrets_distincts
        FROM trips t
        JOIN stop_times st ON st.trip_id = t.trip_id
        GROUP BY t.route_id
        ORDER BY nb_arrets_distincts DESC
        LIMIT 50;
    """,
    "4. Top 20 arrêts les plus desservis": """
        SELECT s.stop_id, s.stop_name, COUNT(*) AS nb_passages
        FROM stop_times st
        JOIN stops s ON s.stop_id = st.stop_id
        GROUP BY s.stop_id, s.stop_name
        ORDER BY nb_passages DESC
        LIMIT 20;
    """,
    "5. Temps moyen de correspondance (transfers)": """
        SELECT AVG(min_transfer_time) AS temps_moyen_sec,
               MIN(min_transfer_time) AS min_sec,
               MAX(min_transfer_time) AS max_sec
        FROM transfers
        WHERE min_transfer_time IS NOT NULL;
    """,
    "6. Nombre de stations / arrêts / accès (location_type)": """
        SELECT COALESCE(location_type, -1) AS location_type, COUNT(*) AS nb
        FROM stops
        GROUP BY COALESCE(location_type, -1)
        ORDER BY location_type;
    """,
    "7. Services par période de validité (min/max dates)": """
        SELECT MIN(start_date) AS date_debut_min,
               MAX(end_date) AS date_fin_max,
               COUNT(*) AS nb_services
        FROM calendar;
    """,
    "8. Lignes avec plus de 100 courses (HAVING)": """
        SELECT t.route_id, COUNT(*) AS nb_courses
        FROM trips t
        GROUP BY t.route_id
        HAVING COUNT(*) > 100
        ORDER BY nb_courses DESC
        LIMIT 100;
    """,
    "9. Arrêts ayant au moins 500 passages (HAVING)": """
        SELECT st.stop_id, s.stop_name, COUNT(*) AS nb_passages
        FROM stop_times st
        JOIN stops s ON s.stop_id = st.stop_id
        GROUP BY st.stop_id, s.stop_name
        HAVING COUNT(*) >= 500
        ORDER BY nb_passages DESC
        LIMIT 100;
    """,
    "10. Courses par direction (direction_id)": """
        SELECT COALESCE(direction_id, -1) AS direction_id, COUNT(*) AS nb_courses
        FROM trips
        GROUP BY COALESCE(direction_id, -1)
        ORDER BY nb_courses DESC;
    """,
}

choix_b = st.selectbox("Choisissez une requête (partie B)", list(requetes_agregats.keys()))
st.code(requetes_agregats[choix_b], language="sql")
if st.button("▶️ Exécuter la requête B"):
    try:
        df = run_query(requetes_agregats[choix_b])
        st.dataframe(df, use_container_width=True)
        st.success(f"{len(df)} ligne(s) affichée(s)")
    except Exception as e:
        st.error(f"Erreur SQL : {e}")

st.markdown("---")
st.markdown("## Exécution libre (SQL personnalisé)")

sql_libre = st.text_area(
    "Saisissez votre requête SQL",
    value="SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;",
    height=180
)

if st.button("🧪 Exécuter SQL libre"):
    try:
        df = run_query(sql_libre)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur SQL : {e}")
