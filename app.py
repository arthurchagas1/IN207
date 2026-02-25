import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Dict, Optional

st.set_page_config(page_title="GTFS IDFM Loader", layout="wide")

# Pasta local com os arquivos .txt
DATA_DIR = Path("data")

# Arquivos GTFS esperados (IDFM + extensões)
GTFS_FILES = [
    "agency.txt",
    "routes.txt",
    "trips.txt",
    "calendar.txt",
    "calendar_dates.txt",
    "stops.txt",
    "stop_times.txt",
    "transfers.txt",
    "stop_extensions.txt",
    "pathways.txt",
    "booking_rules.txt",
    "ticketing_deep_links.txt",
]

DATE_COLUMNS = {
    "calendar.txt": ["start_date", "end_date"],
    "calendar_dates.txt": ["date"],  # alguns feeds usam "date"
}

TIME_COLUMNS = {
    "stop_times.txt": ["arrival_time", "departure_time"],
}


def parse_gtfs_time_to_seconds(val: Optional[str]) -> Optional[int]:
    """Converte HH:MM:SS GTFS em segundos (aceita >24h)."""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return None
    try:
        h, m, s = map(int, str(val).strip().split(":"))
        return h * 3600 + m * 60 + s
    except Exception:
        return None


def read_gtfs_folder(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """Lê os .txt GTFS da pasta local."""
    dataframes = {}

    if not data_dir.exists() or not data_dir.is_dir():
        raise FileNotFoundError(f"Pasta não encontrada: {data_dir.resolve()}")

    for fname in GTFS_FILES:
        fpath = data_dir / fname
        if not fpath.exists():
            continue

        # Ler tudo como string primeiro
        df = pd.read_csv(fpath, dtype=str, keep_default_na=False, na_values=[""])
        df.columns = [c.strip() for c in df.columns]

        # Datas GTFS (YYYYMMDD)
        for col in DATE_COLUMNS.get(fname, []):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format="%Y%m%d", errors="coerce")

        # Horários GTFS -> segundos
        for col in TIME_COLUMNS.get(fname, []):
            if col in df.columns:
                df[f"{col}_secs"] = df[col].apply(parse_gtfs_time_to_seconds)

        dataframes[fname] = df

    return dataframes


