{{
    config(
        materialized="external",
        location="../datalake/bronze/france_communes.parquet",
        format="parquet"
    )
}}

SELECT
    *,
    filename AS source_file_path,
    CURRENT_TIMESTAMP AS dt_ingested,
    REGEXP_EXTRACT(source_file_path, '(\d{4})', 1) AS release_year
FROM {{ source("raw", "france_communes") }}
