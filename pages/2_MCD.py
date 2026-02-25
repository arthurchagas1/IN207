import streamlit as st
import pandas as pd

st.set_page_config(page_title="MCD", page_icon="🧩", layout="wide")

st.title("🧩 Étape 1 — Modèle Conceptuel de Données (MCD)")
st.markdown(
    """
## Application métier
Système d'information pour l'analyse et l'exploitation des données de transport public
à partir d'un jeu de données **GTFS Île-de-France Mobilités**.

Le MCD ci-dessous modélise les principaux objets métier :
- agences de transport,
- lignes,
- services calendaires,
- courses (trips),
- arrêts / stations / accès,
- horaires de passage,
- correspondances à pied,
- cheminements internes en station.
"""
)

# -----------------------------
# 1) Entités et attributs (MCD)
# -----------------------------
st.subheader("1) Entités et attributs")

mcd_entities = {
    "AGENCY": [
        "agency_id (Identifiant)",
        "agency_name",
        "agency_url",
        "agency_timezone",
        "agency_lang",
        "agency_phone",
        "agency_email",
    ],
    "ROUTE": [
        "route_id (Identifiant)",
        "agency_id",
        "route_short_name",
        "route_long_name",
        "route_desc",
        "route_type",
        "route_color",
        "route_text_color",
    ],
    "SERVICE": [
        "service_id (Identifiant)",
        "monday ... sunday",
        "start_date",
        "end_date",
    ],
    "SERVICE_EXCEPTION": [
        "service_id",
        "date",
        "exception_type",
    ],
    "TRIP": [
        "trip_id (Identifiant)",
        "route_id",
        "service_id",
        "trip_headsign",
        "trip_short_name",
        "direction_id",
        "block_id",
        "wheelchair_accessible",
        "bikes_allowed",
    ],
    "STOP": [
        "stop_id (Identifiant)",
        "stop_name",
        "stop_lat",
        "stop_lon",
        "location_type",
        "parent_station",
        "zone_id",
        "wheelchair_boarding",
        "platform_code",
    ],
    "STOP_TIME": [
        "trip_id",
        "stop_sequence",
        "stop_id",
        "arrival_time",
        "departure_time",
        "pickup_type",
        "drop_off_type",
        "timepoint",
    ],
    "TRANSFER": [
        "transfer_id (Identifiant technique)",
        "from_stop_id",
        "to_stop_id",
        "transfer_type",
        "min_transfer_time",
    ],
    "PATHWAY": [
        "pathway_id (Identifiant)",
        "from_stop_id",
        "to_stop_id",
        "pathway_mode",
        "is_bidirectional",
        "traversal_time",
        "length_meters",
    ],
}

# Affichage en colonnes
cols = st.columns(3)
for i, (entity, attrs) in enumerate(mcd_entities.items()):
    with cols[i % 3]:
        st.markdown(f"### {entity}")
        for a in attrs:
            st.write(f"- {a}")

# -----------------------------
# 2) Associations et cardinalités
# -----------------------------
st.subheader("2) Associations et cardinalités")

assoc_df = pd.DataFrame(
    [
        ["AGENCY", "ROUTE", "Une agence gère plusieurs lignes", "1,N"],
        ["ROUTE", "TRIP", "Une ligne possède plusieurs courses", "1,N"],
        ["SERVICE", "TRIP", "Un service planifie plusieurs courses", "1,N"],
        ["SERVICE", "SERVICE_EXCEPTION", "Un service possède des exceptions de calendrier", "1,N"],
        ["TRIP", "STOP_TIME", "Une course est composée de passages horodatés", "1,N"],
        ["STOP", "STOP_TIME", "Un arrêt apparaît dans plusieurs passages", "1,N"],
        ["STOP", "STOP", "Hiérarchie station ↔ quai / accès (parent_station)", "1,N"],
        ["STOP", "TRANSFER", "Correspondance sortante (from_stop)", "1,N"],
        ["STOP", "TRANSFER", "Correspondance entrante (to_stop)", "1,N"],
        ["STOP", "PATHWAY", "Cheminement interne sortant", "1,N"],
        ["STOP", "PATHWAY", "Cheminement interne entrant", "1,N"],
    ],
    columns=["Entité A", "Entité B", "Association", "Cardinalité"],
)
st.dataframe(assoc_df, use_container_width=True)

