{{
    config(
        materialized="external",
        location="../datalake/silver/subvention/dotation_soutien_territoire.parquet",
        format="parquet"
    )
}}

SELECT
    exercice::INTEGER AS exercice,
    dispositif,
    programme,
    beneficiaire_type,
    beneficiaire_siren::TEXT AS beneficiaire_siren,
    beneficiaire_dep,
    beneficiaire_nom,
    beneficiaire_code_insee,
    intitule,
    REPLACE(cout_ht, ',', '.')::DOUBLE AS cout_ht,
    REPLACE(subvention, ',', '.')::DOUBLE AS subvention,
    REPLACE(taux, ',', '.')::DOUBLE AS taux,
    release_year
FROM {{ ref("brz_dotation_soutien_territoire") }}
WHERE
    release_year = (
        SELECT MAX(subvention_max.release_year)
        FROM {{ ref("brz_dotation_soutien_territoire") }} AS subvention_max
    )
    AND subvention IS NOT NULL
