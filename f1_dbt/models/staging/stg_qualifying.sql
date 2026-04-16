select *
FROM {{ source('public', 'qualifying') }}
order by position