# -----------------------------
# 3) Diagramme MCD automatique (Graphviz)
# -----------------------------
st.subheader("3) Diagramme MCD (généré automatiquement)")

dot = r"""
digraph MCD_GTFS {
    rankdir=LR;
    graph [fontsize=10, fontname="Helvetica", splines=true, overlap=false];
    node  [shape=record, fontname="Helvetica", fontsize=10];
    edge  [fontname="Helvetica", fontsize=9];

    AGENCY [label="{AGENCY|PK agency_id\lagency_name\lagency_url\lagency_timezone\lagency_lang\lagency_phone\lagency_email\l}"];
    ROUTE [label="{ROUTE|PK route_id\lFK agency_id\lroute_short_name\lroute_long_name\lroute_type\lroute_color\lroute_text_color\l}"];
    SERVICE [label="{SERVICE|PK service_id\lmonday..sunday\lstart_date\lend_date\l}"];
    SERVICE_EXCEPTION [label="{SERVICE_EXCEPTION|PK/FK service_id\lPK date\lexception_type\l}"];
    TRIP [label="{TRIP|PK trip_id\lFK route_id\lFK service_id\ltrip_headsign\ldirection_id\lblock_id\lwheelchair_accessible\lbikes_allowed\l}"];
    STOP [label="{STOP|PK stop_id\lstop_name\lstop_lat\lstop_lon\llocation_type\lFK parent_station\lzone_id\lwheelchair_boarding\lplatform_code\l}"];
    STOP_TIME [label="{STOP_TIME|PK/FK trip_id\lPK stop_sequence\lFK stop_id\larrival_time\ldeparture_time\lpickup_type\ldrop_off_type\ltimepoint\l}"];
    TRANSFER [label="{TRANSFER|PK transfer_id\lFK from_stop_id\lFK to_stop_id\ltransfer_type\lmin_transfer_time\l}"];
    PATHWAY [label="{PATHWAY|PK pathway_id\lFK from_stop_id\lFK to_stop_id\lpathway_mode\lis_bidirectional\ltraversal_time\llength_meters\l}"];

    // Relations principales
    AGENCY -> ROUTE [label="gère 1,N", arrowhead="crow", arrowsize=0.8];
    ROUTE -> TRIP [label="contient 1,N", arrowhead="crow", arrowsize=0.8];
    SERVICE -> TRIP [label="planifie 1,N", arrowhead="crow", arrowsize=0.8];
    SERVICE -> SERVICE_EXCEPTION [label="a des exceptions 1,N", arrowhead="crow", arrowsize=0.8];

    TRIP -> STOP_TIME [label="compose 1,N", arrowhead="crow", arrowsize=0.8];
    STOP -> STOP_TIME [label="dessert 1,N", arrowhead="crow", arrowsize=0.8];

    // Auto-relation stop (parent_station)
    STOP -> STOP [label="parent_station (1,N)", arrowhead="crow", arrowsize=0.7, color="gray40"];

    // Transfers et pathways
    STOP -> TRANSFER [label="from_stop (1,N)", arrowhead="crow", arrowsize=0.7, color="gray35"];
    STOP -> TRANSFER [label="to_stop (1,N)", arrowhead="crow", arrowsize=0.7, color="gray35"];

    STOP -> PATHWAY [label="from_stop (1,N)", arrowhead="crow", arrowsize=0.7, color="gray35"];
    STOP -> PATHWAY [label="to_stop (1,N)", arrowhead="crow", arrowsize=0.7, color="gray35"];
}
"""

st.graphviz_chart(dot, use_container_width=True)

# -----------------------------
# 4) Légende / interprétation
# -----------------------------
st.subheader("4) Légende et interprétation")

st.markdown(
    """
- **PK** : clé primaire  
- **FK** : clé étrangère  
- `STOP_TIME` est l'entité d'association entre **TRIP** et **STOP** (elle porte les horaires et l’ordre des arrêts).  
- `STOP` est une entité hiérarchique :
  - un **arrêt physique**,
  - une **station / gare**,
  - un **accès**,
  - etc. (selon `location_type`).
- `TRANSFER` modélise les correspondances à pied entre arrêts proches.
- `PATHWAY` modélise les cheminements internes (gare/station).
"""
)

st.info(
    "Ce MCD est suffisamment riche pour générer un MLD avec plus de 4 tables, "
    "et permet de construire des requêtes SQL variées (jointures, agrégations, divisions, etc.)."
)
