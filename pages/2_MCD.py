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
# 1) Entités et attributs
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
        ["AGENCY", "ROUTE", "gère", "(0,N)", "(1,1)"],
        ["ROUTE", "TRIP", "possède", "(0,N)", "(1,1)"],
        ["SERVICE", "TRIP", "planifie", "(0,N)", "(1,1)"],
        ["SERVICE", "SERVICE_EXCEPTION", "a des exceptions", "(0,N)", "(1,1)"],
        ["TRIP", "STOP_TIME", "est composé de", "(1,N)", "(1,1)"],
        ["STOP", "STOP_TIME", "apparaît dans", "(0,N)", "(1,1)"],
        ["STOP (parent)", "STOP (enfant)", "parent_station", "(0,N)", "(0,1)"],
        ["STOP", "TRANSFER", "from_stop", "(0,N)", "(1,1)"],
        ["STOP", "TRANSFER", "to_stop", "(0,N)", "(1,1)"],
        ["STOP", "PATHWAY", "from_stop", "(0,N)", "(1,1)"],
        ["STOP", "PATHWAY", "to_stop", "(0,N)", "(1,1)"],
    ],
    columns=[
        "Entité A",
        "Entité B",
        "Association",
        "Cardinalité A",
        "Cardinalité B",
    ],
)

st.dataframe(assoc_df, use_container_width=True)

# -----------------------------
# 3) Diagramme MCD automatique (Graphviz)
# -----------------------------
st.subheader("3) Diagramme MCD")

dot = r"""
digraph MCD_GTFS {
    rankdir=LR;
    graph [fontsize=10, fontname="Helvetica", splines=true, overlap=false, pad=0.3];
    node  [shape=record, fontname="Helvetica", fontsize=10];
    edge  [fontname="Helvetica", fontsize=9, dir=none];

    AGENCY [label="{AGENCY|PK agency_id\lagency_name\lagency_url\lagency_timezone\lagency_lang\lagency_phone\lagency_email\l}"];
    ROUTE [label="{ROUTE|PK route_id\lFK agency_id\lroute_short_name\lroute_long_name\lroute_desc\lroute_type\lroute_color\lroute_text_color\l}"];
    SERVICE [label="{SERVICE|PK service_id\lmonday..sunday\lstart_date\lend_date\l}"];
    SERVICE_EXCEPTION [label="{SERVICE_EXCEPTION|PK/FK service_id\lPK date\lexception_type\l}"];
    TRIP [label="{TRIP|PK trip_id\lFK route_id\lFK service_id\ltrip_headsign\ltrip_short_name\ldirection_id\lblock_id\lwheelchair_accessible\lbikes_allowed\l}"];
    STOP [label="{STOP|PK stop_id\lstop_name\lstop_lat\lstop_lon\llocation_type\lFK parent_station\lzone_id\lwheelchair_boarding\lplatform_code\l}"];
    STOP_TIME [label="{STOP_TIME|PK/FK trip_id\lPK stop_sequence\lFK stop_id\larrival_time\ldeparture_time\lpickup_type\ldrop_off_type\ltimepoint\l}"];
    TRANSFER [label="{TRANSFER|PK transfer_id\lFK from_stop_id\lFK to_stop_id\ltransfer_type\lmin_transfer_time\l}"];
    PATHWAY [label="{PATHWAY|PK pathway_id\lFK from_stop_id\lFK to_stop_id\lpathway_mode\lis_bidirectional\ltraversal_time\llength_meters\l}"];

    // Relations principales
    AGENCY -> ROUTE [taillabel="(0,N)", headlabel="(1,1)", label="gère", labeldistance=2.2];
    ROUTE -> TRIP [taillabel="(0,N)", headlabel="(1,1)", label="possède", labeldistance=2.2];
    SERVICE -> TRIP [taillabel="(0,N)", headlabel="(1,1)", label="planifie", labeldistance=2.2];
    SERVICE -> SERVICE_EXCEPTION [taillabel="(0,N)", headlabel="(1,1)", label="a des exceptions", labeldistance=2.2];

    TRIP -> STOP_TIME [taillabel="(1,N)", headlabel="(1,1)", label="est composé de", labeldistance=2.2];
    STOP -> STOP_TIME [taillabel="(0,N)", headlabel="(1,1)", label="apparaît dans", labeldistance=2.2];

    // Auto-relation STOP
    STOP -> STOP [taillabel="(0,N)", headlabel="(0,1)", label="parent_station", color="gray40", labeldistance=2.0];

    // Transfers
    STOP -> TRANSFER [taillabel="(0,N)", headlabel="(1,1)", label="from_stop", color="gray35", labeldistance=2.0];
    STOP -> TRANSFER [taillabel="(0,N)", headlabel="(1,1)", label="to_stop", color="gray35", labeldistance=2.0];

    // Pathways
    STOP -> PATHWAY [taillabel="(0,N)", headlabel="(1,1)", label="from_stop", color="gray35", labeldistance=2.0];
    STOP -> PATHWAY [taillabel="(0,N)", headlabel="(1,1)", label="to_stop", color="gray35", labeldistance=2.0];
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
- Les cardinalités sont exprimées **à chaque extrémité** de la relation.
- `(0,N)` signifie : participation facultative, potentiellement multiple.
- `(1,1)` signifie : participation obligatoire et unique.
- `(1,N)` signifie : participation obligatoire et multiple.
- `(0,1)` signifie : participation facultative et unique.

### Interprétation métier
- Une **AGENCY** peut gérer zéro à plusieurs **ROUTE** ; une **ROUTE** appartient à une seule **AGENCY**.
- Une **ROUTE** peut avoir zéro à plusieurs **TRIP** ; un **TRIP** appartient à une seule **ROUTE**.
- Un **SERVICE** peut planifier zéro à plusieurs **TRIP** ; un **TRIP** dépend d’un seul **SERVICE**.
- Un **SERVICE** peut avoir zéro à plusieurs **SERVICE_EXCEPTION** ; chaque exception appartient à un seul service.
- Un **TRIP** est composé d’un ou plusieurs **STOP_TIME** ; chaque **STOP_TIME** appartient à un seul **TRIP**.
- Un **STOP** peut apparaître dans zéro à plusieurs **STOP_TIME** ; chaque **STOP_TIME** référence un seul **STOP**.
- Un **STOP parent** peut regrouper plusieurs **STOP enfants** ; un **STOP enfant** a au plus un **parent_station**.
- `TRANSFER` modélise les correspondances à pied entre arrêts.
- `PATHWAY` modélise les cheminements internes dans une station/gare.
"""
)

st.info(
    "Cette version est plus correcte pour un MCD, car les cardinalités sont "
    "portées par chaque extrémité de la relation et non fusionnées au milieu de l’arête."
)
