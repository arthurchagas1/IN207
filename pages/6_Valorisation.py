import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Valorisation", page_icon="📊", layout="wide")

DB_PATH = "database.db"

def q(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()

st.title("📊 Étape 5 — Valorisation des données")
st.markdown("Tableau de bord interactif pour explorer le réseau de transport.")

if not Path(DB_PATH).exists():
    st.warning("La base `database.db` n'existe pas encore. Passez par la page **DDL**.")
    st.stop()

# KPI globaux
kpi_sql = {
    "Agences": "SELECT COUNT(*) AS n FROM agency;",
    "Lignes": "SELECT COUNT(*) AS n FROM routes;",
    "Courses": "SELECT COUNT(*) AS n FROM trips;",
    "Arrêts": "SELECT COUNT(*) AS n FROM stops;",
    "Passages": "SELECT COUNT(*) AS n FROM stop_times;",
    "Correspondances": "SELECT COUNT(*) AS n FROM transfers;",
}
vals = {}
for k, sql in kpi_sql.items():
    try:
        vals[k] = int(q(sql)["n"][0])
    except Exception:
        vals[k] = 0

cols = st.columns(3)
for i, (k, v) in enumerate(vals.items()):
    cols[i % 3].metric(k, f"{v:,}".replace(",", " "))

st.markdown("---")

# Distribution route_type
st.subheader("1) Répartition des lignes par type de transport")
df_route_type = q("""
    SELECT CAST(route_type AS TEXT) AS route_type, COUNT(*) AS nb_lignes
    FROM routes
    GROUP BY route_type
    ORDER BY nb_lignes DESC;
""")
if not df_route_type.empty:
    st.bar_chart(df_route_type.set_index("route_type"))
else:
    st.info("Aucune donnée disponible pour `routes`.")

# Top lignes
st.subheader("2) Top lignes par nombre de courses")
top_n = st.slider("Nombre de lignes à afficher", min_value=5, max_value=50, value=15, step=5)
df_top_routes = q(f"""
    SELECT 
        t.route_id,
        COALESCE(r.route_short_name, t.route_id) AS libelle_ligne,
        COUNT(*) AS nb_courses
    FROM trips t
    LEFT JOIN routes r ON r.route_id = t.route_id
    GROUP BY t.route_id, libelle_ligne
    ORDER BY nb_courses DESC
    LIMIT {top_n};
""")
if not df_top_routes.empty:
    st.dataframe(df_top_routes, use_container_width=True)
    st.bar_chart(df_top_routes.set_index("libelle_ligne")["nb_courses"])

st.markdown("---")

# Analyse par ligne (filtre)
st.subheader("3) Analyse détaillée d’une ligne")

df_routes_list = q("""
    SELECT route_id,
           COALESCE(route_short_name, route_id) AS route_short_name,
           COALESCE(route_long_name, '') AS route_long_name
    FROM routes
    ORDER BY route_short_name;
""")

if not df_routes_list.empty:
    df_routes_list["label"] = df_routes_list["route_short_name"] + " — " + df_routes_list["route_long_name"]
    selected_label = st.selectbox("Choisir une ligne", df_routes_list["label"].tolist())
    selected_route_id = df_routes_list.loc[df_routes_list["label"] == selected_label, "route_id"].iloc[0]

    # KPIs de la ligne
    c1, c2, c3 = st.columns(3)
    nb_trips = q(f"SELECT COUNT(*) AS n FROM trips WHERE route_id = '{selected_route_id}';")["n"][0]
    nb_stops = q(f"""
        SELECT COUNT(DISTINCT st.stop_id) AS n
        FROM trips t
        JOIN stop_times st ON st.trip_id = t.trip_id
        WHERE t.route_id = '{selected_route_id}';
    """)["n"][0]
    nb_dirs = q(f"SELECT COUNT(DISTINCT COALESCE(direction_id,-1)) AS n FROM trips WHERE route_id = '{selected_route_id}';")["n"][0]

    c1.metric("Courses", int(nb_trips))
    c2.metric("Arrêts distincts", int(nb_stops))
    c3.metric("Directions", int(nb_dirs))

    # Arrêts les plus fréquents sur la ligne
    st.markdown("### Arrêts les plus desservis sur cette ligne")
    df_stops_line = q(f"""
        SELECT s.stop_name, COUNT(*) AS nb_passages
        FROM trips t
        JOIN stop_times st ON st.trip_id = t.trip_id
        JOIN stops s ON s.stop_id = st.stop_id
        WHERE t.route_id = '{selected_route_id}'
        GROUP BY s.stop_name
        ORDER BY nb_passages DESC
        LIMIT 20;
    """)
    st.dataframe(df_stops_line, use_container_width=True)
    if not df_stops_line.empty:
        st.bar_chart(df_stops_line.set_index("stop_name")["nb_passages"])

st.markdown("---")

# Carte simple (si lat/lon disponibles)
st.subheader("4) Carte des arrêts (échantillon)")
nb_points = st.slider("Nombre de points sur la carte", 100, 5000, 1000, 100)
df_map = q(f"""
    SELECT stop_name, stop_lat, stop_lon
    FROM stops
    WHERE stop_lat IS NOT NULL AND stop_lon IS NOT NULL
    LIMIT {nb_points};
""")
if not df_map.empty:
    st.map(df_map.rename(columns={"stop_lat": "lat", "stop_lon": "lon"}))
else:
    st.info("Coordonnées géographiques non disponibles.")

st.markdown("---")

# Contrôles qualité
st.subheader("5) Indicateurs de qualité des données")
df_quality = q("""
    SELECT 'stop_times sans trip' AS indicateur, COUNT(*) AS nb
    FROM stop_times st
    LEFT JOIN trips t ON t.trip_id = st.trip_id
    WHERE t.trip_id IS NULL

    UNION ALL

    SELECT 'stop_times sans stop' AS indicateur, COUNT(*) AS nb
    FROM stop_times st
    LEFT JOIN stops s ON s.stop_id = st.stop_id
    WHERE s.stop_id IS NULL

    UNION ALL

    SELECT 'trips sans route' AS indicateur, COUNT(*) AS nb
    FROM trips t
    LEFT JOIN routes r ON r.route_id = t.route_id
    WHERE r.route_id IS NULL
""")
st.dataframe(df_quality, use_container_width=True)
