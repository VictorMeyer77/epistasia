SELECT
    *,
    filename AS source_file_path,
    CURRENT_TIMESTAMP AS dt_ingested,
    REGEXP_EXTRACT(source_file_path, '_(\d{4})', 1) AS release_year
FROM {{ source("raw", "sirene_etablissement") }}
