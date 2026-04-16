import fastf1
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

# Configuración
CACHE_PATH = Path("data/raw/cache")
CACHE_PATH.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_PATH))

DB_URL = "postgresql://tomas@localhost:5432/f1_data"
engine = create_engine(DB_URL)

def extract_event(year: int, round_number: int) -> dict:
    """
    Extrae todos los datos de un GP completo.
    Devuelve un diccionario con DataFrames listos para cargar.
    """
    print(f"📡 Cargando GP {round_number} de {year}...")

    # Cargar sesiones
    qualifying = fastf1.get_session(year, round_number, 'Q')
    race = fastf1.get_session(year, round_number, 'R')

    qualifying.load()
    race.load()

    # --- EVENT ---
    event_data = {
        'event_id': f"{year}_{round_number:02d}",
        'year': year,
        'round': round_number,
        'event_name': race.event['EventName'],
        'circuit': race.event['Location'],
        'country': race.event['Country'],
        'date': race.date.date()
    }
    events_df = pd.DataFrame([event_data])

    # --- QUALIFYING ---
    qual_results = qualifying.results[[
        'Abbreviation', 'FullName', 'TeamName',
        'TeamColor', 'Position', 'Q1', 'Q2', 'Q3'
    ]].copy()

    qual_results.columns = [
        'driver_abbr', 'full_name', 'team_name',
        'team_color', 'position', 'q1_time', 'q2_time', 'q3_time'
    ]

    # Convertir tiempos a segundos
    for col in ['q1_time', 'q2_time', 'q3_time']:
        qual_results[col] = pd.to_timedelta(qual_results[col]).dt.total_seconds()

    qual_results['best_time'] = qual_results[['q1_time', 'q2_time', 'q3_time']].min(axis=1)
    qual_results['event_id'] = event_data['event_id']

    # --- RACE RESULTS ---
    race_results = race.results[[
        'Abbreviation', 'FullName', 'TeamName', 'TeamColor',
        'Position', 'GridPosition', 'Time', 'Status', 'Points'
    ]].copy()

    race_results.columns = [
        'driver_abbr', 'full_name', 'team_name', 'team_color',
        'position', 'grid_position', 'time', 'status', 'points'
    ]

    race_results['time'] = pd.to_timedelta(race_results['time']).dt.total_seconds()
    race_results['event_id'] = event_data['event_id']

    # --- LAPS ---
    def process_laps(session, session_type):
        laps = session.laps[[
            'Driver', 'LapNumber', 'LapTime',
            'Sector1Time', 'Sector2Time', 'Sector3Time',
            'IsPersonalBest', 'Compound', 'TyreLife',
            'FreshTyre', 'Position', 'Deleted'
        ]].copy()

        laps.columns = [
            'driver_abbr', 'lap_number', 'lap_time',
            'sector1_time', 'sector2_time', 'sector3_time',
            'is_personal_best', 'compound', 'tyre_life',
            'fresh_tyre', 'position', 'is_deleted'
        ]

        # Convertir tiempos a segundos
        for col in ['lap_time', 'sector1_time', 'sector2_time', 'sector3_time']:
            laps[col] = pd.to_timedelta(laps[col]).dt.total_seconds()

        laps['session_type'] = session_type
        laps['event_id'] = event_data['event_id']

        return laps

    qual_laps = process_laps(qualifying, 'Q')
    race_laps = process_laps(race, 'R')
    laps_df = pd.concat([qual_laps, race_laps], ignore_index=True)

    return {
        'events': events_df,
        'qualifying': qual_results,
        'race_results': race_results,
        'laps': laps_df
    }


def load_to_postgres(data: dict):
    """Carga todos los DataFrames en PostgreSQL."""
    for table_name, df in data.items():
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='append',
            index=False,
            chunksize=1000
        )
        print(f"✅ {table_name}: {len(df):,} filas cargadas")


if __name__ == "__main__":
    from sqlalchemy import text

    year = 2023
    total_rounds = 22

    for round_number in range(1, total_rounds + 1):
        event_id = f"{year}_{round_number:02d}"

        # Verificar si el GP ya está cargado
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM events WHERE event_id = '{event_id}'")
            )
            already_loaded = result.fetchone()[0] > 0

        if already_loaded:
            print(f"⏭️  Round {round_number} ya existe, saltando...")
            continue

        try:
            data = extract_event(year, round_number)
            load_to_postgres(data)
            print(f"✅ Round {round_number} completado\n")
        except Exception as e:
            print(f"❌ Error en round {round_number}: {e}\n")
            continue

    print("🏁 Temporada completa cargada")