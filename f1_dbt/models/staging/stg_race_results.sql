select *
FROM {{ source('public', 'race_results') }}
order by position