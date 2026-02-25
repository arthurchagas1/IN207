import streamlit as st
import pandas as pd

st.set_page_config(page_title="MLD", page_icon="🧱", layout="wide")

st.title("🧱 Étape 2 — Modèle Logique de Données (MLD)")

st.markdown("## Schéma relationnel (extrait principal)")

mld = [
    ["agency", "agency_id", "agency_name, agency_url, agency_timezone, agency_lang, agency_phone", "-"],
    ["routes", "route_id", "agency_id, route_short_name, route_long_name, route_type, route_color", "agency_id → agency.agency_id"],
    ["service", "service_id", "-", "-"],
    ["calendar", "service_id", "monday..sunday, start_date, end_date", "service_id → service.service_id"],
    ["calendar_dates", "(service_id, date)", "exception_type", "service_id → service.service_id"],
    ["trips", "trip_id", "route_id, service_id, trip_headsign, direction_id, block_id", "route_id → routes.route_id ; service_id → service.service_id"],
    ["stops", "stop_id", "stop_name, stop_lat, stop_lon, location_type, parent_station, wheelchair_boarding", "parent_station → stops.stop_id"],
    ["stop_times", "(trip_id, stop_sequence)", "stop_id, arrival_time, departure_time, pickup_type, drop_off_type", "trip_id → trips.trip_id ; stop_id → stops.stop_id"],
    ["transfers", "transfer_id", "from_stop_id, to_stop_id, transfer_type, min_transfer_time", "from_stop_id/to_stop_id → stops.stop_id"],
    ["pathways", "pathway_id", "from_stop_id, to_stop_id, pathway_mode, traversal_time", "from_stop_id/to_stop_id → stops.stop_id"],
]

df = pd.DataFrame(mld, columns=["Table", "Clé primaire", "Attributs principaux", "Clés étrangères"])
st.dataframe(df, use_container_width=True)

st.markdown("## Contraintes d’intégrité")
st.markdown(
    """
- **Intégrité d’entité** : chaque table possède une clé primaire non nulle.
- **Intégrité référentielle** :
  - `routes.agency_id` référence `agency`
  - `trips.route_id` référence `routes`
  - `trips.service_id` référence `service`
  - `stop_times.trip_id` référence `trips`
  - `stop_times.stop_id` référence `stops`
  - `stops.parent_station` référence `stops`
- **Contraintes métier** :
  - `route_type` suit la codification GTFS (bus, métro, tram...)
  - `location_type` décrit le type d’objet (`arrêt`, `station`, `accès`, ...)
  - `arrival_time` et `departure_time` peuvent dépasser `24:00:00` (format GTFS)
"""
)

st.markdown("## 10 requêtes d’algèbre relationnelle (avec 2 divisions)")

queries_ra = [
    "1. σ route_type = 3 (ROUTES)  — lignes de bus",
    "2. π stop_id, stop_name (STOPS) — projection des arrêts",
    "3. TRIPS ⋈ ROUTES — courses avec informations de ligne",
    "4. STOP_TIMES ⋈ STOPS — horaires avec noms d’arrêts",
    "5. σ location_type = 1 (STOPS) — stations",
    "6. π route_id (TRIPS) — lignes ayant au moins une course",
    "7. (TRIPS ⋈ STOP_TIMES) ⋈ STOPS — parcours complets",
    "8. γ route_id, COUNT(trip_id) (TRIPS) — nombre de courses par ligne (préfiguration SQL agrégat)",
    "9. Division ÷ : lignes qui desservent TOUS les arrêts d’un ensemble cible",
    "10. Division ÷ : services actifs TOUS les jours ouvrés (lun→ven) sur une période donnée"
]

for q in queries_ra:
    st.write("-", q)

st.info("Les divisions seront traduites en SQL avec `NOT EXISTS` (technique classique en SQL).")
