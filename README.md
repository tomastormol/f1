# 🏎️ F1 Data Pipeline

End-to-end data pipeline for Formula 1 analytics using the 2023 season data.

## 🏗️ Architecture
FastF1 API
↓
Python + Pandas (extraction & transformation)
↓
PostgreSQL (storage)
↓
dbt (Silver/Gold models)
↓
FastAPI + React (coming soon)

## 🛠️ Tech Stack

- **Data source:** FastF1 (official F1 data)
- **Orchestration:** Apache Airflow (coming soon)
- **Processing:** Python, Pandas
- **Storage:** PostgreSQL
- **Transformation:** dbt
- **API:** FastAPI (coming soon)
- **Dashboard:** React (coming soon)

## 📊 Dataset

- **Season:** 2023 (22 Grand Prix)
- **Tables:** events, qualifying, race_results, laps
- **Total laps:** ~28,000+

## ⚙️ Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip3 install fastf1 pandas sqlalchemy psycopg2-binary dbt-postgres jupyter

# 3. Create database
createdb f1_data

# 4. Run extraction pipeline
python src/extract.py

# 5. Run dbt models
cd f1_dbt
dbt run
```

## 📁 Project Structure

```
├── src/
│   └── extract.py
├── notebooks/
│   └── 01_explore_fastf1.ipynb
├── f1_dbt/
│   └── models/
│       ├── staging/
│       └── mart/
└── DEV_NOTES.md
```