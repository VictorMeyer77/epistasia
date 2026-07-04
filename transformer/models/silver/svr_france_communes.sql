{{
    config(
        materialized="external",
        location="../datalake/silver/france_communes.parquet",
        format="parquet"
    )
}}

SELECT
    communes.typecom AS type_commune,
    communes.com AS code_commune,
    communes.reg AS code_reg,
    communes.dep AS code_dep,
    communes.ctcd AS code_collectivite_territorial,
    communes.arr AS arrondissement,
    communes.tncc AS type_name_format,
    communes.ncc AS name_commune_uppercase,
    communes.nccenr AS name_commune_typo_enriched,
    communes.libelle AS name_commune,
    communes.can AS canton_code,
    communes.comparent AS parent_code_commune,
    communes.release_year
FROM
    {{ ref("brz_france_communes") }} AS communes
WHERE
    communes.release_year
    = (
        SELECT MAX(communes_max.release_year)
        FROM {{ ref("brz_france_communes") }} AS communes_max
    )
