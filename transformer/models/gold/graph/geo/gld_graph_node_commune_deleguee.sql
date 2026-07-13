{{
    config(
        materialized="external",
        location="../datalake/gold/graph/node/commune_deleguee.csv",
        format="csv"
    )
}}

SELECT
    code_commune
        AS "code_commune_deleguee:ID(CommuneDeleguee)",  -- noqa: RF04,RF05
    name_commune AS name -- noqa: RF04,RF05
FROM {{ ref("svr_france_communes") }}
WHERE type_commune IN ('COMD', 'COMA')
