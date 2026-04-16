select *
FROM {{ source('public', 'laps') }}
WHERE NOT is_deleted