import streamlit as st
import pandas as pd

st.set_page_config(page_title="MLD", page_icon="🧱", layout="wide")

st.title("🧱 Étape 2 — Modèle Logique de Données (MLD)")

# =========================
# Schéma relationnel (table)
# =========================
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

# =========================
# Contraintes
# =========================
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

# =========================
# Algèbre relationnelle
# =========================
st.markdown("## 10 requêtes d’algèbre relationnelle (avec 2 divisions)")
st.info("✅ Render LaTeX: títulos/explicações em Markdown e fórmulas em `st.latex()`.")

st.markdown("### Notations")
st.markdown(
    r"""
- $\sigma$ : sélection  
- $\pi$ : projection  
- $\bowtie$ / $\bowtie_{\theta}$ : jointure (naturelle / condition)  
- $\rho$ : renommage  
- $\gamma$ : agrégation (group-by)  
- $\div$ : division  
"""
)

st.markdown("### Relations (extraits)")
st.latex(r"""
\begin{aligned}
&\texttt{ROUTES}(\texttt{route\_id}, \texttt{agency\_id}, \texttt{route\_short\_name}, \texttt{route\_long\_name}, \texttt{route\_type}, \dots)\\
&\texttt{TRIPS}(\texttt{trip\_id}, \texttt{route\_id}, \texttt{service\_id}, \texttt{trip\_headsign}, \texttt{direction\_id}, \dots)\\
&\texttt{STOPS}(\texttt{stop\_id}, \texttt{stop\_name}, \texttt{stop\_lat}, \texttt{stop\_lon}, \texttt{location\_type}, \texttt{parent\_station}, \dots)\\
&\texttt{STOP\_TIMES}(\texttt{trip\_id}, \texttt{stop\_sequence}, \texttt{stop\_id}, \texttt{arrival\_time}, \texttt{departure\_time}, \dots)\\
&\texttt{CALENDAR}(\texttt{service\_id}, \texttt{monday},\dots,\texttt{sunday}, \texttt{start\_date}, \texttt{end\_date})\\
&\texttt{CALENDAR\_DATES}(\texttt{service\_id}, \texttt{date}, \texttt{exception\_type})
\end{aligned}
""")

# Q1
st.markdown("### Q1 — Lignes de bus")
st.latex(r"Q_1 = \sigma_{\texttt{route\_type}=3}(\texttt{ROUTES})")
st.markdown("**Explication :** sélectionne uniquement les routes dont le type GTFS correspond au bus (ici 3).")

# Q2
st.markdown("### Q2 — Liste des arrêts (id + nom)")
st.latex(r"Q_2 = \pi_{\texttt{stop\_id},\texttt{stop\_name}}(\texttt{STOPS})")
st.markdown("**Explication :** projection minimale utile (affichage, menus, auto-complétion), sans ramener toutes les colonnes.")

# Q3
st.markdown("### Q3 — Courses enrichies par les infos de la ligne")
st.latex(r"Q_3 = \texttt{TRIPS} \bowtie_{\texttt{TRIPS.route\_id}=\texttt{ROUTES.route\_id}} \texttt{ROUTES}")
st.markdown("**Explication :** associe chaque course (`trip`) à sa route (nom, type, couleur).")

# Q4
st.markdown("### Q4 — Horaires avec noms d’arrêts")
st.latex(r"Q_4 = \texttt{STOP\_TIMES} \bowtie_{\texttt{STOP\_TIMES.stop\_id}=\texttt{STOPS.stop\_id}} \texttt{STOPS}")
st.markdown("**Explication :** jointure clé GTFS : transforme les horaires liés à `stop_id` en horaires lisibles (nom, station, etc.).")

# Q5
st.markdown("### Q5 — Stations uniquement")
st.latex(r"Q_5 = \sigma_{\texttt{location\_type}=1}(\texttt{STOPS})")
st.markdown("**Explication :** isole les objets « station » (parents) pour analyser hubs, correspondances et regroupements d’arrêts.")

# Q6
st.markdown("### Q6 — Routes ayant au moins une course")
st.latex(r"Q_6 = \pi_{\texttt{route\_id}}(\texttt{TRIPS})")
st.markdown("**Explication :** ensemble des routes réellement utilisées par au moins un trip (utile pour vérifier l’activité).")

# Q7
st.markdown("### Q7 — Parcours complet (trip + stops + horaires)")
st.latex(r"""
Q_7 =
\Big(
(\texttt{TRIPS} \bowtie_{\texttt{TRIPS.trip\_id}=\texttt{STOP\_TIMES.trip\_id}} \texttt{STOP\_TIMES})
\bowtie_{\texttt{STOP\_TIMES.stop\_id}=\texttt{STOPS.stop\_id}} \texttt{STOPS}
\Big)
""")
st.latex(r"Q_7' = Q_7 \bowtie_{\texttt{TRIPS.route\_id}=\texttt{ROUTES.route\_id}} \texttt{ROUTES}")
st.markdown(
    "**Explication :** reconstruit un trajet lisible d’une course : "
    "ordre (`stop_sequence`), arrêts, horaires (et optionnellement la route)."
)

# Q8
st.markdown("### Q8 — Nombre de courses par ligne (agrégation)")
st.latex(r"Q_8 = \gamma_{\texttt{route\_id};\; \textsf{COUNT}(\texttt{trip\_id})\rightarrow \texttt{nb\_trips}}(\texttt{TRIPS})")
st.markdown("**Explication :** mesure l’intensité de service : combien de trips sont associés à chaque route.")

# Q9
st.markdown("### Q9 — Division : routes qui desservent tous les arrêts d’un ensemble cible")
st.markdown("On construit d’abord la relation **ROUTE_STOP(route_id, stop_id)** :")
st.latex(r"""
\texttt{ROUTE\_STOP} =
\pi_{\texttt{TRIPS.route\_id},\texttt{STOP\_TIMES.stop\_id}}
(\texttt{TRIPS} \bowtie_{\texttt{TRIPS.trip\_id}=\texttt{STOP\_TIMES.trip\_id}} \texttt{STOP\_TIMES})
""")
st.markdown("Soit **TARGET_STOPS(stop_id)** l’ensemble des arrêts cibles (table/paramètre).")
st.latex(r"Q_9 = \texttt{ROUTE\_STOP} \div \texttt{TARGET\_STOPS}")
st.markdown(
    "**Explication :** retourne les `route_id` telles que **chaque** arrêt cible apparaît parmi les arrêts desservis "
    "(logique de couverture « tous les éléments requis »)."
)

# Q10
st.markdown("### Q10 — Division : services actifs tous les jours ouvrés (lun→ven) sur une période")
st.markdown(
    "Soit **WD(date)** l’ensemble des dates ouvrées entre $d_{min}$ et $d_{max}$ "
    "(conceptuellement généré à partir du calendrier)."
)
st.latex(r"\texttt{WD(date)} = \{\text{toutes les dates ouvrées entre } d_{min}\text{ et } d_{max}\}")
st.markdown(
    "On définit (conceptuellement) **ACTIVE(service_id, date)** (patron `CALENDAR` + exceptions `CALENDAR_DATES`)."
)
st.latex(r"Q_{10} = \texttt{ACTIVE} \div \texttt{WD}")
st.markdown(
    "**Explication :** renvoie les `service_id` actifs pour **toutes** les dates ouvrées de la période. "
    "En SQL, on traduit typiquement la division avec une double négation via `NOT EXISTS`."
)

st.success("✅ Tout le LaTeX est rendu via `st.latex()` (plus de rendu « texto quebrado »).")
