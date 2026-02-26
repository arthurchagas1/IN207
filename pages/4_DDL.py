import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Dict, Optional

st.set_page_config(page_title="DDL", page_icon="🛠️", layout="wide")

DB_PATH = "database.db"
DATA_DIR = Path("data")

GTFS_FILES = [
    "agency.txt",
    "routes.txt",
    "trips.txt",
    "calendar.txt",
    "calendar_dates.txt",
    "stops.txt",
    "stop_times.txt",
    "transfers.txt",
    "pathways.txt",
    "stop_extensions.txt",
    "booking_rules.txt",
    "ticketing_deep_links.txt",
]

DATE_COLUMNS = {
    "calendar.txt": ["start_date", "end_date"],
    "calendar_dates.txt": ["date"],
}
TIME_COLUMNS = {
    "stop_times.txt": ["arrival_time", "departure_time"],
}

def parse_gtfs_time_to_seconds(val: Optional[str]) -> Optional[int]:
    if pd.isna(val) or val is None or str(val).strip() == "":
        return None
    try:
        h, m, s = map(int, str(val).split(":"))
        return h * 3600 + m * 60 + s
    except Exception:
        return None

def read_gtfs_folder(data_dir: Path) -> Dict[str, pd.DataFrame]:
    dfs = {}
    if not data_dir.exists():
        raise FileNotFoundError("Le dossier data/ est introuvable.")
    for fname in GTFS_FILES:
        fpath = data_dir / fname
        if not fpath.exists():
            continue
        df = pd.read_csv(fpath, dtype=str, keep_default_na=False, na_values=[""])
        df.columns = [c.strip() for c in df.columns]
        for c in DATE_COLUMNS.get(fname, []):
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], format="%Y%m%d", errors="coerce")
        for c in TIME_COLUMNS.get(fname, []):
            if c in df.columns:
                df[f"{c}_secs"] = df[c].apply(parse_gtfs_time_to_seconds)
        dfs[fname] = df
    return dfs

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["stop_lat", "stop_lon"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in [
        "route_type", "direction_id", "wheelchair_accessible", "bikes_allowed",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "exception_type", "stop_sequence", "pickup_type", "drop_off_type", "timepoint",
        "location_type", "wheelchair_boarding", "transfer_type", "min_transfer_time",
        "pathway_mode", "is_bidirectional", "stair_count", "traversal_time"
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def save_sqlite(dfs: Dict[str, pd.DataFrame], db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        # Supprimer tables si existantes
        cur = conn.cursor()
        for t in [
            "agency","routes","service","calendar","calendar_dates","trips","stops",
            "stop_times","transfers","pathways","stop_extensions","booking_rules",
            "ticketing_deep_links"
        ]:
            cur.execute(f"DROP TABLE IF EXISTS {t};")
        conn.commit()

        # Créer table service (métier, pour intégrer service_id)
        cur.execute("CREATE TABLE service (service_id TEXT PRIMARY KEY);")
        conn.commit()

        # Sauvegarde brute des tables GTFS (to_sql)
        for fname, df in dfs.items():
            table = Path(fname).stem.lower()
            normalize(df).to_sql(table, conn, if_exists="replace", index=False)

        # Alimenter service depuis calendar + calendar_dates si présents
        service_ids = set()
        if "calendar.txt" in dfs and "service_id" in dfs["calendar.txt"].columns:
            service_ids.update(dfs["calendar.txt"]["service_id"].dropna().astype(str).tolist())
        if "calendar_dates.txt" in dfs and "service_id" in dfs["calendar_dates.txt"].columns:
            service_ids.update(dfs["calendar_dates.txt"]["service_id"].dropna().astype(str).tolist())

        if service_ids:
            pd.DataFrame({"service_id": sorted(service_ids)}).to_sql("service", conn, if_exists="replace", index=False)

        # Index utiles (performance)
        index_sql = [
            "CREATE INDEX IF NOT EXISTS idx_routes_agency ON routes(agency_id);",
            "CREATE INDEX IF NOT EXISTS idx_trips_route ON trips(route_id);",
            "CREATE INDEX IF NOT EXISTS idx_trips_service ON trips(service_id);",
            "CREATE INDEX IF NOT EXISTS idx_stops_parent ON stops(parent_station);",
            "CREATE INDEX IF NOT EXISTS idx_stop_times_trip ON stop_times(trip_id);",
            "CREATE INDEX IF NOT EXISTS idx_stop_times_stop ON stop_times(stop_id);",
            "CREATE INDEX IF NOT EXISTS idx_stop_times_seq ON stop_times(trip_id, stop_sequence);",
            "CREATE INDEX IF NOT EXISTS idx_transfers_from ON transfers(from_stop_id);",
            "CREATE INDEX IF NOT EXISTS idx_transfers_to ON transfers(to_stop_id);",
            "CREATE INDEX IF NOT EXISTS idx_pathways_from ON pathways(from_stop_id);",
            "CREATE INDEX IF NOT EXISTS idx_pathways_to ON pathways(to_stop_id);",
        ]
        for q in index_sql:
            cur.execute(q)
        conn.commit()
    finally:
        conn.close()

def table_counts(db_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        q = """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
        """
        tables = pd.read_sql_query(q, conn)["name"].tolist()
        rows = []
        for t in tables:
            n = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {t}", conn)["n"][0]
            rows.append((t, int(n)))
        return pd.DataFrame(rows, columns=["table", "nb_lignes"])
    finally:
        conn.close()

def get_table_columns(db_path: str, table: str) -> pd.DataFrame:
    """Retourne le schéma (colonnes) d'une table SQLite."""
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(f"PRAGMA table_info({table});", conn)
    finally:
        conn.close()

def run_sql(db_path: str, sql: str):
    """Exécute une instruction SQL (INSERT/UPDATE/DELETE/DDL)."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()

st.title("🛠️ Étape 3 — DDL : Création et peuplement de la base")

st.markdown(
    """
Cette page :
1. charge automatiquement les fichiers `.txt` depuis `data/`
2. crée / réinitialise `database.db`
3. insère les données dans SQLite
4. ajoute des index pour accélérer les requêtes
"""
)

col1, col2 = st.columns([1, 1])

with col1:
    st.write("**Dossier de données** :", DATA_DIR.resolve())
    st.write("**Base SQLite** :", Path(DB_PATH).resolve())

with col2:
    st.code(
        """
Exemple de DDL (conceptuel) :
CREATE TABLE routes (
  route_id TEXT PRIMARY KEY,
  agency_id TEXT,
  route_short_name TEXT,
  route_long_name TEXT,
  route_type INTEGER
);
""",
        language="sql"
    )

if st.button("🔄 Créer / réinitialiser la base et charger les données"):
    try:
        with st.spinner("Chargement des fichiers GTFS..."):
            dfs = read_gtfs_folder(DATA_DIR)
        with st.spinner("Création de la base SQLite..."):
            save_sqlite(dfs, DB_PATH)
        st.success("Base créée et données chargées avec succès ✅")
    except Exception as e:
        st.error(f"Erreur : {e}")

if Path(DB_PATH).exists():
    st.subheader("Contenu de la base")
    try:
        st.dataframe(table_counts(DB_PATH), use_container_width=True)
    except Exception as e:
        st.warning(f"Impossible de lire la base : {e}")

    # =========================
    # Exemple d'INSERT
    # =========================
    st.markdown("## Exemple pédagogique : INSERT")
    st.markdown(
        """
Comme la base est alimentée automatiquement via `to_sql()`, on ne voit pas explicitement des `INSERT`.
Ci-dessous, on montre un exemple concret **sur la table `agency`** (si elle existe).
"""
    )

    # Vérifie présence de la table agency
    existing_tables = set(table_counts(DB_PATH)["table"].tolist())
    if "agency" in existing_tables:
        st.markdown("### Schéma de `agency` (colonnes)")
        st.dataframe(get_table_columns(DB_PATH, "agency"), use_container_width=True)

        st.markdown("### INSERT (exemple)")
        st.code(
            """
INSERT INTO agency (agency_id, agency_name, agency_url, agency_timezone, agency_lang, agency_phone)
VALUES ('demo_agency', 'Agence Démo', 'https://example.org', 'Europe/Paris', 'fr', '+33 1 23 45 67 89');
""".strip(),
            language="sql",
        )

        st.warning(
            "⚠️ Cet INSERT ne marchera que si les colonnes listées existent dans ta version de `agency.txt` "
            "et si `agency_id='demo_agency'` n’existe pas déjà (sinon, contrainte d’unicité si applicable)."
        )

        if st.button("▶️ Exécuter l'INSERT démo dans agency"):
            try:
                rowcount = run_sql(
                    DB_PATH,
                    """
INSERT INTO agency (agency_id, agency_name, agency_url, agency_timezone, agency_lang, agency_phone)
VALUES ('demo_agency', 'Agence Démo', 'https://example.org', 'Europe/Paris', 'fr', '+33 1 23 45 67 89');
""".strip(),
                )
                st.success(f"INSERT exécuté ✅ (rowcount={rowcount})")
                st.dataframe(table_counts(DB_PATH), use_container_width=True)
            except Exception as e:
                st.error(f"Erreur INSERT : {e}")

        st.markdown("### Vérifier l'insertion (SELECT)")
        st.code(
            "SELECT * FROM agency WHERE agency_id = 'demo_agency';",
            language="sql",
        )
        if st.button("🔎 Afficher la ligne insérée (SELECT)"):
            try:
                conn = sqlite3.connect(DB_PATH)
                df_demo = pd.read_sql_query(
                    "SELECT * FROM agency WHERE agency_id = 'demo_agency';",
                    conn,
                )
                conn.close()
                st.dataframe(df_demo, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur SELECT : {e}")
    else:
        st.info("La table `agency` n'existe pas dans la base actuelle (fichier agency.txt absent).")

st.markdown("## Remarque pédagogique")
st.info(
    "Dans un vrai projet, on écrirait les `CREATE TABLE` manuellement avec toutes les contraintes "
    "(`PRIMARY KEY`, `FOREIGN KEY`, `CHECK`, etc.). Ici, on illustre le peuplement rapide depuis GTFS."
)
