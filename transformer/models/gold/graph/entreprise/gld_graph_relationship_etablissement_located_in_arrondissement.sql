{{
    config(
        materialized="external",
        location="../datalake/gold/graph/relationship/etablissement_located_in_arrondissement.csv",
        format="csv"
    )
}}

SELECT
    e.siret AS ":START_ID(Etablissement)",  -- noqa: RF04,RF05
    c.code_commune AS ":END_ID(Arrondissement)"  -- noqa: RF04,RF05
FROM {{ ref("svr_ent_sirene_etablissement") }} AS e
LEFT JOIN {{ ref("svr_france_communes") }} AS c
    ON e.code_commune_etablissement = c.code_commune
WHERE
    c.type_commune = 'ARM'
    AND e.code_commune_etablissement IS NOT NULL
