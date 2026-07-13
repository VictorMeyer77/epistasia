{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/commune.csv",
        format="csv"
    )
}}

SELECT
    code_commune AS "code_commune:ID(Commune)",  -- noqa: RF04,RF05
    name_commune AS name, -- noqa: RF04,RF05
    code_dep,
    code_reg
FROM {{ ref("svr_france_communes") }}
WHERE type_commune = 'COM'
