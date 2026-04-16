# 🏎️ F1 Data Pipeline — Dev Notes

Notas técnicas del proyecto. Decisiones de diseño, comandos útiles y aprendizajes.

---

## Setup inicial

**Fecha:** Abril 2026  
**Objetivo:** Pipeline de datos de F1 con Airflow, dbt y dashboard en React.

### Entorno

```bash
cd ~/Data/f1-data-pipeline
source venv/bin/activate
jupyter notebook
```

### Dependencias instaladas

```bash
pip3 install fastf1 pandas jupyter matplotlib
```

**FastF1:** librería Python oficial para datos de F1. Descarga datos de la web oficial de Formula 1.
Documentación: https://docs.fastf1.dev

---

## Arquitectura prevista
FastF1 API
↓
Airflow (orquestación diaria)
↓
Pandas (transformación)
↓
dbt (modelos Silver/Gold)
↓
PostgreSQL (almacenamiento)
↓
FastAPI (API REST)
↓
React (dashboard)

---

## Decisiones técnicas

### ¿Por qué FastF1?
Librería Python específica para F1 con datos oficiales desde 2018.
Alternativas consideradas: OpenF1 API (descartada por menor cobertura histórica).

### ¿Por qué Medallion Architecture?
Mismo patrón que el proyecto Olist. Bronze = datos crudos de FastF1,
Silver = datos limpios con dbt staging, Gold = métricas para el dashboard.

---

## Log de desarrollo

### [Hoy] — Exploración inicial FastF1

**Datos disponibles por sesión:**
- laps → tiempos de vuelta, sectores, compuestos, velocidades
- pick_quicklaps() → filtra vueltas limpias automáticamente
- pick_fastest() → vuelta más rápida de la sesión

**Problema detectado:**
- LapTime viene como timedelta (0 days 00:01:29.708)
- Solución: .dt.total_seconds() para convertir a segundos numéricos
- NaT en vueltas incompletas (pit out, eliminadas) → filtrar con pick_quicklaps()

**Sesión cargada:**
- GP Bahréin 2023 Qualifying
- 254 vueltas totales, 20 pilotos
- VER pole con 1:29.708

### Visualización exploratoria
- matplotlib para exploración en notebooks
- Dashboard final será React con Recharts/Chart.js
- Los datos ya vienen con colores de equipo implícitos (Team column)
- pick_quicklaps() es clave para filtrar datos limpios

## Diseño de la base de datos

### Tablas en PostgreSQL

#### events
Información de cada Gran Premio.
event_id        → identificador único
year            → 2023
round           → número del GP en la temporada
event_name      → Bahrain Grand Prix
circuit         → Bahrain International Circuit
country         → Bahrain
date            → fecha de la carrera

#### qualifying
Resultados de clasificación por GP.
event_id        → referencia a events
driver_abbr     → VER, HAM, LEC...
full_name       → Max Verstappen
team_name       → Red Bull Racing
team_color      → #3671C6
position        → posición final en clasificación
q1_time         → tiempo Q1 en segundos
q2_time         → tiempo Q2 en segundos
q3_time         → tiempo Q3 en segundos
best_time       → mejor tiempo general en segundos

#### race_results
Resultados de carrera por GP.
event_id        → referencia a events
driver_abbr     → VER, HAM, LEC...
full_name       → Max Verstappen
team_name       → Red Bull Racing
team_color      → #3671C6
position        → posición final
grid_position   → posición de salida
time            → tiempo total en segundos
status          → Finished, Retired, +1 Lap...
points          → puntos conseguidos

#### laps
Tiempos de vuelta individuales (qualifying y carrera).
event_id        → referencia a events
session_type    → Q (qualifying) o R (race)
driver_abbr     → VER, HAM...
lap_number      → número de vuelta
lap_time        → tiempo en segundos
sector1_time    → sector 1 en segundos
sector2_time    → sector 2 en segundos
sector3_time    → sector 3 en segundos
is_personal_best → True/False
compound        → SOFT, MEDIUM, HARD
tyre_life       → vueltas con ese juego
fresh_tyre      → True/False
position        → posición en pista
is_deleted      → True/False

### Relaciones
events (1) ──→ (N) qualifying
events (1) ──→ (N) race_results
events (1) ──→ (N) laps

### Decisiones de diseño
- Tiempos siempre en segundos (float) para poder hacer cálculos numéricos
- session_type en laps para distinguir qualifying de carrera en la misma tabla
- team_color incluido en qualifying y race_results para el dashboard React
- is_deleted en laps para poder filtrar vueltas inválidas fácilmente

### Idempotencia del pipeline

El script verifica si un GP ya existe en la tabla `events` antes de cargarlo.
Si existe, lo salta. Esto permite ejecutar el script varias veces sin duplicar datos.

**Clave:** `event_id` con formato `{year}_{round:02d}` (ej: `2023_01`)

### Comandos útiles

```bash
# Ejecutar el pipeline completo
cd ~/Data/f1-data-pipeline
source venv/bin/activate
python src/extract.py

# Verificar datos en PostgreSQL
psql f1_data
SELECT round, event_name FROM events ORDER BY round;
SELECT COUNT(*) FROM laps;
```