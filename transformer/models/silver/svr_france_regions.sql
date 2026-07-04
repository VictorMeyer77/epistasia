{{
    config(
        materialized="external",
        location="../datalake/silver/france_regions.parquet",
        format="parquet"
    )
}}

SELECT
    regions.reg AS code_reg,
    regions.cheflieu AS code_commune_cheflieu,
    regions.tncc AS type_name_format,
    regions.ncc AS name_reg_uppercase,
    regions.nccenr AS name_reg_typo_enriched,
    regions.libelle AS name_reg,
    regions.release_year
FROM
    {{ ref("brz_france_regions") }} AS regions
WHERE
    regions.release_year
    = (
        SELECT MAX(regions_max.release_year)
        FROM {{ ref("brz_france_regions") }} AS regions_max
    )