def normalize_dtypes(dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    out = {}

    numeric_candidates = [
        "route_type", "direction_id", "wheelchair_accessible", "bikes_allowed",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "exception_type", "stop_sequence", "pickup_type", "drop_off_type", "timepoint",
        "location_type", "wheelchair_boarding", "transfer_type", "min_transfer_time",
        "pathway_mode", "is_bidirectional", "stair_count", "traversal_time",
        "length", "max_slope", "min_width", "length_meters"
    ]

    for fname, df in dataframes.items():
        df = df.copy()

        # Converter números quando existir
        for col in numeric_candidates:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Lat/Lon
        for col in ["stop_lat", "stop_lon"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        out[fname] = df

    return out


def save_to_sqlite(dataframes: Dict[str, pd.DataFrame], db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        for fname, df in dataframes.items():
            table_name = Path(fname).stem.lower()
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()


def basic_quality_checks(dataframes: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    checks = {}

    if "trips.txt" in dataframes and "routes.txt" in dataframes:
        trips = dataframes["trips.txt"]
        routes = dataframes["routes.txt"]
        if "route_id" in trips.columns and "route_id" in routes.columns:
            checks["trips.route_id sem match em routes"] = int((~trips["route_id"].isin(routes["route_id"])).sum())

    if "stop_times.txt" in dataframes and "stops.txt" in dataframes:
        st = dataframes["stop_times.txt"]
        stops = dataframes["stops.txt"]
        if "stop_id" in st.columns and "stop_id" in stops.columns:
            checks["stop_times.stop_id sem match em stops"] = int((~st["stop_id"].isin(stops["stop_id"])).sum())

    if "stop_times.txt" in dataframes and "trips.txt" in dataframes:
        st = dataframes["stop_times.txt"]
        trips = dataframes["trips.txt"]
        if "trip_id" in st.columns and "trip_id" in trips.columns:
            checks["stop_times.trip_id sem match em trips"] = int((~st["trip_id"].isin(trips["trip_id"])).sum())

    if "stops.txt" in dataframes:
        stops = dataframes["stops.txt"]
        if "parent_station" in stops.columns and "stop_id" in stops.columns:
            parent_vals = stops["parent_station"].dropna().astype(str)
            parent_vals = parent_vals[parent_vals.str.strip() != ""]
            checks["stops.parent_station sem match em stops"] = int((~parent_vals.isin(stops["stop_id"])).sum())

    return checks


def compute_kpis(dataframes: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    def nrows(file):
        return len(dataframes[file]) if file in dataframes else 0

    kpis = {
        "Agências": nrows("agency.txt"),
        "Linhas": nrows("routes.txt"),
        "Viagens": nrows("trips.txt"),
        "Stops": nrows("stops.txt"),
        "Stop Times": nrows("stop_times.txt"),
        "Transfers": nrows("transfers.txt"),
        "Pathways": nrows("pathways.txt"),
    }

    if "stops.txt" in dataframes and "location_type" in dataframes["stops.txt"].columns:
        lt = dataframes["stops.txt"]["location_type"].fillna(-1)
        kpis["Stops físicos (0)"] = int((lt == 0).sum())
        kpis["Estações (1)"] = int((lt == 1).sum())
        kpis["Acessos (2)"] = int((lt == 2).sum())

    return kpis


def top_routes_by_trip_count(dataframes: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    if "trips.txt" not in dataframes or "route_id" not in dataframes["trips.txt"].columns:
        return pd.DataFrame()

    trips = dataframes["trips.txt"].copy()
    agg = trips.groupby("route_id", dropna=False).size().reset_index(name="trip_count")

    if "routes.txt" in dataframes:
        routes = dataframes["routes.txt"].copy()
        cols = [c for c in ["route_id", "route_short_name", "route_long_name", "route_type"] if c in routes.columns]
        if cols:
            agg = agg.merge(routes[cols], on="route_id", how="left")

    return agg.sort_values("trip_count", ascending=False).head(20)


def service_date_range(dataframes: Dict[str, pd.DataFrame]):
    if "calendar.txt" not in dataframes:
        return None, None
    cal = dataframes["calendar.txt"]
    if "start_date" not in cal.columns or "end_date" not in cal.columns:
        return None, None
    return cal["start_date"].min(), cal["end_date"].max()


# -----------------------------
# UI
# -----------------------------
st.title("🚇 GTFS IDFM Loader (pasta local)")
st.caption("Carregamento automático da pasta `data/` + SQLite + análise rápida")

db_name = st.text_input("Nome do banco SQLite de saída", value="gtfs_idfm.sqlite")

if st.button("🔄 Recarregar dados da pasta data/") or "dfs" not in st.session_state:
    try:
        with st.spinner(f"Lendo arquivos de {DATA_DIR.resolve()} ..."):
            dfs = read_gtfs_folder(DATA_DIR)
            dfs = normalize_dtypes(dfs)
            st.session_state["dfs"] = dfs
        st.success(f"Arquivos carregados: {len(st.session_state['dfs'])}")
    except Exception as e:
        st.error(f"Erro ao carregar pasta data/: {e}")

dfs = st.session_state.get("dfs", {})

if dfs:
    # Arquivos encontrados
    st.subheader("Arquivos encontrados")
    found_files = pd.DataFrame({
        "arquivo": list(dfs.keys()),
        "linhas": [len(v) for v in dfs.values()],
        "colunas": [len(v.columns) for v in dfs.values()],
    })
    st.dataframe(found_files, use_container_width=True)

    # KPIs
    st.subheader("KPIs iniciais")
    kpis = compute_kpis(dfs)
    cols = st.columns(4)
    for i, (k, v) in enumerate(kpis.items()):
        cols[i % 4].metric(k, f"{v:,}".replace(",", "."))

    # Período de serviço
    min_d, max_d = service_date_range(dfs)
    if min_d is not None and max_d is not None:
        st.info(f"Período de `calendar.txt`: **{min_d.date()}** até **{max_d.date()}**")

    # Integridade
    st.subheader("Checagens rápidas")
    checks = basic_quality_checks(dfs)
    if checks:
        st.dataframe(pd.DataFrame(checks.items(), columns=["checagem", "qtd_problemas"]), use_container_width=True)

    # Top rotas
    st.subheader("Top 20 linhas por número de trips")
    top_routes = top_routes_by_trip_count(dfs)
    if not top_routes.empty:
        st.dataframe(top_routes, use_container_width=True)
    else:
        st.write("Sem dados suficientes.")

    # Preview de tabela
    st.subheader("Preview")
    table_choice = st.selectbox("Escolha a tabela", list(dfs.keys()))
    st.dataframe(dfs[table_choice].head(100), use_container_width=True)

    # Salvar SQLite
    if st.button("💾 Salvar em SQLite"):
        try:
            with st.spinner("Gravando banco SQLite..."):
                save_to_sqlite(dfs, db_name)
            st.success(f"Banco salvo: {db_name}")

            with open(db_name, "rb") as f:
                st.download_button(
                    "⬇️ Baixar SQLite",
                    data=f,
                    file_name=db_name,
                    mime="application/octet-stream"
                )
        except Exception as e:
            st.error(f"Erro ao salvar SQLite: {e}")

else:
    st.warning(f"Nenhum arquivo GTFS foi carregado de `{DATA_DIR}`.")
    st.markdown("""
    Verifique se a pasta `data/` existe na mesma pasta do `app.py` e contém arquivos como:
    - `agency.txt`
    - `routes.txt`
    - `trips.txt`
    - `stops.txt`
    - `stop_times.txt`
    """)
