# IN207 — GTFS Île-de-France (SQLite Database + Streamlit App)

This project is a pedagogical Streamlit application that demonstrates the end-to-end workflow of building a relational database from GTFS (General Transit Feed Specification) public-transport data (Île-de-France context), then exploring it through data modeling, DDL, SQL queries, and dashboarding.

The app is structured as a multi-page Streamlit website:
1. MCD (Conceptual Data Model)
2. MLD (Logical Data Model + relational algebra)
3. DDL (SQLite creation + population + indexes + INSERT example)
4. SQL queries (including relational division translated with NOT EXISTS)
5. Valorisation / dashboard (KPIs + charts + optional maps)

---

## Key Features

### Conceptual & Logical Modeling
- MCD and MLD presented in an educational format
- Integrity constraints highlighted (entity + referential + business constraints)

### Relational Algebra (RA)
- 10 relational algebra queries including 2 divisions
- Rendered using Streamlit’s native LaTeX support (`st.latex()`)

### Database Creation (DDL) & Population
- Loads GTFS `.txt` files from `data/`
- Creates / resets a local SQLite database: `database.db`
- Imports tables using Pandas `to_sql`
- Normalizes numeric columns (route types, coordinates, flags…)
- Adds performance indexes
- Includes a pedagogical INSERT example (and optional execution)

### SQL Querying
- Join queries (`trips ⋈ routes`, `stop_times ⋈ stops`, etc.)
- Aggregations (`GROUP BY`, `COUNT`, top-k analyses)
- Division patterns using `NOT EXISTS` (classic SQL approach)

---

## Repository Structure

Filenames may differ slightly depending on your submission structure, but the project typically follows this layout:

~~~text
.
├─ app.py                        # Streamlit entrypoint (or main.py)
├─ pages/
│  ├─ 2_MCD.py                    # Conceptual model
│  ├─ 3_MLD.py                    # Logical model + relational algebra (LaTeX)
│  ├─ 4_DDL.py                    # SQLite loading + indexes + INSERT example
│  ├─ 5_Requetes_SQL.py           # SQL queries + free query editor (optional)
│  └─ 6_Valorisation.py           # Dashboard (optional)
├─ data/
│  ├─ agency.txt
│  ├─ routes.txt
│  ├─ trips.txt
│  ├─ calendar.txt
│  ├─ calendar_dates.txt
│  ├─ stops.txt
│  ├─ stop_times.txt
│  ├─ transfers.txt
│  ├─ pathways.txt
│  ├─ stop_extensions.txt
│  ├─ booking_rules.txt
│  └─ ticketing_deep_links.txt
└─ database.db                    # generated after running the DDL step
~~~

---

## Requirements

- Python 3.9+ recommended
- Main dependencies:
  - streamlit
  - pandas

Optional (if you use diagrams):
- graphviz (Python package + system dependency, depending on OS)

---

## Setup & Run

### 1) Create a virtual environment (recommended)

macOS/Linux:
~~~bash
python -m venv .venv
source .venv/bin/activate
~~~

Windows (PowerShell):
~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
~~~

### 2) Install dependencies

~~~bash
pip install --upgrade pip
pip install streamlit pandas
~~~

(Optional, if you use graphviz diagrams)
~~~bash
pip install graphviz
# You may also need to install Graphviz using your OS package manager.
~~~

### 3) Run the Streamlit app

From the project root:
~~~bash
streamlit run app.py
~~~

---

## Data Setup (GTFS)

Place all GTFS `.txt` files inside the `data/` directory.

The loader checks for these filenames (missing files are skipped):
- `agency.txt`
- `routes.txt`
- `trips.txt`
- `calendar.txt`
- `calendar_dates.txt`
- `stops.txt`
- `stop_times.txt`
- `transfers.txt`
- `pathways.txt`
- `stop_extensions.txt`
- `booking_rules.txt`
- `ticketing_deep_links.txt`

GTFS-specific handling included in the loader:
- Dates parsed from `YYYYMMDD`:
  - `calendar.start_date`, `calendar.end_date`
  - `calendar_dates.date`
- Times may exceed `24:00:00` (valid in GTFS):
  - additional columns: `stop_times.arrival_time_secs`, `stop_times.departure_time_secs`

---

## Building the SQLite Database (DDL)

Once the app is running:
1. Open the page: **“Étape 3 — DDL”**
2. Click: **“Créer / réinitialiser la base et charger les données”**
3. The app will:
   - drop existing tables (if any)
   - create a `service` table
   - load GTFS tables into SQLite
   - create helpful indexes

A summary table displays the number of rows per table.

---

## Example INSERT (Pedagogical)

Example shown in the UI:

~~~sql
INSERT INTO agency (agency_id, agency_name, agency_url, agency_timezone, agency_lang, agency_phone)
VALUES ('demo_agency', 'Agence Démo', 'https://example.org', 'Europe/Paris', 'fr', '+33 1 23 45 67 89');
~~~

Note: This INSERT only works if those columns exist in your `agency` table, and if `demo_agency` is not already present.

---

## Relational Division in SQL (NOT EXISTS)

Relational division (÷) is not a built-in SQL operator. The classic translation uses double negation with `NOT EXISTS`.

Pattern:

~~~sql
SELECT x
FROM R_candidates c
WHERE NOT EXISTS (
  SELECT 1
  FROM Required r
  WHERE NOT EXISTS (
    SELECT 1
    FROM R
    WHERE R.x = c.x AND R.y = r.y
  )
);
~~~

Used for queries like:
- routes that serve all stops from a target set
- services active on all weekdays in a given period

---

## Troubleshooting

### `data/` folder not found
Create it and place the GTFS `.txt` files inside:
~~~bash
mkdir data
~~~

### `database.db` does not exist
Run the DDL step in the app:
- **“Étape 3 — DDL”** → **“Créer / réinitialiser…”**

### LaTeX is displayed as plain text
Streamlit supports LaTeX, but block formulas should be rendered with `st.latex()`.
When editing code, prefer raw strings: `r"..."` or `r"""..."""`.

### SQLite tables differ from expected
GTFS feeds can vary:
- some columns may be absent depending on the dataset
- the loader uses `to_sql`, so the schema mirrors the input files

---

## License

Educational project for IN207. Add a license if you plan to publish or reuse publicly.

---

## Acknowledgements
- GTFS: General Transit Feed Specification
- Dataset: Île-de-France public-transport GTFS feed
- Streamlit for the interactive web interface
- SQLite for lightweight relational storage
