{{
    config(
        materialized="external",
        location="../datalake/silver/france_departements.parquet",
        format="parquet"
    )
}}

SELECT
    departements.dep AS code_dep,
    departements.reg AS code_reg,
    departements.cheflieu AS code_commune_prefecture,
    departements.tncc AS type_name_format,
    departements.ncc AS name_dep_uppercase,
    departements.nccenr AS name_dep_typo_enriched,
    departements.libelle AS name_dep,
    departements.release_year
FROM
    {{ ref("brz_france_departements") }} AS departements
WHERE
    departements.release_year
    = (
        SELECT MAX(departements_max.release_year)
        FROM {{ ref("brz_france_departements") }} AS departements_max
    )
