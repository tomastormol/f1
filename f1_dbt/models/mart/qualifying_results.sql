-- Qualifying results with gap to pole position
SELECT
    e.event_name,
    e.round,
    e.date,
    q.position,
    q.driver_abbr,
    q.full_name,
    q.team_name,
    q.team_color,
    q.best_time,
    ROUND(
        (q.best_time - MIN(q.best_time) OVER (PARTITION BY q.event_id))::numeric
    , 3) AS gap_to_pole
FROM {{ ref('stg_qualifying') }} q
LEFT JOIN {{ ref('stg_events') }} e ON q.event_id = e.event_id
ORDER BY e.round, q.position