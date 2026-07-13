{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/arrondissement.csv",
        format="csv"
    )
}}

SELECT
    code_commune
        AS "code_arrondissement:ID(Arrondissement)",  -- noqa: RF04,RF05
    name_commune AS name -- noqa: RF04,RF05
FROM {{ ref("svr_france_communes") }}
WHERE type_commune = 'ARM'
